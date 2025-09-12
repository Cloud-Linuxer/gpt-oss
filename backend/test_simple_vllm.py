#!/usr/bin/env python3
"""Simple test to check vLLM tool calling."""

import httpx
import json
import asyncio

VLLM_URL = "http://localhost:8000/v1/chat/completions"


async def test_tool_calling():
    """Test if vLLM supports tool calling."""
    print("=" * 80)
    print("vLLM TOOL CALLING TEST")
    print("=" * 80)
    
    # Define a simple tool
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
        {"role": "system", "content": "You are a helpful assistant that can use tools."},
        {"role": "user", "content": "Calculate 2 + 2 for me"}
    ]
    
    print("\n📝 Request:")
    print(f"Messages: {json.dumps(messages, indent=2)}")
    print(f"Tools: {json.dumps(tools, indent=2)}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: With tools
        print("\n🔧 Test 1: With tools parameter")
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = await client.post(VLLM_URL, json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Without tools
        print("\n🔧 Test 2: Without tools parameter")
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = await client.post(VLLM_URL, json=payload)
            print(f"Status: {response.status_code}")
            result = response.json()
            if "choices" in result:
                message = result["choices"][0]["message"]
                print(f"Response content: {message.get('content', 'No content')}")
                if "tool_calls" in message:
                    print(f"Tool calls: {message['tool_calls']}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 3: Check model info
        print("\n📊 Test 3: Model information")
        try:
            response = await client.get("http://localhost:8000/v1/models")
            models = response.json()
            print(f"Available models: {json.dumps(models, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_tool_calling())