"""
Memory-based chat API endpoints for Lumia.
"""
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
from datetime import datetime

from app.models.chat import ChatMessage
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])

# Global memory service instance
memory_service = MemoryService()


@router.post("/chat")
async def chat_with_memory_simple(message: ChatMessage):
    """
    Simple chat response with memory context (non-streaming).
    
    Returns a complete JSON response for easier integration with external apps.
    """
    import time
    start_time = time.time()
    
    print(f"🕐 Starting simple memory chat request...")
    
    # Use brain_id if provided, otherwise use user_id
    effective_brain_id = message.brain_id or message.user_id
    
    # Get combined memory context (same logic as streaming endpoint)
    memory_start = time.time()
    combined_memory = await memory_service.get_combined_context(effective_brain_id, message.message)
    memory_time = time.time() - memory_start
    print(f"⏱️  Memory context retrieval took: {memory_time:.3f}s")
    
    realtime_context = combined_memory.context
    print(f"⚡ Real-time context: {realtime_context}")
    
    # Combine memory context with real-time context
    context_start = time.time()
    final_context = None
    context_parts = []
    persona_profile = combined_memory.persona_profile
    
    # Always include persona profile if available
    if persona_profile:
        context_parts.append(f"## Om användaren:\n{persona_profile}")
        print(f"👤 Including persona profile ({len(persona_profile)} chars)")
    
    # Include the combined context (recent conversations + Brain data)
    if realtime_context:
        context_parts.append(realtime_context)
        print(f"📝 Including combined context ({len(realtime_context)} chars)")
    
    if context_parts:
        final_context = "\n\n".join(context_parts)
        print(f"📝 Final context length: {len(final_context)} characters")
    else:
        print(f"ℹ️  No context found for user {message.user_id}")
    
    context_time = time.time() - context_start
    print(f"⏱️  Context preparation took: {context_time:.3f}s")
    
    # Generate full response (non-streaming)
    print(f"🚀 Starting Ollama generation...")
    ollama_start = time.time()
    full_response = ""
    first_chunk_received = False
    
    async for chunk in memory_service.chat_service.ollama_service.generate_response(
        prompt=message.message,
        context=final_context,
        system_prompt=message.system_prompt,
        stream=True
    ):
        if not first_chunk_received:
            first_chunk_time = time.time() - ollama_start
            print(f"⚡ First chunk from Ollama after: {first_chunk_time:.3f}s")
            first_chunk_received = True
        
        full_response += chunk
    
    generation_time = time.time() - ollama_start
    print(f"⏱️  Full generation took: {generation_time:.3f}s")
    
    # Start background tasks for memory updates (non-blocking)
    asyncio.create_task(memory_service.add_to_short_term_memory(effective_brain_id, message.message, full_response))
    asyncio.create_task(memory_service.update_long_term_memory_async(effective_brain_id))
    asyncio.create_task(memory_service.save_conversation_to_brain_async(effective_brain_id, message.message, full_response))
    
    total_time = time.time() - start_time
    print(f"⏱️  Total request time: {total_time:.3f}s")
    
    return {
        "response": full_response,
        "user_id": message.user_id,
        "brain_id": effective_brain_id,
        "system_prompt_used": message.system_prompt,
        "context_used": bool(final_context),
        "context_length": len(final_context) if final_context else 0,
        "response_length": len(full_response),
        "persona_included": bool(persona_profile),
        "processing_time_ms": round(total_time * 1000, 2)
    }


