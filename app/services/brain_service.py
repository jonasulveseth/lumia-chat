"""
Brain service for communication with Brain API.
"""
import time
import httpx
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.models.chat import BrainIngestRequest, BrainQueryRequest, BrainQueryResponse


class BrainService:
    """Service for communicating with Brain API."""
    
    def __init__(self):
        self.base_url = settings.brain_api_url
    
    async def ingest_content(
        self, 
        customer_id: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Ingest content into Brain for a specific customer.
        
        Args:
            customer_id: Customer collection identifier
            content: Content to ingest
            metadata: Optional metadata
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "customer_id": customer_id,
            "content": content,
            "metadata": metadata or {}
        }
        
        async with httpx.AsyncClient() as client:
            try:
                start_time = time.time()
                response = await client.post(
                    f"{self.base_url}/ingest",
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                ingest_time = time.time() - start_time
                print(f"⏱️  Brain ingest took: {ingest_time:.2f}s")
                return True
                
            except httpx.HTTPError as e:
                print(f"❌ Error ingesting content: {e}")
                return False
            except Exception as e:
                print(f"❌ Unexpected error in ingest: {e}")
                return False
    
    async def query_context(
        self, 
        customer_id: str, 
        question: str, 
        n_results: int = 3,
        date_filter: Optional[str] = None
    ) -> Optional[BrainQueryResponse]:
        """
        Query Brain for relevant context.
        
        Args:
            customer_id: Customer collection identifier
            question: Question to search for
            n_results: Number of results to return
            date_filter: Optional date filter (YYYY-MM-DD format)
            
        Returns:
            BrainQueryResponse or None if error
        """
        payload = {
            "customer_id": customer_id,
            "question": question,
            "n_results": n_results
        }
        
        # Add date filter if provided
        if date_filter:
            # Support simple string (single date) or list of dates for OR semantics
            if isinstance(date_filter, list):
                payload["metadata_filter"] = {"date": date_filter}
            else:
                payload["metadata_filter"] = {"date": date_filter}
        
        async with httpx.AsyncClient() as client:
            try:
                start_time = time.time()
                response = await client.post(
                    f"{self.base_url}/query",
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                query_time = time.time() - start_time
                print(f"⏱️  Brain query HTTP request took: {query_time:.2f}s")
                
                # Expect data to possibly include 'context' (list of strings) and 'sources' (list of {content, metadata, ...})
                context_list = data.get("context", []) or []
                sources_list = data.get("sources", []) or []
                return BrainQueryResponse(
                    results=context_list,
                    scores=[1.0] * len(context_list),
                    answer=data.get("answer", None),
                    sources=sources_list
                )
                
            except httpx.HTTPError as e:
                print(f"❌ Error querying Brain: {e}")
                return None
            except Exception as e:
                print(f"❌ Unexpected error in query: {e}")
                return None
    
    async def query_quick_context(
        self, 
        customer_id: str, 
        question: str, 
        n_results: int = 2,
        date_filter: Optional[str] = None
    ) -> Optional[BrainQueryResponse]:
        """
        Quick query Brain for context (search results only, no LLM).
        
        Args:
            customer_id: Customer collection identifier
            question: Question to search for
            n_results: Number of results to return
            date_filter: Optional date filter (YYYY-MM-DD format)
            
        Returns:
            BrainQueryResponse with search results only (no answer)
        """
        payload = {
            "customer_id": customer_id,
            "question": question,
            "n_results": n_results
        }
        
        # Add date filter if provided
        if date_filter:
            if isinstance(date_filter, list):
                payload["metadata_filter"] = {"date": date_filter}
            else:
                payload["metadata_filter"] = {"date": date_filter}
        
        async with httpx.AsyncClient() as client:
            try:
                start_time = time.time()
                response = await client.post(
                    f"{self.base_url}/search",  # Use new fast search endpoint
                    json=payload,
                    timeout=httpx.Timeout(5.0, connect=2.0)  # Reduced timeout for faster endpoint
                )
                response.raise_for_status()
                data = response.json()
                
                query_time = time.time() - start_time
                print(f"⚡ Quick Brain query took: {query_time:.2f}s")
                
                # Map response to our model (no answer field for quick queries)
                context_list = data.get("context", []) or []
                sources_list = data.get("sources", []) or []
                return BrainQueryResponse(
                    results=context_list,
                    scores=[1.0] * len(context_list),  # Default scores
                    answer=data.get("answer", None),
                    sources=sources_list
                )
                
            except httpx.HTTPError as e:
                status = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
                text = None
                try:
                    if hasattr(e, "response") and e.response is not None:
                        text = e.response.text[:300]
                except Exception:
                    text = None
                print(f"❌ Error in quick Brain query: {repr(e)} status={status} body={text}")
                return None
            except Exception as e:
                print(f"❌ Unexpected error in quick query: {e}")
                return None
    
    async def get_collection_info(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a customer's collection.
        
        Args:
            customer_id: Customer collection identifier
            
        Returns:
            Collection info or None if error
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/collections/{customer_id}",
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                print(f"Error getting collection info: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error getting collection info: {e}")
                return None
    
    async def health_check(self) -> bool:
        """
        Check if Brain API is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=5.0
                )
                response.raise_for_status()
                return True
                
            except Exception as e:
                print(f"Brain health check failed: {e}")
                return False 