"""
RAG models for Brain service.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class IngestRequest(BaseModel):
    """Request model for ingesting content."""
    customer_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class IngestResponse(BaseModel):
    """Response model for ingestion."""
    success: bool
    message: str
    customer_id: str
    timestamp: datetime


class QueryRequest(BaseModel):
    """Request model for querying content."""
    customer_id: str
    question: str
    n_results: int = 3
    similarity_threshold: Optional[float] = None


class QueryResponse(BaseModel):
    """Response model for queries."""
    results: List[str]
    scores: List[float]
    context: Optional[str] = None
    customer_id: str
    question: str


class CollectionInfo(BaseModel):
    """Model for collection information."""
    customer_id: str
    document_count: int
    created_at: datetime
    last_updated: datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    ollama_healthy: bool
    chroma_healthy: bool 