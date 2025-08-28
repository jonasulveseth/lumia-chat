#!/usr/bin/env python3
"""
Test Lumia Memory System
"""
import asyncio
import time
import httpx
import json

async def test_memory_system():
    """Test the memory system with multiple conversations."""
    
    user_id = "test_user_memory"
    
    print(f"🧠 Testing Lumia Memory System...")
    print(f"👤 User ID: {user_id}")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: First conversation (no memory yet)
        print("\n🔍 Test 1: First conversation")
        start_time = time.time()
        
        payload = {
            "message": "Hej, jag heter Jonas och jag gillar programmering",
            "user_id": user_id
        }
        
        try:
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/stream",
                json=payload,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                full_response = ""
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
                                        print(f"⏱️  First chunk received after: {first_chunk_time:.2f}s")
                                    
                                    chunk = data["chunk"]
                                    full_response += chunk
                                    chunk_count += 1
                                
                                if "done" in data:
                                    print("✅ Stream completed")
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Total time: {total_time:.2f}s")
                print(f"📄 Response: {full_response[:100]}...")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Wait a moment for background updates
        print("\n⏳ Waiting for background memory updates...")
        await asyncio.sleep(3)
        
        # Test 2: Check memory stats
        print("\n🔍 Test 2: Memory stats")
        try:
            response = await client.get(f"http://localhost:8002/memory/stats/{user_id}")
            stats = response.json()
            print(f"📊 Memory stats: {stats}")
        except Exception as e:
            print(f"❌ Memory stats failed: {e}")
        
        # Test 3: Second conversation (should use memory)
        print("\n🔍 Test 3: Second conversation (with memory)")
        start_time = time.time()
        
        payload = {
            "message": "Vad kommer du ihåg om mig?",
            "user_id": user_id
        }
        
        try:
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/stream",
                json=payload,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                full_response = ""
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
                                        print(f"⏱️  First chunk received after: {first_chunk_time:.2f}s")
                                    
                                    chunk = data["chunk"]
                                    full_response += chunk
                                    chunk_count += 1
                                
                                if "done" in data:
                                    print("✅ Stream completed")
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Total time: {total_time:.2f}s")
                print(f"📄 Response: {full_response[:100]}...")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Test 4: Third conversation (more memory)
        print("\n🔍 Test 4: Third conversation (more memory)")
        start_time = time.time()
        
        payload = {
            "message": "Berätta mer om mina intressen",
            "user_id": user_id
        }
        
        try:
            async with client.stream(
                "POST",
                "http://localhost:8002/memory/chat/stream",
                json=payload,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                full_response = ""
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
                                        print(f"⏱️  First chunk received after: {first_chunk_time:.2f}s")
                                    
                                    chunk = data["chunk"]
                                    full_response += chunk
                                    chunk_count += 1
                                
                                if "done" in data:
                                    print("✅ Stream completed")
                                    break
                                    
                            except json.JSONDecodeError:
                                continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Total time: {total_time:.2f}s")
                print(f"📄 Response: {full_response[:100]}...")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        # Test 5: Final memory stats
        print("\n🔍 Test 5: Final memory stats")
        try:
            response = await client.get(f"http://localhost:8002/memory/stats/{user_id}")
            stats = response.json()
            print(f"📊 Final memory stats: {stats}")
        except Exception as e:
            print(f"❌ Memory stats failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Memory System Test Summary:")
    print("- First conversation: Should be fast (no memory)")
    print("- Second conversation: Should use short-term memory")
    print("- Third conversation: Should use both short and long-term memory")
    print("- Memory stats should show growing context")

if __name__ == "__main__":
    asyncio.run(test_memory_system()) 