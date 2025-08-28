#!/usr/bin/env python3
"""
Test script to demonstrate streaming vs non-streaming for longer responses.
"""

import asyncio
import time
import httpx
import json
from datetime import datetime

async def test_long_response_streaming():
    """Test streaming with a long response to show the difference."""
    
    print("🧪 Testing long response streaming...")
    print("=" * 60)
    
    # Test with a prompt that will generate a longer response
    payload = {
        "message": "Skriv en detaljerad historia om en magisk skog med minst 500 ord. Inkludera karaktärer, dialog, beskrivningar och en komplett handling med början, mitt och slut.",
        "user_id": "test_user_123"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/stream",
                json=payload,
                headers=headers,
                timeout=120.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                chunk_count = 0
                full_response = ""
                chunk_times = []
                last_chunk_time = None
                
                print("🔄 Starting long response streaming...")
                print(f"⏰ Start time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                
                async for line in response.aiter_lines():
                    if line.strip():
                        if line.startswith("data: "):
                            try:
                                data_str = line[6:]
                                data = json.loads(data_str)
                                
                                if "chunk" in data:
                                    chunk_time = time.time() - start_time
                                    chunk = data["chunk"]
                                    
                                    if first_chunk_time is None:
                                        first_chunk_time = chunk_time
                                        print(f"⚡ First chunk received after: {first_chunk_time:.3f}s")
                                        print(f"⏰ First chunk time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                                    
                                    full_response += chunk
                                    chunk_count += 1
                                    chunk_times.append(chunk_time)
                                    
                                    # Show progress every 20 chunks
                                    if chunk_count % 20 == 0:
                                        if last_chunk_time is not None:
                                            time_since_last = chunk_time - last_chunk_time
                                            print(f"📦 Chunk {chunk_count:3d} at {chunk_time:6.3f}s (+{time_since_last:5.3f}s): '{chunk[:20]}...' (Total: {len(full_response)} chars)")
                                        else:
                                            print(f"📦 Chunk {chunk_count:3d} at {chunk_time:6.3f}s (FIRST): '{chunk[:20]}...' (Total: {len(full_response)} chars)")
                                    
                                    last_chunk_time = chunk_time
                                
                                if "done" in data:
                                    total_time = time.time() - start_time
                                    print(f"✅ Long stream completed in {total_time:.3f}s")
                                    print(f"⏰ End time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                                    break
                                    
                            except json.JSONDecodeError as e:
                                print(f"❌ JSON decode error: {e}")
                                continue
                
                # Analysis
                print("\n" + "=" * 60)
                print("📊 LONG RESPONSE ANALYSIS")
                print("=" * 60)
                
                if chunk_times:
                    time_between_chunks = [chunk_times[i] - chunk_times[i-1] for i in range(1, len(chunk_times))]
                    avg_time_between = sum(time_between_chunks) / len(time_between_chunks) if time_between_chunks else 0
                    min_time_between = min(time_between_chunks) if time_between_chunks else 0
                    max_time_between = max(time_between_chunks) if time_between_chunks else 0
                    
                    print(f"📈 Total chunks: {chunk_count}")
                    print(f"📈 Response length: {len(full_response)} characters")
                    print(f"📈 Words: ~{len(full_response.split())} words")
                    print()
                    print(f"⏱️  First chunk latency: {first_chunk_time:.3f}s")
                    print(f"⏱️  Average time between chunks: {avg_time_between:.3f}s ({avg_time_between*1000:.1f}ms)")
                    print(f"⏱️  Min time between chunks: {min_time_between:.3f}s ({min_time_between*1000:.1f}ms)")
                    print(f"⏱️  Max time between chunks: {max_time_between:.3f}s ({max_time_between*1000:.1f}ms)")
                    print(f"⏱️  Total generation time: {time.time() - start_time:.3f}s")
                    print()
                    
                    # Calculate time to see meaningful content
                    time_to_100_chars = None
                    time_to_500_chars = None
                    accumulated_chars = 0
                    for i, chunk_time in enumerate(chunk_times):
                        # Approximate chunk size (average 3 chars per chunk)
                        accumulated_chars += 3
                        
                        if accumulated_chars >= 100 and time_to_100_chars is None:
                            time_to_100_chars = chunk_time
                        if accumulated_chars >= 500 and time_to_500_chars is None:
                            time_to_500_chars = chunk_time
                    
                    if time_to_100_chars:
                        print(f"⏱️  Time to 100 characters: {time_to_100_chars:.3f}s")
                    if time_to_500_chars:
                        print(f"⏱️  Time to 500 characters: {time_to_500_chars:.3f}s")
                    
                    print()
                    print("🎯 STREAMING BENEFITS FOR LONG RESPONSES:")
                    print("-" * 50)
                    print(f"✅ User sees first content after: {first_chunk_time:.3f}s")
                    print(f"✅ User sees 100 chars after: {time_to_100_chars:.3f}s" if time_to_100_chars else "✅ User sees meaningful content quickly")
                    print(f"✅ User sees 500 chars after: {time_to_500_chars:.3f}s" if time_to_500_chars else "✅ User sees substantial content quickly")
                    print(f"✅ Total wait time: {time.time() - start_time:.3f}s")
                    print()
                    print("📝 FIRST 200 CHARACTERS:")
                    print(f"'{full_response[:200]}...'")
                    
                else:
                    print("❌ No chunks received!")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

async def compare_streaming_vs_non_streaming():
    """Compare streaming vs non-streaming for the same prompt."""
    
    print("\n" + "=" * 60)
    print("🔄 COMPARING STREAMING VS NON-STREAMING")
    print("=" * 60)
    
    prompt = "Skriv en kort historia om en katt (max 100 ord)"
    
    # Test streaming
    print("📡 Testing STREAMING endpoint...")
    streaming_start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/stream",
                json={"message": prompt, "user_id": "test_user_123"},
                headers={"Content-Type": "application/json"},
                timeout=30.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                full_response = ""
                
                async for line in response.aiter_lines():
                    if line.strip() and line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if "chunk" in data:
                                if first_chunk_time is None:
                                    first_chunk_time = time.time() - streaming_start
                                full_response += data["chunk"]
                            if "done" in data:
                                break
                        except json.JSONDecodeError:
                            continue
                
                streaming_total = time.time() - streaming_start
                print(f"   ⚡ First chunk: {first_chunk_time:.3f}s")
                print(f"   ⏱️  Total time: {streaming_total:.3f}s")
                print(f"   📝 Response length: {len(full_response)} chars")
    
    except Exception as e:
        print(f"   ❌ Streaming test failed: {e}")
    
    # Test non-streaming
    print("\n📡 Testing NON-STREAMING endpoint...")
    non_streaming_start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "http://localhost:8002/memory/chat",
                json={"message": prompt, "user_id": "test_user_123"},
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            non_streaming_total = time.time() - non_streaming_start
            print(f"   ⏱️  Total time: {non_streaming_total:.3f}s")
            print(f"   📝 Response length: {len(data.get('response', ''))} chars")
            
            # Compare
            print(f"\n📊 COMPARISON:")
            print(f"   Streaming - First chunk: {first_chunk_time:.3f}s, Total: {streaming_total:.3f}s")
            print(f"   Non-streaming - Total: {non_streaming_total:.3f}s")
            print(f"   Difference: {non_streaming_total - first_chunk_time:.3f}s faster first content with streaming")
    
    except Exception as e:
        print(f"   ❌ Non-streaming test failed: {e}")

async def main():
    """Run all tests."""
    print("🚀 Testing streaming benefits for different response lengths...")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await test_long_response_streaming()
    await compare_streaming_vs_non_streaming()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print(f"⏰ Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())
