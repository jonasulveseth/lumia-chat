"""
Thread API endpoints for conversation management.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
from datetime import datetime

from app.models.chat import Thread, ThreadMessage, CreateThreadRequest, ThreadChatMessage
from app.services.thread_service import ThreadService

router = APIRouter(prefix="/threads", tags=["threads"])

# Global thread service instance
thread_service = ThreadService()


@router.post("/", response_model=Thread)
async def create_thread(request: CreateThreadRequest):
    """Create a new conversation thread."""
    try:
        thread = thread_service.create_thread(request)
        return thread
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create thread: {str(e)}")


@router.get("/user/{user_id}", response_model=list[Thread])
async def get_user_threads(user_id: str):
    """Get all threads for a user."""
    try:
        threads = thread_service.get_user_threads(user_id)
        return threads
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get threads: {str(e)}")


@router.get("/{thread_id}", response_model=Thread)
async def get_thread(thread_id: str):
    """Get a specific thread."""
    try:
        thread = thread_service.get_thread(thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        return thread
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thread: {str(e)}")


@router.get("/{thread_id}/messages", response_model=list[ThreadMessage])
async def get_thread_messages(thread_id: str, limit: int = None):
    """Get messages from a thread."""
    try:
        messages = thread_service.get_thread_messages(thread_id, limit)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.post("/{thread_id}/chat")
async def chat_in_thread(message: ThreadChatMessage):
    """Send a message in a thread and get AI response."""
    try:
        response = await thread_service.chat_in_thread(
            message.thread_id, 
            message.user_id, 
            message.message,
            message.brain_id,
            message.system_prompt
        )
        return {
            "response": response,
            "thread_id": message.thread_id,
            "user_id": message.user_id,
            "brain_id": message.brain_id,
            "system_prompt_used": message.system_prompt,
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@router.post("/{thread_id}/chat/stream")
async def stream_chat_in_thread(message: ThreadChatMessage) -> StreamingResponse:
    """Stream chat response in a thread."""
    
    async def generate_response() -> AsyncGenerator[str, None]:
        import time
        import asyncio
        start_time = time.time()
        
        print(f"🧵 Starting thread chat for thread {message.thread_id}")
        
        # Emit immediate open signal
        try:
            yield f"data: {json.dumps({'debug': 'stream_open', 'thread_id': message.thread_id})}\n\n"
            await asyncio.sleep(0)  # Force immediate flush
        except Exception:
            pass

        try:
            # Verify thread exists and belongs to user
            thread = thread_service.get_thread(message.thread_id)
            if not thread or thread.user_id != message.user_id:
                yield f"data: {json.dumps({'error': 'Thread not found or access denied'})}\n\n"
                await asyncio.sleep(0)  # Force immediate flush
                return
            
            # Use provided brain_id or thread's brain_id
            effective_brain_id = message.brain_id or thread.brain_id
            
            # Use provided system_prompt or thread's system_prompt
            effective_system_prompt = message.system_prompt or thread.system_prompt
            
            # Add user message to thread
            thread_service.add_message(message.thread_id, message.user_id, effective_brain_id, "user", message.message, effective_system_prompt)
            
            # Get thread context
            thread_context = thread_service.get_thread_context(message.thread_id)
            print(f"🧵 Thread context length: {len(thread_context)} chars")
            
            # Get additional context from memory system using the brain_id
            memory_context = await thread_service.memory_service.get_combined_context(effective_brain_id, message.message)
            
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
            print(f"🧵 Final context length: {len(final_context) if final_context else 0} chars")
            
            # Generate AI response
            full_response = ""
            first_chunk_received = False
            
            async for chunk in thread_service.chat_service.ollama_service.generate_response(
                prompt=message.message,
                context=final_context,
                system_prompt=effective_system_prompt,
                stream=True
            ):
                if not first_chunk_received:
                    first_chunk_time = time.time() - start_time
                    print(f"⚡ First chunk from thread chat after: {first_chunk_time:.3f}s")
                    first_chunk_received = True
                
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk, 'thread_id': message.thread_id, 'brain_id': effective_brain_id, 'system_prompt': effective_system_prompt})}\n\n"
                await asyncio.sleep(0)  # Force immediate flush for real-time streaming
            
            # Add AI response to thread
            thread_service.add_message(message.thread_id, message.user_id, effective_brain_id, "assistant", full_response, effective_system_prompt)
            
            # Update memory system in background using the brain_id
            asyncio.create_task(thread_service.memory_service.add_to_short_term_memory(effective_brain_id, message.message, full_response))
            asyncio.create_task(thread_service.memory_service.save_conversation_to_brain_async(effective_brain_id, message.message, full_response))
            # Refresh persona to reflect new conversation
            asyncio.create_task(thread_service.memory_service._refresh_persona_background(effective_brain_id))
            
            total_time = time.time() - start_time
            print(f"🧵 Thread chat completed in {total_time:.3f}s")
            
            # Send end marker
            yield f"data: {json.dumps({'done': True, 'thread_id': message.thread_id, 'brain_id': effective_brain_id, 'system_prompt': effective_system_prompt})}\n\n"
            await asyncio.sleep(0)  # Force immediate flush
            
        except Exception as e:
            print(f"❌ Error in thread chat: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            await asyncio.sleep(0)  # Force immediate flush
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.delete("/{thread_id}")
async def delete_thread(thread_id: str, user_id: str):
    """Delete a thread (only by owner)."""
    try:
        success = thread_service.delete_thread(thread_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Thread not found or access denied")
        return {"message": "Thread deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete thread: {str(e)}")


@router.get("/{thread_id}/context")
async def get_thread_context(thread_id: str):
    """Get the conversation context for a thread (for debugging)."""
    try:
        context = thread_service.get_thread_context(thread_id)
        return {
            "thread_id": thread_id,
            "context": context,
            "context_length": len(context),
            "message_count": len(thread_service.get_thread_messages(thread_id))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")
