#!/usr/bin/env python3
"""
Test Lumia in fast mode (no RAG)
"""
import asyncio
import time
import httpx
import json

async def test_fast_mode():
    """Test Lumia with RAG disabled for faster responses."""
    
    test_message = "Hello, how are you today?"
    
    print(f"🚀 Testing Lumia in FAST MODE (no RAG)...")
    print(f"📝 Test message: '{test_message}'")
    print("=" * 50)
    
    # Test with RAG disabled
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        payload = {
            "message": test_message,
            "user_id": "test_user"
        }
        
        try:
            async with client.stream(
                "POST",
                "http://localhost:8002/chat/stream",
                json=payload,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                full_response = ""
                chunk_count = 0
                
                async for line in response.aiter_lines():
                    if line.strip():
                        # Parse Server-Sent Event format: "data: {...}\n\n"
                        if line.startswith("data: "):
                            try:
                                data_str = line[6:]  # Remove "data: " prefix
                                data = json.loads(data_str)
                                
                                if "chunk" in data:
                                    if first_chunk_time is None:
                                        first_chunk_time = time.time() - start_time
                                        print(f"⏱️  First chunk received after: {first_chunk_time:.2f}s")
                                    
                                    chunk = data["chunk"]
                                    full_response += chunk
                                    chunk_count += 1
                                    print(f"📦 Chunk {chunk_count}: '{chunk}'")
                                
                                if "done" in data:
                                    print("✅ Stream completed")
                                    break
                                    
                            except json.JSONDecodeError as e:
                                print(f"❌ JSON decode error: {e}")
                                print(f"📄 Raw line: {line}")
                                continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Lumia (no RAG) total time: {total_time:.2f}s")
                print(f"📊 Generated {chunk_count} chunks")
                print(f"📄 Full response: {full_response}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_fast_mode()) 