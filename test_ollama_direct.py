#!/usr/bin/env python3
"""
Direct Ollama performance test
"""
import asyncio
import time
import httpx
import json

async def test_ollama_direct():
    """Test Ollama performance directly."""
    
    print(f"🔍 Direct Ollama performance test...")
    print("=" * 50)
    
    # Test direct Ollama API
    payload = {
        "model": "llama3.1:8b-text-q8_0",
        "prompt": "Hi, how are you?",
        "stream": True,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 256,
            "num_predict": 128,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "num_ctx": 1024,
            "num_thread": 8,
            "num_gpu": 1,
            "num_gqa": 8,
            "rope_freq_base": 10000,
            "rope_freq_scale": 0.5
        }
    }
    
    async with httpx.AsyncClient() as client:
        print("\n🚀 Testing direct Ollama API...")
        start_time = time.time()
        
        try:
            async with client.stream(
                "POST",
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30.0
            ) as response:
                response.raise_for_status()
                
                first_chunk_time = None
                chunk_count = 0
                
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                if first_chunk_time is None:
                                    first_chunk_time = time.time() - start_time
                                    print(f"⏱️  First chunk from Ollama: {first_chunk_time:.3f}s")
                                
                                chunk_count += 1
                            
                            if data.get("done", False):
                                total_time = time.time() - start_time
                                print(f"⏱️  Total Ollama time: {total_time:.3f}s")
                                print(f"📊 Ollama chunks: {chunk_count}")
                                break
                                
                        except json.JSONDecodeError:
                            continue
                
        except Exception as e:
            print(f"❌ Direct Ollama test failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Ollama Performance Analysis:")
    print("- This tests Ollama directly without any overhead")
    print("- If this is slow, the issue is with Ollama itself")

if __name__ == "__main__":
    asyncio.run(test_ollama_direct()) 