#!/usr/bin/env python3
"""
Test with complex message to check truncation
"""
import asyncio
import time
import httpx
import json

async def test_complex_message():
    """Test with a complex message to check for truncation."""
    
    user_id = "test_complex_user"
    message = "Kan du förklara för mig hur man bygger en säljpipeline och vad de viktigaste stegen är för att få den att fungera effektivt?"
    
    print(f"🔍 Complex message test...")
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
                                data_str = line[6:]
                                data = json.loads(data_str)
                                
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
                                    print(f"📝 Last 50 chars: '{full_response[-50:]}'")
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Complex Message Analysis:")
    print("- Check if response is complete")
    print("- Look for truncation at the end")

if __name__ == "__main__":
    asyncio.run(test_complex_message()) 