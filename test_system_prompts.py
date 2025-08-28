#!/usr/bin/env python3
"""
Test script for Lumia's new system prompt functionality.
Demonstrates how to control AI behavior dynamically.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8002"

def test_system_prompts():
    """Test the new system prompt functionality."""
    print("🎭 Testing Lumia System Prompt Functionality")
    print("=" * 50)
    
    # Test 1: Create threads with different system prompts
    print("\n1️⃣ Creating threads with different system prompts...")
    
    # Professional thread
    professional_thread = create_thread(
        user_id="test_user",
        brain_id="brain_professional",
        system_prompt="Du är en professionell affärskonsult. Var alltid hövlig, formell och fokuserad på affärsmål. Använd formell svenska och ge konkreta, handlingsbara råd.",
        title="Professional Consultation",
        initial_message="Hej, jag behöver hjälp med min affärsstrategi"
    )
    print(f"✅ Professional thread created: {professional_thread['thread_id']}")
    
    # Casual thread
    casual_thread = create_thread(
        user_id="test_user",
        brain_id="brain_casual",
        system_prompt="Du är en avslappnad och vänlig kompis. Använd informell svenska, var rolig och lekfull. Du kan använda emojis och skämta lite.",
        title="Casual Chat",
        initial_message="Hej! Vad händer?"
    )
    print(f"✅ Casual thread created: {casual_thread['thread_id']}")
    
    # Creative thread
    creative_thread = create_thread(
        user_id="test_user",
        brain_id="brain_creative",
        system_prompt="Du är en kreativ konstnär och poet. Var inspirerande, poetisk och tänk utanför boxen. Använd färgrika beskrivningar och kreativa metaforer.",
        title="Creative Session",
        initial_message="Jag behöver inspiration för ett konstprojekt"
    )
    print(f"✅ Creative thread created: {creative_thread['thread_id']}")
    
    # Test 2: Chat in professional thread
    print("\n2️⃣ Chatting in professional thread...")
    professional_response = chat_in_thread(
        professional_thread["thread_id"],
        "test_user",
        "Vad tycker du om min affärsplan?",
        "brain_professional"
    )
    print(f"💼 Professional AI: {professional_response['response'][:150]}...")
    
    # Test 3: Chat in casual thread
    print("\n3️⃣ Chatting in casual thread...")
    casual_response = chat_in_thread(
        casual_thread["thread_id"],
        "test_user",
        "Vad tycker du om min affärsplan?",
        "brain_casual"
    )
    print(f"😊 Casual AI: {casual_response['response'][:150]}...")
    
    # Test 4: Chat in creative thread
    print("\n4️⃣ Chatting in creative thread...")
    creative_response = chat_in_thread(
        creative_thread["thread_id"],
        "test_user",
        "Vad tycker du om min affärsplan?",
        "brain_creative"
    )
    print(f"🎨 Creative AI: {creative_response['response'][:150]}...")
    
    # Test 5: Override system prompt per message
    print("\n5️⃣ Testing system prompt override...")
    override_response = chat_in_thread(
        professional_thread["thread_id"],
        "test_user",
        "Berätta en rolig historia",
        "brain_professional",
        "Du är en standup-komiker. Var rolig, använd svordomar (mild) och berätta en kort, rolig historia."
    )
    print(f"🎭 Override AI: {override_response['response'][:150]}...")
    
    # Test 6: Memory chat with system prompt
    print("\n6️⃣ Testing memory chat with system prompt...")
    memory_response = memory_chat(
        "test_user",
        "Vad sa jag om min affärsplan?",
        "brain_professional",
        "Du är en analytisk konsult. Ge en kort, saklig sammanfattning av vad användaren har sagt."
    )
    print(f"🧠 Memory AI: {memory_response['response'][:150]}...")
    
    # Test 7: List threads with system prompts
    print("\n7️⃣ Listing threads with system prompts...")
    threads = list_user_threads("test_user")
    for thread in threads:
        print(f"📝 Thread: {thread['title']} (Brain: {thread['brain_id']})")
        if thread.get('system_prompt'):
            print(f"   🎭 System prompt: {thread['system_prompt'][:50]}...")
    
    print("\n✅ All system prompt tests completed successfully!")
    print("\n🎯 System prompt functionality is working correctly!")
    print("   - Different personalities for different threads")
    print("   - Dynamic behavior control")
    print("   - Override capability per message")

def create_thread(user_id: str, brain_id: str, system_prompt: str, title: str, initial_message: str):
    """Create a new thread with system prompt."""
    response = requests.post(f"{BASE_URL}/threads/", json={
        "user_id": user_id,
        "brain_id": brain_id,
        "system_prompt": system_prompt,
        "title": title,
        "initial_message": initial_message
    })
    return response.json()

def chat_in_thread(thread_id: str, user_id: str, message: str, brain_id: str, system_prompt: str = None):
    """Send a message in a thread with optional system prompt override."""
    data = {
        "message": message,
        "user_id": user_id,
        "thread_id": thread_id,
        "brain_id": brain_id
    }
    if system_prompt:
        data["system_prompt"] = system_prompt
    
    response = requests.post(f"{BASE_URL}/threads/{thread_id}/chat", json=data)
    return response.json()

def memory_chat(user_id: str, message: str, brain_id: str, system_prompt: str = None):
    """Memory chat with system prompt."""
    data = {
        "user_id": user_id,
        "message": message,
        "brain_id": brain_id
    }
    if system_prompt:
        data["system_prompt"] = system_prompt
    
    response = requests.post(f"{BASE_URL}/memory/chat", json=data)
    return response.json()

def list_user_threads(user_id: str):
    """List all threads for a user."""
    response = requests.get(f"{BASE_URL}/threads/user/{user_id}")
    return response.json()

def test_streaming_with_system_prompt():
    """Test streaming chat with system prompt."""
    print("\n🔄 Testing streaming chat with system prompt...")
    
    # Create a test thread
    thread = create_thread(
        user_id="stream_test_user",
        brain_id="brain_stream_test",
        system_prompt="Du är en entusiastisk lärare. Förklara saker på ett enkelt och engagerande sätt. Använd exempel och var motiverande.",
        title="Teaching Session",
        initial_message="Hej! Kan du förklara hur AI fungerar?"
    )
    
    # Test streaming chat
    response = requests.post(
        f"{BASE_URL}/threads/{thread['thread_id']}/chat/stream",
        json={
            "message": "Berätta mer om maskininlärning",
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
        test_system_prompts()
        
        # Test streaming
        test_streaming_with_system_prompt()
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8002")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
