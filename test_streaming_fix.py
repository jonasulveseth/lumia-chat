#!/usr/bin/env python3
"""
Enhanced test script to verify that streaming fixes work correctly.
This tests the immediate flushing and real-time streaming capabilities with detailed timing.
"""

import asyncio
import time
import httpx
import json
from datetime import datetime

async def test_streaming_fix():
    """Test the streaming fix with detailed timing measurements."""
    
    print("🧪 Testing streaming fix with detailed timing...")
    print("=" * 60)
    
    # Test the memory chat streaming endpoint
    print("📡 Testing /memory/chat/stream endpoint...")
    
    payload = {
        "message": "Berätta en kort historia om en katt",
        "user_id": "test_user_123"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
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
                chunk_times = []
                chunk_sizes = []
                last_chunk_time = None
                
                print("🔄 Starting to read chunks...")
                print(f"⏰ Start time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                
                async for line in response.aiter_lines():
                    if line.strip():
                        if line.startswith("data: "):
                            try:
                                data_str = line[6:]  # Remove "data: " prefix
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
                                    chunk_sizes.append(len(chunk))
                                    
                                    # Calculate time since last chunk
                                    if last_chunk_time is not None:
                                        time_since_last = chunk_time - last_chunk_time
                                        print(f"📦 Chunk {chunk_count:2d} at {chunk_time:6.3f}s (+{time_since_last:5.3f}s): '{chunk}'")
                                    else:
                                        print(f"📦 Chunk {chunk_count:2d} at {chunk_time:6.3f}s (FIRST): '{chunk}'")
                                    
                                    last_chunk_time = chunk_time
                                
                                if "done" in data:
                                    total_time = time.time() - start_time
                                    print(f"✅ Stream completed in {total_time:.3f}s")
                                    print(f"⏰ End time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                                    break
                                    
                            except json.JSONDecodeError as e:
                                print(f"❌ JSON decode error: {e}")
                                continue
                
                # Detailed timing analysis
                print("\n" + "=" * 60)
                print("📊 DETAILED TIMING ANALYSIS")
                print("=" * 60)
                
                if chunk_times:
                    # Calculate timing statistics
                    time_between_chunks = [chunk_times[i] - chunk_times[i-1] for i in range(1, len(chunk_times))]
                    avg_time_between = sum(time_between_chunks) / len(time_between_chunks) if time_between_chunks else 0
                    min_time_between = min(time_between_chunks) if time_between_chunks else 0
                    max_time_between = max(time_between_chunks) if time_between_chunks else 0
                    
                    # Calculate chunk size statistics
                    avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes)
                    min_chunk_size = min(chunk_sizes)
                    max_chunk_size = max(chunk_sizes)
                    
                    print(f"📈 Total chunks: {chunk_count}")
                    print(f"📈 Response length: {len(full_response)} characters")
                    print(f"📈 Average chunk size: {avg_chunk_size:.1f} chars")
                    print(f"📈 Chunk size range: {min_chunk_size}-{max_chunk_size} chars")
                    print()
                    print(f"⏱️  First chunk latency: {first_chunk_time:.3f}s")
                    print(f"⏱️  Average time between chunks: {avg_time_between:.3f}s ({avg_time_between*1000:.1f}ms)")
                    print(f"⏱️  Min time between chunks: {min_time_between:.3f}s ({min_time_between*1000:.1f}ms)")
                    print(f"⏱️  Max time between chunks: {max_time_between:.3f}s ({max_time_between*1000:.1f}ms)")
                    print()
                    
                    # Streaming quality assessment
                    print("🎯 STREAMING QUALITY ASSESSMENT")
                    print("-" * 40)
                    
                    if avg_time_between < 0.1:  # Less than 100ms
                        print("✅ EXCELLENT: Real-time streaming (< 100ms between chunks)")
                    elif avg_time_between < 0.5:  # Less than 500ms
                        print("✅ GOOD: Fast streaming (< 500ms between chunks)")
                    elif avg_time_between < 1.0:  # Less than 1s
                        print("⚠️  ACCEPTABLE: Moderate streaming (< 1s between chunks)")
                    else:
                        print("❌ POOR: Slow streaming (> 1s between chunks)")
                    
                    if first_chunk_time < 2.0:
                        print("✅ EXCELLENT: Fast first chunk (< 2s)")
                    elif first_chunk_time < 5.0:
                        print("✅ GOOD: Reasonable first chunk (< 5s)")
                    elif first_chunk_time < 10.0:
                        print("⚠️  ACCEPTABLE: Slow first chunk (< 10s)")
                    else:
                        print("❌ POOR: Very slow first chunk (> 10s)")
                    
                    # Check for buffering indicators
                    if max_time_between > avg_time_between * 3:
                        print("⚠️  WARNING: Potential buffering detected (large time gaps)")
                    else:
                        print("✅ CONSISTENT: No buffering detected")
                    
                    print()
                    print("📝 FIRST 100 CHARACTERS:")
                    print(f"'{full_response[:100]}...'")
                    
                else:
                    print("❌ No chunks received!")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

async def test_fast_streaming():
    """Test the fast streaming endpoint with detailed timing."""
    
    print("\n" + "=" * 60)
    print("📡 Testing /memory/chat/fast endpoint...")
    print("=" * 60)
    
    payload = {
        "message": "Hej, hur mår du?",
        "user_id": "test_user_123"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/fast",
                json=payload,
                headers=headers,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                chunk_count = 0
                full_response = ""
                chunk_times = []
                last_chunk_time = None
                
                print("🔄 Starting fast streaming test...")
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
                                    
                                    if last_chunk_time is not None:
                                        time_since_last = chunk_time - last_chunk_time
                                        print(f"📦 Chunk {chunk_count:2d} at {chunk_time:6.3f}s (+{time_since_last:5.3f}s): '{chunk}'")
                                    else:
                                        print(f"📦 Chunk {chunk_count:2d} at {chunk_time:6.3f}s (FIRST): '{chunk}'")
                                    
                                    last_chunk_time = chunk_time
                                
                                if "done" in data:
                                    total_time = time.time() - start_time
                                    print(f"✅ Fast stream completed in {total_time:.3f}s")
                                    print(f"⏰ End time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                # Fast streaming analysis
                print("\n📊 FAST STREAMING ANALYSIS")
                print("-" * 40)
                print(f"📈 Total chunks: {chunk_count}")
                print(f"📈 Response length: {len(full_response)} characters")
                print(f"⏱️  First chunk latency: {first_chunk_time:.3f}s")
                print(f"⏱️  Total time: {time.time() - start_time:.3f}s")
                
                if chunk_times:
                    time_between_chunks = [chunk_times[i] - chunk_times[i-1] for i in range(1, len(chunk_times))]
                    avg_time_between = sum(time_between_chunks) / len(time_between_chunks) if time_between_chunks else 0
                    print(f"⏱️  Average time between chunks: {avg_time_between:.3f}s ({avg_time_between*1000:.1f}ms)")
                
                print(f"📝 Response: '{full_response}'")
                
    except Exception as e:
        print(f"❌ Fast streaming test failed: {e}")

async def test_streaming_consistency():
    """Test streaming consistency across multiple requests."""
    
    print("\n" + "=" * 60)
    print("🔄 Testing streaming consistency...")
    print("=" * 60)
    
    payload = {
        "message": "Test",
        "user_id": "test_user_123"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    results = []
    
    for i in range(3):
        print(f"\n🔄 Test {i+1}/3...")
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
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
                        if line.strip() and line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if "chunk" in data:
                                    if first_chunk_time is None:
                                        first_chunk_time = time.time() - start_time
                                    chunk_count += 1
                                if "done" in data:
                                    break
                            except json.JSONDecodeError:
                                continue
                    
                    total_time = time.time() - start_time
                    results.append({
                        "test": i+1,
                        "first_chunk": first_chunk_time,
                        "total_chunks": chunk_count,
                        "total_time": total_time
                    })
                    
                    print(f"   ⚡ First chunk: {first_chunk_time:.3f}s")
                    print(f"   📦 Total chunks: {chunk_count}")
                    print(f"   ⏱️  Total time: {total_time:.3f}s")
                    
        except Exception as e:
            print(f"   ❌ Test {i+1} failed: {e}")
    
    # Consistency analysis
    if results:
        print("\n📊 CONSISTENCY ANALYSIS")
        print("-" * 40)
        first_chunks = [r["first_chunk"] for r in results if r["first_chunk"] is not None]
        total_times = [r["total_time"] for r in results]
        
        if first_chunks:
            avg_first_chunk = sum(first_chunks) / len(first_chunks)
            min_first_chunk = min(first_chunks)
            max_first_chunk = max(first_chunks)
            
            print(f"⏱️  First chunk - Avg: {avg_first_chunk:.3f}s, Min: {min_first_chunk:.3f}s, Max: {max_first_chunk:.3f}s")
            
            if max_first_chunk - min_first_chunk < 0.5:
                print("✅ CONSISTENT: First chunk timing is stable")
            else:
                print("⚠️  INCONSISTENT: First chunk timing varies significantly")
        
        if total_times:
            avg_total_time = sum(total_times) / len(total_times)
            min_total_time = min(total_times)
            max_total_time = max(total_times)
            
            print(f"⏱️  Total time - Avg: {avg_total_time:.3f}s, Min: {min_total_time:.3f}s, Max: {max_total_time:.3f}s")
            
            if max_total_time - min_total_time < 1.0:
                print("✅ CONSISTENT: Total response time is stable")
            else:
                print("⚠️  INCONSISTENT: Total response time varies significantly")

async def main():
    """Run all streaming tests with detailed timing."""
    print("🚀 Starting comprehensive streaming fix verification tests...")
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await test_streaming_fix()
    await test_fast_streaming()
    await test_streaming_consistency()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print(f"⏰ Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())

