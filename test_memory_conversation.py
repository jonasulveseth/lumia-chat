#!/usr/bin/env python3
"""
Test memory functionality with a conversation
"""
import asyncio
import time
import httpx
import json

async def test_memory_conversation():
    """Test memory with a conversation."""
    
    user_id = "test_memory_user"
    
    print(f"🔍 Memory conversation test...")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
        
        # First message
        print("\n📝 Message 1: 'Hej, jag heter Jonas'")
        payload = {
            "message": "Hej, jag heter Jonas",
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
                
                full_response = ""
                async for line in response.aiter_lines():
                    if line.strip() and line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if "chunk" in data:
                                full_response += data["chunk"]
                            if "done" in data:
                                break
                        except json.JSONDecodeError:
                            continue
                
                print(f"🤖 Response 1: {full_response[:100]}...")
                
        except Exception as e:
            print(f"❌ Message 1 failed: {e}")
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Second message - should reference the first
        print("\n📝 Message 2: 'Vad heter jag?'")
        payload = {
            "message": "Vad heter jag?",
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
                
                full_response = ""
                async for line in response.aiter_lines():
                    if line.strip() and line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if "chunk" in data:
                                full_response += data["chunk"]
                            if "done" in data:
                                break
                        except json.JSONDecodeError:
                            continue
                
                print(f"🤖 Response 2: {full_response[:200]}...")
                
        except Exception as e:
            print(f"❌ Message 2 failed: {e}")
    
    print("\n" + "=" * 50)
    print("📊 Memory Test Analysis:")
    print("- Check if response 2 mentions 'Jonas'")
    print("- If not, memory is not working")

if __name__ == "__main__":
    asyncio.run(test_memory_conversation()) 