"""
Chat models for Lumia application.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Chat message from user."""
    message: str
    user_id: str
    brain_id: Optional[str] = None  # Optional brain ID for dynamic selection
    system_prompt: Optional[str] = None  # Optional system prompt to control AI behavior


class ChatResponse(BaseModel):
    """Chat response from AI."""
    response: str
    context_used: Optional[List[str]] = None
    brain_id: Optional[str] = None
    system_prompt_used: Optional[str] = None


class Thread(BaseModel):
    """Represents a conversation thread."""
    thread_id: str
    user_id: str
    brain_id: str  # Brain ID for this thread
    system_prompt: Optional[str] = None  # System prompt for this thread
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message: Optional[str] = None


class ThreadMessage(BaseModel):
    """Message within a thread."""
    message_id: str
    thread_id: str
    user_id: str
    brain_id: str  # Brain ID for this message
    role: str  # "user" or "assistant"
    content: str
    system_prompt: Optional[str] = None  # System prompt used for this message
    timestamp: datetime


class CreateThreadRequest(BaseModel):
    """Request to create a new thread."""
    user_id: str
    brain_id: str  # Required brain ID for thread
    system_prompt: Optional[str] = None  # Optional system prompt for thread
    title: Optional[str] = None
    initial_message: Optional[str] = None


class ThreadChatMessage(BaseModel):
    """Chat message within a specific thread."""
    message: str
    user_id: str
    thread_id: str
    brain_id: Optional[str] = None  # Optional override for thread's brain_id
    system_prompt: Optional[str] = None  # Optional override for thread's system_prompt


class ChatHistory(BaseModel):
    """Pydantic model for chat history."""
    id: int
    user_id: str
    message: str
    response: str
    timestamp: datetime
    context_used: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class BrainIngestRequest(BaseModel):
    """Pydantic model for Brain ingest requests."""
    customer_id: str
    content: str
    metadata: Optional[dict] = None


class BrainQueryRequest(BaseModel):
    """Pydantic model for Brain query requests."""
    customer_id: str
    question: str
    n_results: int = 3


class BrainQueryResponse(BaseModel):
    """Pydantic model for Brain query responses."""
    results: List[str]
    scores: List[float]
    context: Optional[str] = None
    sources: Optional[List[dict]] = None 