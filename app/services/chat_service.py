"""
Chat service that orchestrates LLM and Brain interactions.
"""
import time
from typing import AsyncGenerator, Optional
from app.services.ollama_service import OllamaService
from app.services.brain_service import BrainService
from app.models.chat import ChatMessage, ChatResponse
from app.core.config import settings
from app.utils.date_utils import detect_swedish_date_filter, detect_swedish_date_filters


class ChatService:
    """Service for handling chat interactions with LLM and Brain."""
    
    def __init__(self):
        self.ollama_service = OllamaService()
        self.brain_service = BrainService()
    
    async def process_message(
        self, 
        message: ChatMessage,
        use_context: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Process a chat message with optional context from Brain.
        
        Args:
            message: Chat message from user
            use_context: Whether to use Brain context
            
        Yields:
            Response chunks as strings
        """
        start_time = time.time()
        context = None
        
        # Query Brain for context if enabled
        if use_context and settings.use_rag:
            try:
                brain_start = time.time()
                print(f"🔍 Querying Brain for context...")
                
                # Detect date filter from user's message (e.g., "igår", "idag")
                # Try to capture one or several dates (e.g., "idag och igår")
                detected_dates = detect_swedish_date_filters(message.message)
                detected_date = detected_dates if len(detected_dates) > 1 else (detected_dates[0] if detected_dates else None)
                if detected_date:
                    print(f"📅 Detected date in message: {detected_date}")

                brain_response = await self.brain_service.query_context(
                    customer_id=message.user_id,
                    question=message.message,
                    n_results=3,
                    date_filter=detected_date
                )
                
                brain_time = time.time() - brain_start
                print(f"⏱️  Brain query took: {brain_time:.2f}s")
                
                if brain_response and brain_response.results:
                    # Combine context from Brain results
                    context = "\n".join(brain_response.results)
                    print(f"📚 Found {len(brain_response.results)} context results")
                else:
                    print("📚 No context found from Brain")
                    
            except Exception as e:
                print(f"❌ Error getting context from Brain: {e}")
        elif not settings.use_rag:
            print("🚫 RAG disabled - skipping Brain query")
        
        # Generate response from Ollama with optional context
        ollama_start = time.time()
        print(f"🤖 Starting Ollama response generation...")
        
        async for chunk in self.ollama_service.generate_response(
            prompt=message.message,
            context=context,
            stream=True
        ):
            yield chunk
        
        ollama_time = time.time() - ollama_start
        total_time = time.time() - start_time
        
        print(f"⏱️  Ollama generation took: {ollama_time:.2f}s")
        print(f"⏱️  Total response time: {total_time:.2f}s")
        
        # Save conversation asynchronously (don't wait for it)
        try:
            # We'll collect the full response for saving
            # This is a simplified approach - in production you'd want to collect the stream
            pass
        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
    
    async def save_conversation(
        self, 
        user_id: str, 
        message: str, 
        response: str,
        context_used: Optional[str] = None
    ) -> bool:
        """
        Save conversation to Brain for future context.
        
        Args:
            user_id: User identifier
            message: User's message
            response: AI response
            context_used: Context that was used
            
        Returns:
            True if successful, False otherwise
        """
        from datetime import datetime
        
        # Prepare content for ingestion
        content = f"User: {message}\nAI: {response}"
        
        # Get current timestamp
        current_time = datetime.now()
        
        metadata = {
            "source": "chat",
            "user_id": user_id,
            "context_used": context_used,
            "timestamp": current_time.isoformat(),
            "date": current_time.strftime("%Y-%m-%d"),
            "time": current_time.strftime("%H:%M:%S"),
            "day_of_week": current_time.strftime("%A"),
            "month": current_time.strftime("%B")
        }
        
        try:
            success = await self.brain_service.ingest_content(
                customer_id=user_id,
                content=content,
                metadata=metadata
            )
            return success
            
        except Exception as e:
            print(f"Error saving conversation: {e}")
            return False
    
    async def get_chat_history(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> Optional[list]:
        """
        Get chat history for a user.
        
        Args:
            user_id: User identifier
            limit: Number of recent conversations to retrieve
            
        Returns:
            List of chat history items or None if error
        """
        try:
            collection_info = await self.brain_service.get_collection_info(user_id)
            if collection_info:
                # This would need to be implemented in Brain API
                # For now, return basic info
                return {
                    "user_id": user_id,
                    "collection_info": collection_info
                }
            return None
            
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return None
    
    async def health_check(self) -> dict:
        """
        Check health of all services.
        
        Returns:
            Health status dictionary
        """
        ollama_healthy = True  # Assume healthy for now
        brain_healthy = await self.brain_service.health_check()
        
        return {
            "ollama": ollama_healthy,
            "brain": brain_healthy,
            "overall": ollama_healthy and brain_healthy
        } 