@router.post("/chat/stream")
async def stream_memory_chat(message: ChatMessage) -> StreamingResponse:
    """
    Stream chat response using memory system.
    
    This endpoint uses cached memory for immediate responses,
    while updating memory in the background.
    """
    
    async def generate_response() -> AsyncGenerator[str, None]:
        import time
        import asyncio
        start_time = time.time()
        
        print(f"🕐 Starting request processing...")
        
        # Emit immediate open signal so the client knows stream started
        try:
            yield f"data: {json.dumps({'debug': 'stream_open'})}\n\n"
            await asyncio.sleep(0)  # Force immediate flush
        except Exception:
            pass

        # Get combined memory context (optimized for speed)
        memory_start = time.time()
        
        # Use brain_id if provided, otherwise use user_id
        effective_brain_id = message.brain_id or message.user_id
        
        combined_memory = await memory_service.get_combined_context(effective_brain_id, message.message)
        memory_time = time.time() - memory_start
        print(f"⏱️  Memory context retrieval took: {memory_time:.3f}s")
        
        realtime_context = combined_memory.context
        realtime_time = memory_time  # Already included above
        print(f"⚡ Real-time context: {realtime_context}")
        
        # Combine memory context with real-time context
        context_start = time.time()
        final_context = None
        context_parts = []
        persona_profile = combined_memory.persona_profile
        
        # Always include persona profile if available (critical when Brain is skipped)
        if persona_profile:
            context_parts.append(f"## Om användaren:\n{persona_profile}")
            print(f"👤 Including persona profile ({len(persona_profile)} chars)")
        
        # Include the combined context (recent conversations + Brain data)
        if realtime_context:
            context_parts.append(realtime_context)
            print(f"📝 Including combined context ({len(realtime_context)} chars)")
        
        if context_parts:
            final_context = "\n\n".join(context_parts)
            print(f"📝 Final context length: {len(final_context)} characters")
        else:
            print(f"ℹ️  No context found for user {message.user_id}")
        
        context_time = time.time() - context_start
        print(f"⏱️  Context preparation took: {context_time:.3f}s")
        
        # Stream response directly from Ollama (optimized)
        print(f"🚀 Starting Ollama generation...")
        ollama_start = time.time()
        # Simple direct streaming - no cache complexity
        full_response = ""
        first_chunk_received = False
        
        # Generate response directly
        async for chunk in memory_service.chat_service.ollama_service.generate_response(
            prompt=message.message,
            context=final_context,
            system_prompt=message.system_prompt,
            stream=True
        ):
            if not first_chunk_received:
                first_chunk_time = time.time() - ollama_start
                print(f"⚡ First chunk from Ollama after: {first_chunk_time:.3f}s")
                first_chunk_received = True
            
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk, 'brain_id': effective_brain_id, 'system_prompt': message.system_prompt})}\n\n"
            await asyncio.sleep(0)  # Force immediate flush for real-time streaming
        
        # Start background tasks for memory updates (non-blocking)
        asyncio.create_task(memory_service.add_to_short_term_memory(effective_brain_id, message.message, full_response))
        asyncio.create_task(memory_service.update_long_term_memory_async(effective_brain_id))
        asyncio.create_task(memory_service.save_conversation_to_brain_async(effective_brain_id, message.message, full_response))
        
        # Send end marker
        yield f"data: {json.dumps({'done': True, 'brain_id': effective_brain_id, 'system_prompt': message.system_prompt})}\n\n"
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


@router.post("/start_generation")
async def start_generation(message: ChatMessage):
    """Start background generation while user types (no caching)."""
    await memory_service.start_generation(message.user_id, message.message)
    return {"status": "started"}


@router.get("/stats/{user_id}")
async def get_memory_stats(user_id: str):
    """
    Get memory statistics for a user.
    """
    stats = memory_service.get_memory_stats(user_id)
    return {
        "user_id": user_id,
        "memory_stats": stats,
        "short_term_memory": memory_service.get_user_memory(user_id).short_term,
        "long_term_memory": memory_service.get_user_memory(user_id).long_term
    }


@router.post("/chat/fast")
async def fast_chat(message: ChatMessage) -> StreamingResponse:
    """
    Fast chat response without memory context for immediate response.
    """
    
    async def generate_response() -> AsyncGenerator[str, None]:
        import time
        import asyncio
        start_time = time.time()
        
        # Direct Ollama response without context
        print(f"🚀 Starting fast Ollama generation...")
        ollama_start = time.time()
        full_response = ""
        first_chunk_received = False
        
        async for chunk in memory_service.chat_service.ollama_service.generate_response(
            prompt=message.message,
            context=None,  # No context for speed
            stream=True
        ):
            if not first_chunk_received:
                first_chunk_time = time.time() - ollama_start
                print(f"⚡ First chunk from fast Ollama after: {first_chunk_time:.3f}s")
                first_chunk_received = True
            
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0)  # Force immediate flush for real-time streaming
        
        # Save to memory in background
        asyncio.create_task(memory_service.add_to_short_term_memory(message.user_id, message.message, full_response))
        
        # Send end marker
        yield f"data: {json.dumps({'done': True})}\n\n"
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


@router.post("/clear/{user_id}")
async def clear_user_memory(user_id: str):
    """
    Clear memory for a specific user.
    """
    if user_id in memory_service.memory_cache:
        del memory_service.memory_cache[user_id]
    
    return {"message": f"Memory cleared for user {user_id}"}


@router.get("/health")
async def memory_health_check():
    """
    Health check for memory service.
    """
    return {
        "status": "healthy",
        "service": "Memory",
        "memory_cache_size": len(memory_service.memory_cache)
    }


