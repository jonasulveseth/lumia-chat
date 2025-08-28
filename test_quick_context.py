#!/usr/bin/env python3
"""
Test quick context vs regular RAG performance
"""
import asyncio
import time
import httpx
import json

async def test_quick_context():
    """Test quick context performance vs regular RAG."""
    
    user_id = "test_quick_user"
    
    print(f"⚡ Testing Quick Context vs Regular RAG...")
    print(f"👤 User ID: {user_id}")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Regular RAG (slow)
        print("\n🔍 Test 1: Regular RAG (slow)")
        start_time = time.time()
        
        payload = {
            "message": "Hej, jag heter Jonas och jag gillar programmering",
            "user_id": user_id
        }
        
        try:
            async with client.stream(
                "POST",
                "http://localhost:8002/chat/stream?use_context=true",
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
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Test 2: Memory system with quick context
        print("\n🔍 Test 2: Memory system with quick context")
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
        
        # Test 3: Second conversation with memory
        print("\n🔍 Test 3: Second conversation (memory + quick context)")
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
    
    print("\n" + "=" * 50)
    print("📊 Quick Context Test Summary:")
    print("- Regular RAG: Should be slow (6-9 seconds)")
    print("- Memory + Quick Context: Should be faster (0.5-2 seconds)")
    print("- Second conversation: Should be even faster with cached memory")

if __name__ == "__main__":
    asyncio.run(test_quick_context()) 