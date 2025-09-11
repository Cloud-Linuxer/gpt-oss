#!/bin/bash

# vLLM API test script

API_URL=${API_URL:-"http://localhost:8000"}
MODEL_NAME=${MODEL_NAME:-"facebook/opt-125m"}

echo "Testing vLLM API at $API_URL"
echo "================================"

# Test 1: Health check
echo -n "1. Health check... "
if curl -s -f "$API_URL/health" > /dev/null 2>&1; then
    echo "✓ OK"
else
    echo "✗ FAILED"
    echo "   Server might not be running or not ready yet"
    exit 1
fi

# Test 2: Get models
echo -n "2. Getting models... "
MODELS=$(curl -s "$API_URL/v1/models" | jq -r '.data[0].id' 2>/dev/null)
if [ -n "$MODELS" ]; then
    echo "✓ OK (Model: $MODELS)"
else
    echo "✗ FAILED"
    exit 1
fi

# Test 3: Completions API
echo "3. Testing completions API..."
RESPONSE=$(curl -s -X POST "$API_URL/v1/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "'"$MODELS"'",
        "prompt": "Hello, my name is",
        "max_tokens": 16,
        "temperature": 0.7
    }')

if echo "$RESPONSE" | jq -r '.choices[0].text' > /dev/null 2>&1; then
    TEXT=$(echo "$RESPONSE" | jq -r '.choices[0].text')
    echo "   ✓ Response: $TEXT"
else
    echo "   ✗ FAILED"
    echo "   Response: $RESPONSE"
    exit 1
fi

# Test 4: Chat completions API
echo "4. Testing chat completions API..."
CHAT_RESPONSE=$(curl -s -X POST "$API_URL/v1/chat/completions" \
    -H "Content-Type: application/json" \
    -d '{
        "model": "'"$MODELS"'",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }')

if echo "$CHAT_RESPONSE" | jq -r '.choices[0].message.content' > /dev/null 2>&1; then
    CHAT_TEXT=$(echo "$CHAT_RESPONSE" | jq -r '.choices[0].message.content')
    echo "   ✓ Response: $CHAT_TEXT"
else
    echo "   ✗ FAILED"
    echo "   Response: $CHAT_RESPONSE"
    exit 1
fi

echo ""
echo "================================"
echo "All tests passed! vLLM is working correctly."