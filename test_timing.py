#!/usr/bin/env python3
"""
Detailed timing test to identify bottlenecks
"""
import asyncio
import time
import httpx
import json

async def test_detailed_timing():
    """Test detailed timing to find bottlenecks."""
    
    user_id = "test_timing_user"
    message = "Hi"
    
    print(f"🔍 Detailed timing test...")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Direct Ollama
        print("\n🔍 Test 1: Direct Ollama")
        start_time = time.time()
        
        try:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:12b",
                    "prompt": "Hello",
                    "stream": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            total_time = time.time() - start_time
            print(f"⏱️  Direct Ollama time: {total_time:.2f}s")
            print(f"📄 Response: {data.get('response', '')[:50]}...")
            
        except Exception as e:
            print(f"❌ Direct Ollama failed: {e}")
        
        # Test 2: Memory endpoint with timing
        print("\n🔍 Test 2: Memory endpoint with detailed timing")
        
        # Time the request preparation
        prep_start = time.time()
        payload = {
            "message": message,
            "user_id": user_id
        }
        prep_time = time.time() - prep_start
        print(f"⏱️  Request preparation: {prep_time:.3f}s")
        
        # Time the HTTP request
        http_start = time.time()
        try:
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/stream",
                json=payload,
                timeout=30.0
            ) as response:
                response.raise_for_status()
                http_time = time.time() - http_start
                print(f"⏱️  HTTP connection: {http_time:.3f}s")
                
                # Time the first chunk
                first_chunk_start = time.time()
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
                                        first_chunk_time = time.time() - first_chunk_start
                                        print(f"⏱️  First chunk: {first_chunk_time:.3f}s")
                                    
                                    chunk_count += 1
                                
                                if "done" in data:
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                total_time = time.time() - http_start
                print(f"⏱️  Total time: {total_time:.3f}s")
                print(f"📊 Chunks: {chunk_count}")
                
        except Exception as e:
            print(f"❌ Memory endpoint failed: {e}")
        
        # Test 3: Health check
        print("\n🔍 Test 3: Health check")
        health_start = time.time()
        try:
            response = await client.get("http://localhost:8002/health")
            health_time = time.time() - health_start
            print(f"⏱️  Health check: {health_time:.3f}s")
            print(f"📄 Response: {response.text}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Timing Analysis:")
    print("- Direct Ollama: Shows if Ollama is the bottleneck")
    print("- HTTP connection: Shows if network is the bottleneck")
    print("- First chunk: Shows if processing is the bottleneck")

if __name__ == "__main__":
    asyncio.run(test_detailed_timing()) 