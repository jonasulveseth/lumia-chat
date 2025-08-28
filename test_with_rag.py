#!/usr/bin/env python3
"""
Test Lumia with RAG enabled to check Brain optimizations
"""
import asyncio
import time
import httpx
import json

async def test_with_rag():
    """Test Lumia with RAG enabled to check Brain performance."""
    
    test_message = "Hello, how are you today?"
    
    print(f"🧠 Testing Lumia with RAG ENABLED...")
    print(f"📝 Test message: '{test_message}'")
    print("=" * 50)
    
    # Test with RAG enabled
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        # Use query parameter to enable RAG
        url = "http://localhost:8002/chat/stream?use_context=true"
        payload = {
            "message": test_message,
            "user_id": "test_user"
        }
        
        try:
            async with client.stream(
                "POST",
                url,
                json=payload,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                full_response = ""
                chunk_count = 0
                
                async for line in response.aiter_lines():
                    if line.strip():
                        if line.startswith("data: "):
                            try:
                                data_str = line[6:]
                                data = json.loads(data_str)
                                
                                if "chunk" in data:
                                    if first_chunk_time is None:
                                        first_chunk_time = time.time() - start_time
                                        print(f"⏱️  First chunk received after: {first_chunk_time:.2f}s")
                                    
                                    chunk = data["chunk"]
                                    full_response += chunk
                                    chunk_count += 1
                                
                                if "done" in data:
                                    print("✅ Stream completed")
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Lumia (RAG enabled) total time: {total_time:.2f}s")
                print(f"📊 Generated {chunk_count} chunks")
                print(f"📄 Response: {full_response[:100]}...")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_with_rag()) 