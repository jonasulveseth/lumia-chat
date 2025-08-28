"""
Simple memory service with basic prefetch.
"""
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass

from app.services.brain_service import BrainService
from app.services.chat_service import ChatService
from app.core.config import settings
from app.tools.time_query import TimeQueryTool  
from app.tools.summary_query import SummaryQueryTool
from app.utils.date_utils import detect_swedish_date_filter, detect_swedish_date_filters


@dataclass
class MemoryContext:
    """Represents a user's memory context."""
    user_id: str
    context: str = ""
    system_prompt: str = ""
    persona_profile: Optional[str] = None
    persona_last_updated: Optional[datetime] = None
    short_term_memory: List[str] = None  # Recent conversations
    last_conversation_time: Optional[datetime] = None


class MemoryService:
    """Service for managing user memory and context."""
    
    def __init__(self):
        self.brain_service = BrainService()
        self.chat_service = ChatService()
        self.memory_cache: Dict[str, MemoryContext] = {}
        self.update_tasks: Set[str] = set()
        self.time_tool = TimeQueryTool()
        self.summary_tool = SummaryQueryTool()
        # Simple memory service - no prefetch complexity

    async def start_generation(self, user_id: str, draft_message: str) -> None:
        """Disabled - no prefetch."""
        return
    
    # All prefetch methods removed for simplicity

    async def get_combined_context(self, user_id: str, current_message: str = "") -> MemoryContext:
        """Get combined context including memory and real-time data."""
        # Get base memory context
        memory = self.get_user_memory(user_id)
        
        print(f"🔍 DEBUG: Memory context for {user_id}")
        print(f"🔍 DEBUG: Has persona: {bool(memory.persona_profile)}")
        print(f"🔍 DEBUG: Persona length: {len(memory.persona_profile) if memory.persona_profile else 0}")
        print(f"🔍 DEBUG: Short-term memory entries: {len(memory.short_term_memory) if memory.short_term_memory else 0}")
        
        # Check if persona needs refresh (run in background, don't block)
        if not memory.persona_profile or (
            memory.persona_last_updated and 
            (datetime.now() - memory.persona_last_updated).total_seconds() > 600  # 10 min
        ):
            # Trigger background persona refresh without waiting
            import asyncio
            asyncio.create_task(self._refresh_persona_background(user_id))
            print("🔄 Persona refresh triggered in background")
        
        # Get recent conversations for immediate context
        recent_conversations = self.get_recent_conversations(user_id, limit=3)
        
        # Get real-time context from Brain (if needed)
        realtime_context = await self.get_realtime_context(user_id, current_message)
        
        # Build combined context
        context_parts = []
        
        # Add recent conversations first
        if recent_conversations:
            context_parts.append(f"## Senaste konversationer:\n{recent_conversations}")
            print(f"💭 Using recent conversations ({len(recent_conversations)} chars)")
        
        # Add Brain context if available
        if realtime_context:
            context_parts.append(f"## Vector store data:\n{realtime_context}")
            print(f"🔍 DEBUG: Brain context length: {len(realtime_context)}")
        
        # Set the combined context
        if context_parts:
            memory.context = "\n\n".join(context_parts)
            print(f"🔍 DEBUG: Combined context length: {len(memory.context)}")
        else:
            print(f"🔍 DEBUG: No context found")
        
        return memory

    def get_user_memory(self, user_id: str) -> MemoryContext:
        """Get or create memory context for a user."""
        if user_id not in self.memory_cache:
            self.memory_cache[user_id] = MemoryContext(
                user_id=user_id,
                context="",
                system_prompt=settings.system_prompt,
                persona_profile=None,
                persona_last_updated=None,
                short_term_memory=[],
                last_conversation_time=None
            )
            # Trigger initial persona build in background
            import asyncio
            asyncio.create_task(self._refresh_persona_background(user_id))
            print(f"🆕 New user {user_id} - initial persona build triggered")
        return self.memory_cache[user_id]

    async def build_or_refresh_persona(self, user_id: str, force: bool = False) -> Optional[str]:
        """Build a compact persona profile from Brain with recency-weighted diversity."""
        try:
            print("👤 Building persona profile (recency-weighted + diverse)...")
            
            # Fetch a larger pool focused on recent, but not exclusively
            from datetime import datetime, timedelta
            recent_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
            
            brain_response = await self.brain_service.query_quick_context(
                customer_id=user_id,
                question="persona preferences background motivation goals interests tone style likes dislikes activities habits summary recent conversations",
                n_results=20,  # larger pool for diversity
                date_filter=recent_date
            )
            
            if not (brain_response and brain_response.sources):
                return None
            
            # Normalize sources
            sources = [s for s in brain_response.sources if isinstance(s, dict)]
            
            # Prefer chat conversations but don't exclude other high-signal sources
            chat_sources = [s for s in sources if (s.get("metadata", {}).get("content_type") == "chat" or s.get("metadata", {}).get("memory_type") == "conversation")]
            non_chat_sources = [s for s in sources if s not in chat_sources]
            
            def get_ts(src):
                md = src.get("metadata", {})
                return md.get("timestamp", "1970-01-01")
            
            # Sort both groups by recency
            chat_sources.sort(key=get_ts, reverse=True)
            non_chat_sources.sort(key=get_ts, reverse=True)
            
            # Take a recency-weighted sample while keeping diversity across time
            selected: list[dict] = []
            max_total = 8
            max_recent = 5  # stronger weight to recent
            
            # 1) Take top recent chats
            selected.extend(chat_sources[:max_recent])
            
            # 2) Add diverse older chats (stride sampling)
            remaining_chat = chat_sources[max_recent:]
            if remaining_chat:
                stride = max(1, len(remaining_chat) // 2)
                selected.extend(remaining_chat[::stride][:2])
            
            # 3) Add some non-chat diverse items if space remains (e.g., summaries/notes)
            remaining_slots = max_total - len(selected)
            if remaining_slots > 0 and non_chat_sources:
                stride_nc = max(1, len(non_chat_sources) // remaining_slots)
                selected.extend(non_chat_sources[::stride_nc][:remaining_slots])
            
            # Deduplicate by content prefix to avoid repeats
            seen = set()
            content_pieces: list[str] = []
            for src in selected:
                txt = (src.get("content") or src.get("text") or "").strip()
                if not txt:
                    continue
                key = (txt[:80] if len(txt) >= 80 else txt)
                if key in seen:
                    continue
                seen.add(key)
                content_pieces.append(txt[:400])  # concise snippets
            
            if content_pieces:
                return "\n\n".join(content_pieces)
            return None
        except Exception:
            return None

    async def _refresh_persona_background(self, user_id: str):
        """Refresh persona profile in background without blocking main flow."""
        try:
            persona = await self.build_or_refresh_persona(user_id)
            if persona is not None:
                memory = self.get_user_memory(user_id)
                memory.persona_profile = persona
                memory.persona_last_updated = datetime.now()
                print(f"✅ Persona profile updated in background ({len(persona)} chars)")
        except Exception as e:
            print(f"❌ Background persona refresh failed: {e}")

    async def get_realtime_context(self, user_id: str, current_message: str) -> str:
        """Get real-time context for immediate use."""
        try:
            print(f"🔍 DEBUG: Getting real-time context for: '{current_message}'")
            
            # Use LLM to intelligently decide if Brain context is needed
            needs_context = await self.chat_service.ollama_service.needs_brain_context(current_message)
            
            if not needs_context:
                print(f"🤖 LLM decided to skip Brain for: '{current_message}'")
                print(f"🔍 DEBUG: This might be why you're getting short responses!")
                return ""
            else:
                print(f"🎯 LLM decided Brain context needed for: '{current_message}'")
                
            # Always fetch fresh context
            print("🆕 Fetching fresh context (prefetch disabled)")
            
            # If the user's current message contains a clear date, use it
            detected_dates = detect_swedish_date_filters(current_message)
            detected_date = detected_dates if len(detected_dates) > 1 else (detected_dates[0] if detected_dates else None)
            if detected_date:
                print(f"📅 Detected date in message: {detected_date}")

            # Try tools with timeout to prevent long delays
            try:
                import asyncio
                # Time tool with 3s timeout
                t_res = await asyncio.wait_for(
                    self.time_tool.maybe_run(user_id=user_id, message=current_message), 
                    timeout=3.0
                )
                if t_res:
                    result_content = t_res.content if hasattr(t_res, 'content') else str(t_res)
                    print(f"⏰ Time tool result: {len(result_content)} chars")
                    return result_content
            except asyncio.TimeoutError:
                print("⏰ Time tool timeout - skipping")
            except Exception as e:
                print(f"⏰ Time tool error: {e}")

            try:
                # Summary tool with 3s timeout  
                s_res = await asyncio.wait_for(
                    self.summary_tool.maybe_run(user_id=user_id, message=current_message),
                    timeout=3.0
                )
                if s_res:
                    result_content = s_res.content if hasattr(s_res, 'content') else str(s_res)
                    print(f"📋 Summary tool result: {len(result_content)} chars")
                    return result_content
            except asyncio.TimeoutError:
                print("📋 Summary tool timeout - skipping")
            except Exception as e:
                print(f"📋 Summary tool error: {e}")

            # Check for file-related intents to bias towards files
            file_intents = [
                "fil", "filen", "dokument", "pdf", "word", "excel", "xlsx", "docx", "ppt", "presentation",
                "bilaga", "bifogad", "attachment", "rapport", "avtal", "kontrakt", "specifikation"
            ]
            is_file_query = any(word in message_lower for word in file_intents)
            
            print(f"🔍 DEBUG: is_file_query: {is_file_query}")
            
            # Fallback to basic Brain query with dynamic semantic enhancement
            search_terms = current_message
            
            # Dynamic semantic enhancement for better ranking of factual content
            message_lower = current_message.lower()
            
            # Check for "recent" or "last" conversation patterns
            recent_patterns = [
                "vad pratade vi om sist", "vad sa vi sist", "vad diskuterade vi sist",
                "vad pratade vi om senast", "vad sa vi senast", "vad diskuterade vi senast",
                "vad pratade vi om förra", "vad sa vi förra", "vad diskuterade vi förra",
                "senaste konversation", "senaste diskussion", "senaste prat",
                "vad pratade vi om sist", "vad sa vi sist", "vad diskuterade vi sist",
                "fortsätta på den konversationen", "fortsätta därifrån",
                "vad pratade vi om sist", "vad sa vi sist", "vad diskuterade vi sist"
            ]
            
            # More specific patterns for temporal queries
            temporal_patterns = [
                "vad pratade vi om sist", "vad sa vi sist", "vad diskuterade vi sist",
                "vad pratade vi om senast", "vad sa vi senast", "vad diskuterade vi senast",
                "vad pratade vi om förra", "vad sa vi förra", "vad diskuterade vi förra",
                "senaste konversation", "senaste diskussion", "senaste prat",
                "fortsätta på den konversationen", "fortsätta därifrån",
                "vad pratade vi om sist", "vad sa vi sist", "vad diskuterade vi sist"
            ]
            
            is_recent_query = any(pattern in message_lower for pattern in recent_patterns)
            is_temporal_query = any(pattern in message_lower for pattern in temporal_patterns)
            
            print(f"🔍 DEBUG: Message: '{current_message}'")
            print(f"🔍 DEBUG: is_recent_query: {is_recent_query}")
            print(f"🔍 DEBUG: is_temporal_query: {is_temporal_query}")
            
            # For temporal queries, always use recent date filter
            if is_temporal_query:
                is_recent_query = True
                print(f"🕐 Temporal query detected: '{current_message}'")
            
            # Check for "what do you know about X" patterns
            if any(pattern in message_lower for pattern in ["vad vet du om", "berätta om", "vad är", "vad handlar"]):
                # Extract the subject (X) from the question
                import re
                
                # Pattern to extract subject after common question phrases
                patterns = [
                    r"vad vet du om\s+(.+?)[\?\.]*$",
                    r"berätta om\s+(.+?)[\?\.]*$", 
                    r"vad är\s+(.+?)[\?\.]*$",
                    r"vad handlar\s+(.+?)\s+om[\?\.]*$"
                ]
                
                subject = None
                for pattern in patterns:
                    match = re.search(pattern, message_lower)
                    if match:
                        subject = match.group(1).strip()
                        break
                
                if subject:
                    # Add semantic context words that help find factual content about the subject
                    # These words bias the search toward informative content rather than conversational patterns
                    semantic_enhancers = [
                        "projekt", "företag", "verktyg", "tjänst", "produkt", "plattform", "system",
                        "funktionalitet", "användning", "syfte", "beskrivning", "information",
                        "detaljer", "fakta", "egenskaper", "användare", "kunder", "mål"
                    ]
                    
                    # Create enhanced search that should rank factual content higher
                    search_terms = f"{subject} {' '.join(semantic_enhancers[:8])}"
                    print(f"🔍 Enhanced semantic search: '{current_message}' → '{search_terms[:60]}...'")
                
            # Fallback enhancement for general informational questions
            elif any(word in message_lower for word in ["vad", "berätta", "förklara", "hur", "varför"]):
                search_terms = f"{current_message} information fakta detaljer specifikt beskrivning"
                print(f"🔍 General semantic enhancement: '{search_terms[:60]}...'")
            
            # Keep original message for non-informational queries
            else:
                print(f"🔍 Using original search terms: '{search_terms}'")
            
            # For recent queries, prioritize recent dates
            if is_recent_query and not detected_date:
                from datetime import datetime, timedelta
                # Use last 3 days for "recent" queries
                recent_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
                detected_date = recent_date
                print(f"📅 Recent query detected, using date filter: {detected_date}")
            
            # For temporal queries, be even more aggressive with date filtering
            if is_temporal_query:
                from datetime import datetime, timedelta
                # Use last 24 hours for temporal queries to get the most recent
                today_date = datetime.now().strftime("%Y-%m-%d")
                yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                detected_date = [today_date, yesterday_date]  # Use both today and yesterday
                print(f"🕐 Temporal query: using date filter for today and yesterday: {detected_date}")
            
            print(f"🔍 DEBUG: Final detected_date: {detected_date}")
            print(f"🔍 DEBUG: Querying Brain with: '{search_terms}'")
            
            # Build metadata filter if file-focused
            metadata_filter = None
            if is_file_query:
                metadata_filter = {"content_type": "file"}
            
            print(f"🔍 DEBUG: Querying Brain with: '{search_terms}' metadata_filter={metadata_filter}")
            brain_response = await self.brain_service.query_quick_context(
                customer_id=user_id,
                question=search_terms,
                n_results=10,  # Get more results to filter from
                date_filter=detected_date,
                metadata_filter=metadata_filter
            )
            
            if brain_response and brain_response.sources:
                lines = []
                sources = brain_response.sources
                
                # For recent queries, sort by date (most recent first)
                if is_recent_query:
                    try:
                        # Sort sources by timestamp if available
                        def get_timestamp(source):
                            if isinstance(source, dict):
                                metadata = source.get("metadata", {})
                                timestamp = metadata.get("timestamp", "")
                                # Convert ISO timestamp to sortable format
                                if timestamp:
                                    return timestamp
                            return "1970-01-01"  # Default for sorting
                        
                        sources = sorted(sources, key=get_timestamp, reverse=True)
                        print(f"📅 Sorted {len(sources)} sources by date (most recent first)")
                    except Exception as e:
                        print(f"⚠️ Could not sort by date: {e}")
                
                for src in sources:
                    if isinstance(src, dict):
                        txt = src.get("content") or src.get("text") or ""
                        if txt:
                            lines.append(txt)
                            
                            # Limit to avoid too much context  
                            if len(lines) >= 6:
                                break
                
                if lines:
                    print(f"🔍 Found {len(lines)} semantic sources (relying on ChromaDB ranking)")
                    result = "\n\n".join(lines)
                    print(f"🔍 DEBUG: Brain context result length: {len(result)}")
                    return result
                else:
                    print("❌ No sources found")
                    print(f"🔍 DEBUG: No Brain sources found for user {user_id}")
                    # Fallback 1: widen date window if we used a filter
                    try:
                        if detected_date:
                            from datetime import datetime, timedelta
                            wide_dates = [(datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d") for d in range(0, 7)]
                            print(f"🛟 Retrying Brain search with widened date window (7 days): {wide_dates[:3]}...")
                            retry_resp = await self.brain_service.query_quick_context(
                                customer_id=user_id,
                                question=search_terms,
                                n_results=10,
                                date_filter=wide_dates
                            )
                            if retry_resp and retry_resp.sources:
                                lines = []
                                for src in retry_resp.sources:
                                    if isinstance(src, dict):
                                        txt = src.get("content") or src.get("text") or ""
                                        if txt:
                                            lines.append(txt)
                                            if len(lines) >= 6:
                                                break
                                if lines:
                                    result = "\n\n".join(lines)
                                    print(f"✅ Fallback succeeded, context length: {len(result)}")
                                    return result
                    except Exception as _:
                        pass
                    # Fallback 2: return short-term memory if available
                    try:
                        memory_cache_item = self.get_user_memory(user_id)
                        if memory_cache_item and memory_cache_item.context:
                            print("🛟 Using short-term memory as fallback context")
                            return memory_cache_item.context
                    except Exception:
                        pass
                    return ""
            elif brain_response.results:
                result = "\n\n".join(brain_response.results)
                print(f"🔍 DEBUG: Brain results length: {len(result)}")
                return result
            else:
                print("ℹ️  No real-time context found")
                print(f"🔍 DEBUG: No Brain response for user {user_id}")
                # Final fallback: short-term memory
                try:
                    memory_cache_item = self.get_user_memory(user_id)
                    if memory_cache_item and memory_cache_item.context:
                        print("🛟 Final fallback to short-term memory")
                        return memory_cache_item.context
                except Exception:
                    pass
                return ""
                
        except Exception as e:
            print(f"❌ Error getting real-time context: {e}")
            return None

    async def get_realtime_context_debug(self, user_id: str, current_message: str) -> Dict[str, Any]:
        """Diagnose why real-time context might be empty by exposing internal decisions."""
        try:
            from copy import deepcopy
            debug: Dict[str, Any] = {
                "message": current_message,
                "needs_context": None,
                "detected_date": None,
                "is_recent_query": None,
                "is_temporal_query": None,
                "search_terms": None,
                "brain_sources_count": 0,
                "brain_sources_sample": [],
            }
            needs_context = await self.chat_service.ollama_service.needs_brain_context(current_message)
            debug["needs_context"] = needs_context
            if not needs_context:
                return debug
            # Date detection
            detected_dates = detect_swedish_date_filters(current_message)
            detected_date = detected_dates if len(detected_dates) > 1 else (detected_dates[0] if detected_dates else None)
            debug["detected_date"] = deepcopy(detected_date)
            search_terms = current_message
            message_lower = current_message.lower()
            recent_patterns = [
                "vad pratade vi om sist", "vad sa vi sist", "vad diskuterade vi sist",
                "vad pratade vi om senast", "vad sa vi senast", "vad diskuterade vi senast",
                "vad pratade vi om förra", "vad sa vi förra", "vad diskuterade vi förra",
                "senaste konversation", "senaste diskussion", "senaste prat",
                "fortsätta på den konversationen", "fortsätta därifrån"
            ]
            temporal_patterns = recent_patterns
            is_recent_query = any(pattern in message_lower for pattern in recent_patterns)
            is_temporal_query = any(pattern in message_lower for pattern in temporal_patterns)
            if is_temporal_query and not is_recent_query:
                is_recent_query = True
            debug["is_recent_query"] = is_recent_query
            debug["is_temporal_query"] = is_temporal_query
            # Enhance informational queries a bit
            if any(pattern in message_lower for pattern in ["vad vet du om", "berätta om", "vad är", "vad handlar"]):
                import re
                patterns = [
                    r"vad vet du om\s+(.+?)[\?\.]*$",
                    r"berätta om\s+(.+?)[\?\.]*$",
                    r"vad är\s+(.+?)[\?\.]*$",
                    r"vad handlar\s+(.+?)\s+om[\?\.]*$"
                ]
                subject = None
                for p in patterns:
                    m = re.search(p, message_lower)
                    if m:
                        subject = m.group(1).strip()
                        break
                if subject:
                    search_terms = f"{subject} projekt företag verktyg tjänst produkt plattform system"
            elif any(w in message_lower for w in ["vad", "berätta", "förklara", "hur", "varför"]):
                search_terms = f"{current_message} information fakta detaljer specifikt beskrivning"
            debug["search_terms"] = search_terms
            # Date adjustments
            if is_recent_query and not detected_date:
                recent_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
                detected_date = recent_date
            if is_temporal_query:
                today_date = datetime.now().strftime("%Y-%m-%d")
                yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                detected_date = [today_date, yesterday_date]
            debug["detected_date"] = deepcopy(detected_date)
            brain_response = await self.brain_service.query_quick_context(
                customer_id=user_id,
                question=search_terms,
                n_results=10,
                date_filter=detected_date
            )
            if brain_response and brain_response.sources:
                sources = brain_response.sources
                # Sort if temporal to prefer latest
                if is_recent_query:
                    try:
                        def ts(src):
                            md = src.get("metadata", {}) if isinstance(src, dict) else {}
                            return md.get("timestamp", "1970-01-01")
                        sources = sorted(sources, key=ts, reverse=True)
                    except Exception:
                        pass
                debug["brain_sources_count"] = len(sources)
                for src in sources[:3]:
                    if isinstance(src, dict):
                        md = src.get("metadata", {})
                        preview = (src.get("content") or src.get("text") or "")[:140]
                        debug["brain_sources_sample"].append({
                            "date": md.get("date"),
                            "timestamp": md.get("timestamp"),
                            "preview": preview
                        })
            return debug
        except Exception as e:
            return {"error": str(e), "message": current_message}

    async def save_conversation_to_brain_async(self, user_id: str, user_message: str, ai_response: str) -> None:
        """Save conversation to Brain in background."""
        try:
            # Prevent duplicate saves
            if user_id in self.update_tasks:
                return
            
            self.update_tasks.add(user_id)
            
            current_time = datetime.now()
            conversation_text = f"Användare: {user_message}\nAssistent: {ai_response}"
            
            metadata = {
                "source": "chat",
                "content_type": "chat",
                "user_id": user_id,
                "timestamp": current_time.isoformat(),
                "date": current_time.strftime("%Y-%m-%d"),
                "time": current_time.strftime("%H:%M:%S"),
                "day_of_week": current_time.strftime("%A"),
                "month": current_time.strftime("%B"),
                "memory_type": "conversation"
            }
            
            success = await self.brain_service.ingest_content(
                customer_id=user_id,
                content=conversation_text,
                metadata=metadata
            )
            
            if success:
                print(f"💾 Conversation saved to Brain for user {user_id}")
            else:
                print(f"❌ Failed to save conversation to Brain for user {user_id}")
                
        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
        finally:
            if user_id in self.update_tasks:
                self.update_tasks.remove(user_id)

    async def add_to_short_term_memory(self, user_id: str, user_message: str, ai_response: str) -> None:
        """Add conversation to short-term memory (simplified implementation)."""
        try:
            memory = self.get_user_memory(user_id)
            
            # Initialize short-term memory if None or empty
            if memory.short_term_memory is None:
                memory.short_term_memory = []
            
            # Create conversation entry
            conversation_entry = f"Användare: {user_message}\nAssistent: {ai_response}"
            
            # Add to short-term memory (keep last 5 conversations)
            memory.short_term_memory.append(conversation_entry)
            if len(memory.short_term_memory) > 5:
                memory.short_term_memory = memory.short_term_memory[-5:]  # Keep only last 5
            
            memory.last_conversation_time = datetime.now()
            print(f"💭 Short-term memory updated for {user_id} ({len(memory.short_term_memory)} entries)")
        except Exception as e:
            print(f"❌ Error updating short-term memory: {e}")
    
    async def update_long_term_memory_async(self, user_id: str) -> None:
        """Update long-term memory (simplified - delegates to Brain)."""
        try:
            # The real long-term memory is handled by Brain storage
            print(f"🧠 Long-term memory update triggered for {user_id}")
        except Exception as e:
            print(f"❌ Error updating long-term memory: {e}")

    def get_memory_stats(self, user_id: str) -> dict:
        """Get memory statistics for a user."""
        if user_id in self.memory_cache:
            memory = self.memory_cache[user_id]
            return {
                "user_id": user_id,
                "has_context": bool(memory.context),
                "context_length": len(memory.context) if memory.context else 0,
                "has_persona": bool(memory.persona_profile),
                "persona_last_updated": memory.persona_last_updated.isoformat() if memory.persona_last_updated else None
            }
        return {"user_id": user_id, "cached": False}

    def get_recent_conversations(self, user_id: str, limit: int = 3) -> str:
        """Get recent conversations for context."""
        try:
            memory = self.get_user_memory(user_id)
            if not memory.short_term_memory or len(memory.short_term_memory) == 0:
                return ""
            
            # Get the most recent conversations
            recent_conversations = memory.short_term_memory[-limit:]
            return "\n\n".join(recent_conversations)
        except Exception as e:
            print(f"❌ Error getting recent conversations: {e}")
            return ""
