#!/usr/bin/env python3
"""
Test to check which endpoints are available and their performance
"""
import asyncio
import time
import httpx
import json

async def test_endpoints():
    """Test different endpoints to see which one is being used."""
    
    user_id = "test_endpoint_user"
    message = "Hej, test"
    
    print(f"🔍 Testing different endpoints...")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Regular chat endpoint
        print("\n🔍 Test 1: Regular chat endpoint (/chat/stream)")
        start_time = time.time()
        
        payload = {
            "message": message,
            "user_id": user_id
        }
        
        try:
            async with client.stream(
                "POST",
                "http://localhost:8002/chat/stream",
                json=payload,
                timeout=30.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
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
                                        print(f"⏱️  First chunk: {first_chunk_time:.2f}s")
                                    
                                    chunk_count += 1
                                
                                if "done" in data:
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Total time: {total_time:.2f}s")
                print(f"📊 Chunks: {chunk_count}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Test 2: Memory chat endpoint
        print("\n🔍 Test 2: Memory chat endpoint (/memory/chat/stream)")
        start_time = time.time()
        
        payload = {
            "message": message,
            "user_id": user_id
        }
        
        try:
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/stream",
                json=payload,
                timeout=30.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
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
                                        print(f"⏱️  First chunk: {first_chunk_time:.2f}s")
                                    
                                    chunk_count += 1
                                
                                if "done" in data:
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Total time: {total_time:.2f}s")
                print(f"📊 Chunks: {chunk_count}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Test 3: Check available endpoints
        print("\n🔍 Test 3: Available endpoints")
        try:
            response = await client.get("http://localhost:8002/docs")
            print(f"✅ API docs available at: http://localhost:8002/docs")
        except Exception as e:
            print(f"❌ API docs failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Endpoint Test Summary:")
    print("- /chat/stream: Regular RAG (should be slow)")
    print("- /memory/chat/stream: Memory system (should be faster)")
    print("- Check which endpoint your chat interface is using!")

if __name__ == "__main__":
    asyncio.run(test_endpoints()) 