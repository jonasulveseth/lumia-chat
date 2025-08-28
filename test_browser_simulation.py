#!/usr/bin/env python3
"""
Test that simulates browser fetch exactly
"""
import asyncio
import time
import httpx
import json

async def test_browser_fetch():
    """Test that simulates browser fetch exactly."""
    
    user_id = "test_browser_user"
    message = "Hi"
    
    print(f"🌐 Browser fetch simulation test...")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
        # Simulate browser fetch with exact headers
        print("\n🔍 Simulating browser fetch")
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
            # Simulate the exact browser fetch
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/stream",
                json=payload,
                headers=headers,
                timeout=30.0
            ) as response:
                response.raise_for_status()
                
                # Simulate browser processing
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
                                        print(f"⏱️  First chunk (browser sim): {first_chunk_time:.3f}s")
                                    
                                    chunk_count += 1
                                
                                if "done" in data:
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Total time (browser sim): {total_time:.3f}s")
                print(f"📊 Chunks: {chunk_count}")
                
        except Exception as e:
            print(f"❌ Browser simulation failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Browser Simulation Analysis:")
    print("- This simulates the exact browser fetch")
    print("- Compare with web interface experience")

if __name__ == "__main__":
    asyncio.run(test_browser_fetch()) 