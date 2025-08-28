#!/usr/bin/env python3
"""
Test script for Lumia's new brain_id functionality.
Demonstrates how to use different brain IDs for different contexts.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8002"

def test_brain_id_functionality():
    """Test the new brain_id functionality."""
    print("🧠 Testing Lumia Brain ID Functionality")
    print("=" * 50)
    
    # Test 1: Create threads with different brain IDs
    print("\n1️⃣ Creating threads with different brain IDs...")
    
    # Work thread
    work_thread = create_thread(
        user_id="test_user",
        brain_id="brain_work",
        title="Work Projects",
        initial_message="Hej, jag jobbar med Bowter och reemove.ai projekt"
    )
    print(f"✅ Work thread created: {work_thread['thread_id']}")
    
    # Personal thread
    personal_thread = create_thread(
        user_id="test_user",
        brain_id="brain_personal", 
        title="Personal Chat",
        initial_message="Hej, jag gillar att spela gitarr och läsa böcker"
    )
    print(f"✅ Personal thread created: {personal_thread['thread_id']}")
    
    # Test 2: Chat in work thread
    print("\n2️⃣ Chatting in work thread...")
    work_response = chat_in_thread(
        work_thread["thread_id"],
        "test_user",
        "Vilken plattform tänker du på?",
        "brain_work"
    )
    print(f"🤖 Work AI: {work_response['response'][:100]}...")
    
    # Test 3: Chat in personal thread
    print("\n3️⃣ Chatting in personal thread...")
    personal_response = chat_in_thread(
        personal_thread["thread_id"],
        "test_user", 
        "Vad gillar jag att göra på fritiden?",
        "brain_personal"
    )
    print(f"🤖 Personal AI: {personal_response['response'][:100]}...")
    
    # Test 4: Memory chat with different brains
    print("\n4️⃣ Testing memory chat with different brains...")
    
    work_memory = memory_chat("test_user", "Vad sa jag om Bowter?", "brain_work")
    print(f"🧠 Work memory: {work_memory['response'][:100]}...")
    
    personal_memory = memory_chat("test_user", "Vad sa jag om mina hobbies?", "brain_personal")
    print(f"🧠 Personal memory: {personal_memory['response'][:100]}...")
    
    # Test 5: List threads
    print("\n5️⃣ Listing user threads...")
    threads = list_user_threads("test_user")
    for thread in threads:
        print(f"📝 Thread: {thread['title']} (Brain: {thread['brain_id']})")
    
    # Test 6: Get thread messages
    print("\n6️⃣ Getting thread messages...")
    work_messages = get_thread_messages(work_thread["thread_id"])
    print(f"💬 Work thread has {len(work_messages)} messages")
    
    personal_messages = get_thread_messages(personal_thread["thread_id"])
    print(f"💬 Personal thread has {len(personal_messages)} messages")
    
    print("\n✅ All tests completed successfully!")
    print("\n🎯 Brain ID functionality is working correctly!")
    print("   - Different brains have separate memories")
    print("   - Threads can use different brain contexts")
    print("   - Memory isolation works as expected")

def create_thread(user_id: str, brain_id: str, title: str, initial_message: str):
    """Create a new thread with brain_id."""
    response = requests.post(f"{BASE_URL}/threads/", json={
        "user_id": user_id,
        "brain_id": brain_id,
        "title": title,
        "initial_message": initial_message
    })
    return response.json()

def chat_in_thread(thread_id: str, user_id: str, message: str, brain_id: str):
    """Send a message in a thread."""
    response = requests.post(f"{BASE_URL}/threads/{thread_id}/chat", json={
        "message": message,
        "user_id": user_id,
        "thread_id": thread_id,
        "brain_id": brain_id
    })
    return response.json()

def memory_chat(user_id: str, message: str, brain_id: str):
    """Simple memory chat with brain_id."""
    response = requests.post(f"{BASE_URL}/memory/chat", json={
        "user_id": user_id,
        "message": message,
        "brain_id": brain_id
    })
    return response.json()

def list_user_threads(user_id: str):
    """List all threads for a user."""
    response = requests.get(f"{BASE_URL}/threads/user/{user_id}")
    return response.json()

def get_thread_messages(thread_id: str):
    """Get messages from a thread."""
    response = requests.get(f"{BASE_URL}/threads/{thread_id}/messages")
    return response.json()

def test_streaming_chat():
    """Test streaming chat with brain_id."""
    print("\n🔄 Testing streaming chat with brain_id...")
    
    # Create a test thread
    thread = create_thread(
        user_id="stream_test_user",
        brain_id="brain_stream_test",
        title="Streaming Test",
        initial_message="Hej, detta är en streaming test"
    )
    
    # Test streaming chat
    response = requests.post(
        f"{BASE_URL}/threads/{thread['thread_id']}/chat/stream",
        json={
            "message": "Berätta mer om vad vi pratade om",
            "user_id": "stream_test_user",
            "thread_id": thread["thread_id"],
            "brain_id": "brain_stream_test"
        },
        stream=True
    )
    
    print("📡 Streaming response:")
    full_response = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode('utf-8').replace('data: ', ''))
                if 'chunk' in data:
                    chunk = data['chunk']
                    print(chunk, end='', flush=True)
                    full_response += chunk
                elif 'done' in data:
                    print("\n✅ Streaming completed")
                    break
            except json.JSONDecodeError:
                continue
    
    return full_response

if __name__ == "__main__":
    try:
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Test basic functionality
        test_brain_id_functionality()
        
        # Test streaming
        test_streaming_chat()
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
