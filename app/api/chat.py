"""
Chat API endpoints for Lumia.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json

from app.models.chat import ChatMessage, ChatResponse
from app.services.chat_service import ChatService
from app.utils.date_utils import detect_swedish_date_filter, detect_swedish_date_filters

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def stream_chat(message: ChatMessage, use_context: bool = True) -> StreamingResponse:
    """
    Stream chat response from LLM with optional Brain context.
    
    Args:
        message: Chat message from user
        use_context: Whether to use Brain context (default: True)
        
    Returns:
        Streaming response with AI reply
    """
    chat_service = ChatService()
    
    async def generate_response() -> AsyncGenerator[str, None]:
        import asyncio
        full_response = ""
        
        async for chunk in chat_service.process_message(message, use_context=use_context):
            full_response += chunk
            # Send chunk immediately as Server-Sent Event
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0)  # Force immediate flush for real-time streaming
        
        # Save conversation to Brain asynchronously (don't wait)
        try:
            await chat_service.save_conversation(
                user_id=message.user_id,
                message=message.message,
                response=full_response
            )
        except Exception as e:
            print(f"Error saving conversation: {e}")
        
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


@router.post("/")
async def chat(message: ChatMessage) -> ChatResponse:
    """
    Get chat response from LLM with optional Brain context.
    
    Args:
        message: Chat message from user
        
    Returns:
        Complete AI response
    """
    chat_service = ChatService()
    
    full_response = ""
    context_used = None
    
    # Get context from Brain
    try:
        detected_dates = detect_swedish_date_filters(message.message)
        detected_date = detected_dates if len(detected_dates) > 1 else (detected_dates[0] if detected_dates else None)
        if detected_date:
            print(f"📅 Detected date in message: {detected_date}")
        brain_response = await chat_service.brain_service.query_context(
            customer_id=message.user_id,
            question=message.message,
            n_results=3,
            date_filter=detected_date
        )
        
        if brain_response and brain_response.results:
            context_used = "\n".join(brain_response.results)
            
    except Exception as e:
        print(f"Error getting context: {e}")
    
    # Generate response
    async for chunk in chat_service.process_message(message):
        full_response += chunk
    
    # Save conversation
    await chat_service.save_conversation(
        user_id=message.user_id,
        message=message.message,
        response=full_response,
        context_used=context_used
    )
    
    return ChatResponse(
        response=full_response,
        context_used=[context_used] if context_used else None
    )


@router.get("/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 10):
    """
    Get chat history for a user.
    
    Args:
        user_id: User identifier
        limit: Number of recent conversations to retrieve
        
    Returns:
        Chat history
    """
    chat_service = ChatService()
    
    try:
        history = await chat_service.get_chat_history(user_id, limit)
        if history is None:
            raise HTTPException(status_code=404, detail="No history found")
        return history
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}/date/{date}")
async def get_chat_history_by_date(user_id: str, date: str):
    """
    Get chat history for a user from a specific date.
    
    Args:
        user_id: User identifier
        date: Date in YYYY-MM-DD format
        
    Returns:
        Chat history from that date
    """
    chat_service = ChatService()
    
    try:
        # Query Brain for conversations from specific date
        brain_response = await chat_service.brain_service.query_context(
            customer_id=user_id,
            question="Show all conversations from this date",
            n_results=20,
            date_filter=date
        )
        
        if brain_response:
            return {
                "user_id": user_id,
                "date": date,
                "conversations": brain_response.results,
                "count": len(brain_response.results)
            }
        else:
            return {
                "user_id": user_id,
                "date": date,
                "conversations": [],
                "count": 0,
                "message": "No conversations found for this date"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Check health of chat services.
    
    Returns:
        Health status
    """
    chat_service = ChatService()
    
    try:
        health = await chat_service.health_check()
        return health
        
    except Exception as e:
        return {
            "ollama": False,
            "brain": False,
            "overall": False,
            "error": str(e)
        } 