@router.get("/persona/{user_id}")
async def get_user_persona(user_id: str):
    """
    Get the current persona profile for a user (for testing).
    """
    try:
        memory = memory_service.get_user_memory(user_id)
        
        return {
            "user_id": user_id,
            "has_persona": bool(memory.persona_profile),
            "persona_profile": memory.persona_profile,
            "persona_length": len(memory.persona_profile) if memory.persona_profile else 0,
            "persona_last_updated": memory.persona_last_updated.isoformat() if memory.persona_last_updated else None,
            "time_since_update": None if not memory.persona_last_updated else 
                round((datetime.now() - memory.persona_last_updated).total_seconds(), 1)
        }
    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_id
        }


@router.post("/persona/{user_id}/refresh")
async def refresh_user_persona(user_id: str):
    """
    Force refresh the persona profile for a user (for testing).
    """
    try:
        print(f"🔄 Force refreshing persona for {user_id}...")
        persona = await memory_service.build_or_refresh_persona(user_id, force=True)
        
        if persona:
            memory = memory_service.get_user_memory(user_id)
            memory.persona_profile = persona
            memory.persona_last_updated = datetime.now()
            
            return {
                "user_id": user_id,
                "success": True,
                "persona_profile": persona,
                "persona_length": len(persona),
                "message": "Persona refreshed successfully"
            }
        else:
            return {
                "user_id": user_id,
                "success": False,
                "message": "No persona data found in Brain for this user"
            }
    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_id,
            "success": False
        }


@router.get("/debug/{user_id}")
async def debug_memory_context(user_id: str, message: str = "test"):
    """
    Debug endpoint to check memory context and Brain integration.
    """
    try:
        # Get memory context
        memory = memory_service.get_user_memory(user_id)
        
        # Check Brain context decision
        needs_context = await memory_service.chat_service.ollama_service.needs_brain_context(message)
        
        # Get real-time context
        realtime_context = await memory_service.get_realtime_context(user_id, message)
        
        # Get combined context
        combined_memory = await memory_service.get_combined_context(user_id, message)
        
        return {
            "user_id": user_id,
            "test_message": message,
            "memory_info": {
                "has_persona": bool(memory.persona_profile),
                "persona_length": len(memory.persona_profile) if memory.persona_profile else 0,
                "persona_preview": memory.persona_profile[:200] + "..." if memory.persona_profile else None,
                "persona_last_updated": memory.persona_last_updated.isoformat() if memory.persona_last_updated else None
            },
            "brain_decision": {
                "needs_context": needs_context,
                "decision_reason": "LLM decided whether to use Brain context"
            },
            "realtime_context": {
                "found": bool(realtime_context),
                "length": len(realtime_context) if realtime_context else 0,
                "preview": realtime_context[:200] + "..." if realtime_context else None
            },
            "combined_context": {
                "has_context": bool(combined_memory.context),
                "context_length": len(combined_memory.context) if combined_memory.context else 0,
                "has_persona": bool(combined_memory.persona_profile),
                "persona_length": len(combined_memory.persona_profile) if combined_memory.persona_profile else 0
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "user_id": user_id,
            "test_message": message
        }


@router.get("/debug2/{user_id}")
async def debug_memory_context_v2(user_id: str, message: str = "test"):
	"""Extended debug endpoint showing internal realtime-context diagnostics."""
	try:
		memory = memory_service.get_user_memory(user_id)
		needs_context = await memory_service.chat_service.ollama_service.needs_brain_context(message)
		diag = await memory_service.get_realtime_context_debug(user_id, message)
		return {
			"user_id": user_id,
			"test_message": message,
			"has_persona": bool(memory.persona_profile),
			"needs_context": needs_context,
			"diagnostics": diag,
		}
	except Exception as e:
		return {"error": str(e), "user_id": user_id, "test_message": message}


@router.post("/test/stream")
async def test_stream() -> StreamingResponse:
    """
    Simple test endpoint to check if streaming works.
    """
    
    async def generate_test_response() -> AsyncGenerator[str, None]:
        import time
        import asyncio
        start_time = time.time()
        
        # Send immediate response
        yield f"data: {json.dumps({'chunk': 'Test started at ' + str(start_time)})}\n\n"
        await asyncio.sleep(0)  # Force immediate flush
        
        # Send a few more chunks quickly
        for i in range(5):
            await asyncio.sleep(0.1)  # Small delay
            yield f"data: {json.dumps({'chunk': f'Chunk {i+1} at {time.time() - start_time:.2f}s'})}\n\n"
            await asyncio.sleep(0)  # Force immediate flush
        
        yield f"data: {json.dumps({'done': True})}\n\n"
        await asyncio.sleep(0)  # Force immediate flush
    
    return StreamingResponse(
        generate_test_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    ) 