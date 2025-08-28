#!/usr/bin/env python3
"""
Test raw response to check if truncation is real or just display issue
"""
import asyncio
import time
import httpx
import json

async def test_raw_response():
    """Test raw response to check truncation."""
    
    user_id = "test_raw_user"
    message = "Kan du förklara för mig hur man bygger en säljpipeline?"
    
    print(f"🔍 Raw response test...")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
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
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/stream",
                json=payload,
                headers=headers,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                chunk_count = 0
                full_response = ""
                
                async for line in response.aiter_lines():
                    if line.strip():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if "chunk" in data:
                                    if first_chunk_time is None:
                                        first_chunk_time = time.time()
                                        print(f"⏱️  First chunk: {first_chunk_time:.3f}s")
                                    
                                    chunk_count += 1
                                    full_response += data["chunk"]
                                
                                if "done" in data:
                                    total_time = time.time() - first_chunk_time if first_chunk_time else 0
                                    print(f"⏱️  Total time: {total_time:.3f}s")
                                    print(f"📊 Chunks: {chunk_count}")
                                    print(f"📝 Response length: {len(full_response)} characters")
                                    print(f"📝 Last 100 chars: '{full_response[-100:]}'")
                                    print(f"📝 Full response ends with: '{full_response[-10:]}'")
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Raw Response Analysis:")
    print("- Check if response ends with complete sentences")
    print("- Look for proper punctuation at the end")

if __name__ == "__main__":
    asyncio.run(test_raw_response()) 