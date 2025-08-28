#!/usr/bin/env python3
"""
Test different Ollama models and settings for performance
"""
import asyncio
import time
import httpx
import json

async def test_ollama_model(model_name: str, options: dict = None):
    """Test a specific Ollama model."""
    
    if options is None:
        options = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 128,
            "num_predict": 64,
            "top_k": 40,
            "repeat_penalty": 1.1,
            "num_ctx": 512,
            "num_thread": 8
        }
    
    payload = {
        "model": model_name,
        "prompt": "Hi, how are you?",
        "stream": True,
        "options": options
    }
    
    async with httpx.AsyncClient() as client:
        print(f"\n🚀 Testing model: {model_name}")
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
                                    print(f"⏱️  First chunk: {first_chunk_time:.3f}s")
                                
                                chunk_count += 1
                            
                            if data.get("done", False):
                                total_time = time.time() - start_time
                                print(f"⏱️  Total time: {total_time:.3f}s")
                                print(f"📊 Chunks: {chunk_count}")
                                break
                                
                        except json.JSONDecodeError:
                            continue
                
        except Exception as e:
            print(f"❌ Failed: {e}")

async def test_models():
    """Test different models and settings."""
    
    print(f"🔍 Ollama model performance test...")
    print("=" * 50)
    
    # Test different models
    models_to_test = [
        "llama3.1:8b-text-q8_0",
        "llama3.1:8b-text-q4_0",  # Smaller quantization
        "llama3.1:8b-text",       # No quantization
    ]
    
    for model in models_to_test:
        await test_ollama_model(model)
    
    # Test with minimal settings
    print(f"\n🔧 Testing with minimal settings...")
    minimal_options = {
        "temperature": 0.7,
        "max_tokens": 64,
        "num_predict": 32,
        "num_ctx": 256,
        "num_thread": 4
    }
    
    await test_ollama_model("llama3.1:8b-text-q8_0", minimal_options)
    
    print("\n" + "=" * 50)
    print("📊 Model Performance Analysis:")
    print("- Compare first chunk times")
    print("- Lower quantization = faster but less accurate")

if __name__ == "__main__":
    asyncio.run(test_models()) 