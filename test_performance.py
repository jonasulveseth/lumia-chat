#!/usr/bin/env python3
"""
Performance test script for Lumia
"""
import asyncio
import time
import httpx
import json

async def test_lumia_performance():
    """Test Lumia performance with timing measurements."""
    
    # Test message
    test_message = "Hello, how are you today?"
    
    print(f"🧪 Testing Lumia performance...")
    print(f"📝 Test message: '{test_message}'")
    print("=" * 50)
    
    # Test 1: Direct Ollama (for comparison)
    print("\n🔍 Test 1: Direct Ollama (baseline)")
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        payload = {
            "model": "gemma3:12b",
            "prompt": f"Du är Lumia, en hjälpsam AI-assistent. Svar på svenska.\n\nAnvändare: {test_message}\nLumia:",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048
            }
        }
        
        try:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            data = response.json()
            direct_time = time.time() - start_time
            print(f"⏱️  Direct Ollama response time: {direct_time:.2f}s")
            print(f"📄 Response: {data.get('response', '')[:100]}...")
            
        except Exception as e:
            print(f"❌ Direct Ollama test failed: {e}")
    
    # Test 2: Lumia with context
    print("\n🔍 Test 2: Lumia with RAG context")
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        payload = {
            "message": test_message,
            "user_id": "test_user"
        }
        
        try:
            async with client.stream(
                "POST",
                "http://localhost:8002/chat/stream",
                json=payload,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                full_response = ""
                chunk_count = 0
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "chunk" in data:
                                if first_chunk_time is None:
                                    first_chunk_time = time.time() - start_time
                                    print(f"⏱️  First chunk received after: {first_chunk_time:.2f}s")
                                
                                chunk = data["chunk"]
                                full_response += chunk
                                chunk_count += 1
                                
                        except json.JSONDecodeError:
                            continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Lumia total response time: {total_time:.2f}s")
                print(f"📊 Generated {chunk_count} chunks")
                print(f"📄 Response: {full_response[:100]}...")
                
        except Exception as e:
            print(f"❌ Lumia test failed: {e}")
    
    # Test 3: Lumia without context
    print("\n🔍 Test 3: Lumia without RAG context")
    start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        payload = {
            "message": test_message,
            "user_id": "test_user",
            "use_context": False
        }
        
        try:
            async with client.stream(
                "POST",
                "http://localhost:8002/chat/stream",
                json=payload,
                timeout=60.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                full_response = ""
                chunk_count = 0
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "chunk" in data:
                                if first_chunk_time is None:
                                    first_chunk_time = time.time() - start_time
                                    print(f"⏱️  First chunk received after: {first_chunk_time:.2f}s")
                                
                                chunk = data["chunk"]
                                full_response += chunk
                                chunk_count += 1
                                
                        except json.JSONDecodeError:
                            continue
                
                total_time = time.time() - start_time
                print(f"⏱️  Lumia (no context) total time: {total_time:.2f}s")
                print(f"📊 Generated {chunk_count} chunks")
                print(f"📄 Response: {full_response[:100]}...")
                
        except Exception as e:
            print(f"❌ Lumia (no context) test failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Performance Summary:")
    print("Compare the times above to identify bottlenecks:")
    print("- If direct Ollama is much faster → RAG/Brain is the bottleneck")
    print("- If Lumia without context is much faster → Brain query is the bottleneck")
    print("- If all are slow → Ollama model is the bottleneck")

if __name__ == "__main__":
    asyncio.run(test_lumia_performance()) 