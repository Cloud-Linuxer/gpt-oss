#!/usr/bin/env python3
"""Simple direct test of vLLM tool calling."""

import httpx
import json
import asyncio

VLLM_URL = "http://localhost:8000/v1/chat/completions"

async def test_simple_tool_call():
    """Test basic tool calling functionality."""
    
    tools = [{
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        }
    }]
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Use tools when available."},
        {"role": "user", "content": "Calculate 25 * 4"}
    ]
    
    request_data = {
        "model": "openai/gpt-oss-20b",
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "temperature": 0.1,
        "max_tokens": 200
    }
    
    print("📡 Sending request to vLLM...")
    print(f"Request: {json.dumps(request_data, indent=2)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(VLLM_URL, json=request_data)
            print(f"\n📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
                
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0]["message"]
                    
                    if "tool_calls" in message:
                        print("✅ Tool calls detected!")
                        for call in message["tool_calls"]:
                            print(f"  Tool: {call['function']['name']}")
                            print(f"  Args: {call['function']['arguments']}")
                    else:
                        print("❌ No tool calls in response")
                        print(f"Content: {message.get('content', 'No content')}")
                else:
                    print("❌ No choices in response")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_tool_call())