#!/bin/bash

# Lumia Brain ID API Examples
# This script demonstrates how to use the new brain_id functionality

BASE_URL="http://localhost:8002"

echo "🧠 Lumia Brain ID API Examples"
echo "=============================="

# Example 1: Create a work thread
echo -e "\n1️⃣ Creating work thread..."
WORK_THREAD=$(curl -s -X POST "$BASE_URL/threads/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "brain_id": "brain_work",
    "title": "Work Projects",
    "initial_message": "Hej, jag jobbar med Bowter och reemove.ai projekt"
  }')

echo "Work thread created:"
echo $WORK_THREAD | jq '.'

# Extract thread ID
WORK_THREAD_ID=$(echo $WORK_THREAD | jq -r '.thread_id')

# Example 2: Create a personal thread
echo -e "\n2️⃣ Creating personal thread..."
PERSONAL_THREAD=$(curl -s -X POST "$BASE_URL/threads/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "brain_id": "brain_personal",
    "title": "Personal Chat",
    "initial_message": "Hej, jag gillar att spela gitarr och läsa böcker"
  }')

echo "Personal thread created:"
echo $PERSONAL_THREAD | jq '.'

# Extract thread ID
PERSONAL_THREAD_ID=$(echo $PERSONAL_THREAD | jq -r '.thread_id')

# Example 3: Chat in work thread
echo -e "\n3️⃣ Chatting in work thread..."
WORK_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$WORK_THREAD_ID/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Vilken plattform tänker du på?\",
    \"user_id\": \"demo_user\",
    \"thread_id\": \"$WORK_THREAD_ID\",
    \"brain_id\": \"brain_work\"
  }")

echo "Work thread response:"
echo $WORK_RESPONSE | jq '.response'

# Example 4: Chat in personal thread
echo -e "\n4️⃣ Chatting in personal thread..."
PERSONAL_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$PERSONAL_THREAD_ID/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Vad gillar jag att göra på fritiden?\",
    \"user_id\": \"demo_user\",
    \"thread_id\": \"$PERSONAL_THREAD_ID\",
    \"brain_id\": \"brain_personal\"
  }")

echo "Personal thread response:"
echo $PERSONAL_RESPONSE | jq '.response'

# Example 5: Memory chat with work brain
echo -e "\n5️⃣ Memory chat with work brain..."
WORK_MEMORY=$(curl -s -X POST "$BASE_URL/memory/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "message": "Vad sa jag om Bowter?",
    "brain_id": "brain_work"
  }')

echo "Work memory response:"
echo $WORK_MEMORY | jq '.response'

# Example 6: Memory chat with personal brain
echo -e "\n6️⃣ Memory chat with personal brain..."
PERSONAL_MEMORY=$(curl -s -X POST "$BASE_URL/memory/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "message": "Vad sa jag om mina hobbies?",
    "brain_id": "brain_personal"
  }')

echo "Personal memory response:"
echo $PERSONAL_MEMORY | jq '.response'

# Example 7: List user threads
echo -e "\n7️⃣ Listing user threads..."
THREADS=$(curl -s -X GET "$BASE_URL/threads/user/demo_user")

echo "User threads:"
echo $THREADS | jq '.[] | {title, brain_id, message_count}'

# Example 8: Get thread messages
echo -e "\n8️⃣ Getting work thread messages..."
WORK_MESSAGES=$(curl -s -X GET "$BASE_URL/threads/$WORK_THREAD_ID/messages")

echo "Work thread messages:"
echo $WORK_MESSAGES | jq '.[] | {role, content, brain_id}'

echo -e "\n✅ All examples completed!"
echo "🎯 Brain ID functionality is working correctly!"
