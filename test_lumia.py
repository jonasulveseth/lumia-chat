#!/usr/bin/env python3
"""
Test script for Lumia functionality.
"""
import asyncio
import httpx
import json
from app.services.brain_service import BrainService
from app.services.ollama_service import OllamaService


async def test_brain_connection():
    """Test connection to Brain service."""
    print("🧠 Testing Brain connection...")
    
    brain_service = BrainService()
    
    # Test health check
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8000/health")
            if response.status_code == 200:
                print("✅ Brain service is healthy")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Brain service health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to Brain service: {e}")
        return False
    
    # Test collection creation
    try:
        collection_data = {
            "customer_id": "lumia_test_user",
            "description": "Test collection for Lumia",
            "metadata": {"source": "test"}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:8000/collections",
                json=collection_data
            )
            if response.status_code == 200:
                print("✅ Test collection created successfully")
            else:
                print(f"⚠️  Collection creation failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Collection creation error: {e}")
    
    return True


async def test_ollama_connection():
    """Test connection to Ollama."""
    print("🤖 Testing Ollama connection...")
    
    ollama_service = OllamaService()
    
    try:
        models = await ollama_service.list_models()
        if models:
            print(f"✅ Ollama is running, found {len(models)} models")
            print(f"   Available models: {models[:3]}...")  # Show first 3
        else:
            print("⚠️  Ollama is running but no models found")
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        return False
    
    return True


async def test_chat_functionality():
    """Test basic chat functionality."""
    print("💬 Testing chat functionality...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8002/chat/",
                json={
                    "message": "Hej! Kan du berätta vad Lumia är?",
                    "user_id": "lumia_test_user"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Chat endpoint working")
                print(f"   Response: {data['response'][:100]}...")
            else:
                print(f"❌ Chat endpoint failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Chat test failed: {e}")


async def main():
    """Run all tests."""
    print("🚀 Starting Lumia tests...")
    print("=" * 50)
    
    # Test Brain connection
    brain_ok = await test_brain_connection()
    
    # Test Ollama connection
    ollama_ok = await test_ollama_connection()
    
    print("\n" + "=" * 50)
    
    if brain_ok and ollama_ok:
        print("✅ All services are ready!")
        print("\n🎯 Starting chat test...")
        await test_chat_functionality()
    else:
        print("❌ Some services are not available")
        print("   Please ensure:")
        print("   - Brain service is running on http://127.0.0.1:8000")
        print("   - Ollama is running on http://localhost:11434")
        print("   - Lumia is running on http://localhost:8002")
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")


if __name__ == "__main__":
    asyncio.run(main()) 