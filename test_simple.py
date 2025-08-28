#!/usr/bin/env python3
"""
Simple test to check if Lumia API is working
"""
import asyncio
import httpx
import json

async def test_simple():
    """Simple test of Lumia API."""
    
    print("🧪 Simple Lumia API test...")
    
    # Test 1: Health check
    print("\n🔍 Test 1: Health check")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8002/health")
            print(f"✅ Health check: {response.status_code}")
            print(f"📄 Response: {response.text}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
    
    # Test 2: Simple chat request
    print("\n🔍 Test 2: Simple chat request")
    async with httpx.AsyncClient() as client:
        payload = {
            "message": "Hi",
            "user_id": "test_user"
        }
        
        try:
            response = await client.post(
                "http://localhost:8002/chat/stream",
                json=payload,
                timeout=30.0
            )
            print(f"✅ Chat request: {response.status_code}")
            print(f"📄 Response headers: {dict(response.headers)}")
            
            # Try to read the response
            content = await response.aread()
            print(f"📄 Response content length: {len(content)}")
            print(f"📄 First 200 chars: {content[:200]}")
            
        except Exception as e:
            print(f"❌ Chat request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple()) 