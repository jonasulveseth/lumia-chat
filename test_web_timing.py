#!/usr/bin/env python3
"""
Test that simulates the web interface exactly
"""
import asyncio
import time
import httpx
import json

async def test_web_simulation():
    """Test that simulates the web interface exactly."""
    
    user_id = "test_web_user"
    message = "Hi"
    
    print(f"🌐 Web interface simulation test...")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
        # Simulate the exact web interface request
        print("\n🔍 Simulating web interface request")
        start_time = time.time()
        
        payload = {
            "message": message,
            "user_id": user_id
        }
        
        try:
            # Simulate the exact fetch call from web interface
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/stream",
                json=payload,
                timeout=30.0
            ) as response:
                response.raise_for_status()
                
                # Simulate the web interface processing
                reader = response
                decoder = None  # We don't need decoder in Python
                ai_response = ""
                chunk_count = 0
                first_chunk_time = None
                
                async for line in response.aiter_lines():
                    if line.strip():
                        # Simulate the web interface parsing
                        if line.startswith("data: "):
                            try:
                                data_str = line[6:]  # Remove "data: " prefix
                                data = json.loads(data_str)
                                
                                if "chunk" in data:
                                    if first_chunk_time is None:
                                        first_chunk_time = time.time() - start_time
                                        print(f"⏱️  First chunk (web sim): {first_chunk_time:.3f}s")
                                    
                                    chunk = data["chunk"]
                                    ai_response += chunk
                                    chunk_count += 1
                                    
                                    # Simulate rendering (just count)
                                    if chunk_count % 10 == 0:
                                        print(f"📊 Processed {chunk_count} chunks...")
                                
                                if "done" in data:
                                    print("✅ Stream completed")
                                    break
                                    
                            except json.JSONDecodeError as e:
                                print(f"❌ JSON decode error: {e}")
                                continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Total time (web sim): {total_time:.3f}s")
                print(f"📊 Total chunks: {chunk_count}")
                print(f"📄 Response length: {len(ai_response)} chars")
                
        except Exception as e:
            print(f"❌ Web simulation failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Web Simulation Analysis:")
    print("- First chunk time shows when user sees first text")
    print("- Total time shows complete response time")
    print("- Compare with your web interface experience")

if __name__ == "__main__":
    asyncio.run(test_web_simulation()) 