"""
Thread service for managing conversation threads.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from app.models.chat import Thread, ThreadMessage, CreateThreadRequest
from app.services.memory_service import MemoryService
from app.services.chat_service import ChatService


class ThreadService:
    """Service for managing conversation threads."""
    
    def __init__(self):
        self.memory_service = MemoryService()
        self.chat_service = ChatService()
        self.threads: Dict[str, Thread] = {}
        self.messages: Dict[str, List[ThreadMessage]] = {}
        self.max_messages_per_thread = 50  # Prevent token overflow
        self.max_context_messages = 20  # How many recent messages to include in context
    
    def create_thread(self, request: CreateThreadRequest) -> Thread:
        """Create a new conversation thread."""
        thread_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Generate title if not provided
        title = request.title or f"Konversation {now.strftime('%Y-%m-%d %H:%M')}"
        
        thread = Thread(
            thread_id=thread_id,
            user_id=request.user_id,
            brain_id=request.brain_id,
            system_prompt=request.system_prompt,
            title=title,
            created_at=now,
            updated_at=now,
            message_count=0
        )
        
        self.threads[thread_id] = thread
        self.messages[thread_id] = []
        
        # Add initial message if provided
        if request.initial_message:
            self.add_message(thread_id, request.user_id, request.brain_id, "user", request.initial_message, request.system_prompt)
        
        print(f"🧵 Created thread {thread_id} for user {request.user_id} with brain {request.brain_id}")
        if request.system_prompt:
            print(f"🎭 System prompt: {request.system_prompt[:50]}...")
        return thread
    
    def add_message(self, thread_id: str, user_id: str, brain_id: str, role: str, content: str, system_prompt: Optional[str] = None) -> ThreadMessage:
        """Add a message to a thread."""
        if thread_id not in self.threads:
            raise ValueError(f"Thread {thread_id} not found")
        
        message_id = str(uuid.uuid4())
        now = datetime.now()
        
        message = ThreadMessage(
            message_id=message_id,
            thread_id=thread_id,
            user_id=user_id,
            brain_id=brain_id,
            role=role,
            content=content,
            system_prompt=system_prompt,
            timestamp=now
        )
        
        # Add to messages list
        self.messages[thread_id].append(message)
        
        # Update thread metadata
        thread = self.threads[thread_id]
        thread.message_count += 1
        thread.updated_at = now
        thread.last_message = content[:100] + "..." if len(content) > 100 else content
        
        # Limit messages to prevent overflow
        if len(self.messages[thread_id]) > self.max_messages_per_thread:
            # Remove oldest messages, keep the most recent
            self.messages[thread_id] = self.messages[thread_id][-self.max_messages_per_thread:]
            print(f"🧵 Thread {thread_id} reached message limit, removed oldest messages")
        
        print(f"💬 Added {role} message to thread {thread_id} with brain {brain_id}")
        if system_prompt:
            print(f"🎭 Message used system prompt: {system_prompt[:30]}...")
        return message
    
    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        return self.threads.get(thread_id)
    
    def get_user_threads(self, user_id: str) -> List[Thread]:
        """Get all threads for a user."""
        return [thread for thread in self.threads.values() if thread.user_id == user_id]
    
    def get_thread_messages(self, thread_id: str, limit: Optional[int] = None) -> List[ThreadMessage]:
        """Get messages from a thread."""
        if thread_id not in self.messages:
            return []
        
        messages = self.messages[thread_id]
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_thread_context(self, thread_id: str) -> str:
        """Get conversation context for a thread (recent messages)."""
        if thread_id not in self.messages:
            return ""
        
        messages = self.messages[thread_id]
        if not messages:
            return ""
        
        # Get recent messages for context
        recent_messages = messages[-self.max_context_messages:]
        
        context_lines = []
        for msg in recent_messages:
            role_display = "Användare" if msg.role == "user" else "Assistent"
            context_lines.append(f"{role_display}: {msg.content}")
        
        return "\n\n".join(context_lines)
    
    async def chat_in_thread(self, thread_id: str, user_id: str, message: str, brain_id: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Send a message in a thread and get AI response."""
        # Verify thread exists and belongs to user
        thread = self.get_thread(thread_id)
        if not thread or thread.user_id != user_id:
            raise ValueError(f"Thread {thread_id} not found or access denied")
        
        # Use provided brain_id or thread's brain_id
        effective_brain_id = brain_id or thread.brain_id
        
        # Use provided system_prompt or thread's system_prompt
        effective_system_prompt = system_prompt or thread.system_prompt
        
        # Add user message to thread
        self.add_message(thread_id, user_id, effective_brain_id, "user", message, effective_system_prompt)
        
        # Get thread context
        thread_context = self.get_thread_context(thread_id)
        
        # Get additional context from memory system using the brain_id
        memory_context = await self.memory_service.get_combined_context(effective_brain_id, message)
        
        # Combine contexts
        final_context_parts = []
        
        # Always include thread context first
        if thread_context:
            final_context_parts.append(f"## Konversationshistorik:\n{thread_context}")
        
        # Add persona profile if available
        if memory_context.persona_profile:
            final_context_parts.append(f"## Om användaren:\n{memory_context.persona_profile}")
        
        # Add Brain context if available (but not recent conversations since we have thread context)
        if memory_context.context and "Vector store data:" in memory_context.context:
            # Extract only the Brain part, not recent conversations
            brain_part = memory_context.context.split("## Vector store data:")
            if len(brain_part) > 1:
                final_context_parts.append(f"## Vector store data:{brain_part[1]}")
        
        final_context = "\n\n".join(final_context_parts) if final_context_parts else None
        
        # Generate AI response with system prompt
        full_response = ""
        async for chunk in self.chat_service.ollama_service.generate_response(
            prompt=message,
            context=final_context,
            system_prompt=effective_system_prompt,
            stream=True
        ):
            full_response += chunk
        
        # Add AI response to thread
        self.add_message(thread_id, user_id, effective_brain_id, "assistant", full_response, effective_system_prompt)
        
        # Update memory system in background using the brain_id
        import asyncio
        asyncio.create_task(self.memory_service.add_to_short_term_memory(effective_brain_id, message, full_response))
        asyncio.create_task(self.memory_service.save_conversation_to_brain_async(effective_brain_id, message, full_response))
        
        return full_response
    
    def delete_thread(self, thread_id: str, user_id: str) -> bool:
        """Delete a thread (only by owner)."""
        thread = self.get_thread(thread_id)
        if not thread or thread.user_id != user_id:
            return False
        
        del self.threads[thread_id]
        if thread_id in self.messages:
            del self.messages[thread_id]
        
        print(f"🗑️ Deleted thread {thread_id}")
        return True
