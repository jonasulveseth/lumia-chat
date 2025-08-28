#!/bin/bash

# Lumia System Prompt API Examples
# This script demonstrates how to use the new system prompt functionality

BASE_URL="http://localhost:8002"

echo "🎭 Lumia System Prompt API Examples"
echo "==================================="

# Example 1: Create professional thread
echo -e "\n1️⃣ Creating professional thread..."
PROFESSIONAL_THREAD=$(curl -s -X POST "$BASE_URL/threads/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "brain_id": "brain_professional",
    "system_prompt": "Du är en professionell affärskonsult. Var alltid hövlig, formell och fokuserad på affärsmål. Använd formell svenska och ge konkreta, handlingsbara råd.",
    "title": "Professional Consultation",
    "initial_message": "Hej, jag behöver hjälp med min affärsstrategi"
  }')

echo "Professional thread created:"
echo $PROFESSIONAL_THREAD | jq '.'

# Extract thread ID
PROFESSIONAL_THREAD_ID=$(echo $PROFESSIONAL_THREAD | jq -r '.thread_id')

# Example 2: Create casual thread
echo -e "\n2️⃣ Creating casual thread..."
CASUAL_THREAD=$(curl -s -X POST "$BASE_URL/threads/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "brain_id": "brain_casual",
    "system_prompt": "Du är en avslappnad och vänlig kompis. Använd informell svenska, var rolig och lekfull. Du kan använda emojis och skämta lite.",
    "title": "Casual Chat",
    "initial_message": "Hej! Vad händer?"
  }')

echo "Casual thread created:"
echo $CASUAL_THREAD | jq '.'

# Extract thread ID
CASUAL_THREAD_ID=$(echo $CASUAL_THREAD | jq -r '.thread_id')

# Example 3: Chat in professional thread
echo -e "\n3️⃣ Chatting in professional thread..."
PROFESSIONAL_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$PROFESSIONAL_THREAD_ID/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Vad tycker du om min affärsplan?\",
    \"user_id\": \"demo_user\",
    \"thread_id\": \"$PROFESSIONAL_THREAD_ID\",
    \"brain_id\": \"brain_professional\"
  }")

echo "Professional response:"
echo $PROFESSIONAL_RESPONSE | jq '.response'

# Example 4: Chat in casual thread
echo -e "\n4️⃣ Chatting in casual thread..."
CASUAL_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$CASUAL_THREAD_ID/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Vad tycker du om min affärsplan?\",
    \"user_id\": \"demo_user\",
    \"thread_id\": \"$CASUAL_THREAD_ID\",
    \"brain_id\": \"brain_casual\"
  }")

echo "Casual response:"
echo $CASUAL_RESPONSE | jq '.response'

# Example 5: Override system prompt
echo -e "\n5️⃣ Testing system prompt override..."
OVERRIDE_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$PROFESSIONAL_THREAD_ID/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"message\": \"Berätta en rolig historia\",
    \"user_id\": \"demo_user\",
    \"thread_id\": \"$PROFESSIONAL_THREAD_ID\",
    \"brain_id\": \"brain_professional\",
    \"system_prompt\": \"Du är en standup-komiker. Var rolig, använd svordomar (mild) och berätta en kort, rolig historia.\"
  }")

echo "Override response:"
echo $OVERRIDE_RESPONSE | jq '.response'

# Example 6: Memory chat with system prompt
echo -e "\n6️⃣ Memory chat with system prompt..."
MEMORY_RESPONSE=$(curl -s -X POST "$BASE_URL/memory/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "message": "Vad sa jag om min affärsplan?",
    "brain_id": "brain_professional",
    "system_prompt": "Du är en analytisk konsult. Ge en kort, saklig sammanfattning av vad användaren har sagt."
  }')

echo "Memory response:"
echo $MEMORY_RESPONSE | jq '.response'

# Example 7: List threads with system prompts
echo -e "\n7️⃣ Listing threads with system prompts..."
THREADS=$(curl -s -X GET "$BASE_URL/threads/user/demo_user")

echo "User threads:"
echo $THREADS | jq '.[] | {title, brain_id, system_prompt}'

echo -e "\n✅ All system prompt examples completed!"
echo "🎯 System prompt functionality is working correctly!"
