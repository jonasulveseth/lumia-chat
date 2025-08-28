#!/usr/bin/env python3
"""
Direct timing test for the chat endpoint
"""
import asyncio
import time
import httpx
import json

async def test_direct_timing():
    """Test direct endpoint timing."""
    
    user_id = "test_direct_user"
    message = "Hi"
    
    print(f"🔍 Direct timing test...")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
        # Test the fast endpoint
        print("\n🚀 Testing /memory/chat/fast endpoint")
        start_time = time.time()
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
        
        payload = {
            "message": message,
            "user_id": user_id
        }
        
        try:
            # Test the fast endpoint
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/fast",
                json=payload,
                headers=headers,
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
                                        print(f"⏱️  First chunk (fast): {first_chunk_time:.3f}s")
                                    
                                    chunk_count += 1
                                
                                if "done" in data:
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Total time (fast): {total_time:.3f}s")
                print(f"📊 Chunks: {chunk_count}")
                
        except Exception as e:
            print(f"❌ Fast endpoint failed: {e}")
        
        # Test the regular endpoint
        print("\n🔄 Testing /memory/chat/stream endpoint")
        start_time = time.time()
        
        try:
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/stream",
                json=payload,
                headers=headers,
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
                                        print(f"⏱️  First chunk (stream): {first_chunk_time:.3f}s")
                                    
                                    chunk_count += 1
                                
                                if "done" in data:
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Total time (stream): {total_time:.3f}s")
                print(f"📊 Chunks: {chunk_count}")
                
        except Exception as e:
            print(f"❌ Stream endpoint failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Direct Timing Analysis:")
    print("- Fast endpoint should be faster")
    print("- Stream endpoint includes memory context")

if __name__ == "__main__":
    asyncio.run(test_direct_timing()) 