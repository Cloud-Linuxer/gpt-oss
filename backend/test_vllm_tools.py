#!/usr/bin/env python3
"""Test vLLM integration with tool system - Real world examples."""

import httpx
import json
import asyncio
from typing import Dict, List, Any

# vLLM API endpoint
VLLM_URL = "http://localhost:8000/v1/chat/completions"
TOOL_API_URL = "http://localhost:8001"


async def get_tool_schemas():
    """Get tool schemas from our tool API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TOOL_API_URL}/tools")
        tools = response.json()["tools"]
        
        # Convert to OpenAI function calling format
        schemas = []
        for tool in tools:
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"]
                }
            })
        return schemas


async def execute_tool(tool_name: str, parameters: Dict[str, Any]):
    """Execute a tool through our API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TOOL_API_URL}/execute",
            json={"tool_name": tool_name, "parameters": parameters}
        )
        return response.json()


async def chat_with_tools(messages: List[Dict], tools: List[Dict] = None):
    """Chat with vLLM using tools."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        response = await client.post(VLLM_URL, json=payload)
        return response.json()


async def test_scenarios():
    """Test various real-world scenarios."""
    print("=" * 80)
    print("vLLM + TOOL SYSTEM REAL WORLD TESTS")
    print("=" * 80)
    
    # Get available tools
    tool_schemas = await get_tool_schemas()
    print(f"\n📋 Available tools: {len(tool_schemas)}")
    
    # Test 1: Math Calculation
    print("\n" + "=" * 80)
    print("TEST 1: Complex Math Calculation")
    print("-" * 80)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to calculation tools. Use the calculator tool to solve math problems."},
        {"role": "user", "content": "What is the result of: (25 * 4) + sqrt(144) - pow(2, 3)?"}
    ]
    
    print("👤 User: What is the result of: (25 * 4) + sqrt(144) - pow(2, 3)?")
    
    try:
        response = await chat_with_tools(messages, tool_schemas)
        choice = response["choices"][0]
        msg = choice["message"]
        
        if "tool_calls" in msg and msg["tool_calls"]:
            print("\n🤖 AI is using tools:")
            messages.append(msg)
            
            for tool_call in msg["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                print(f"  📞 Calling: {func_name}")
                print(f"     Args: {func_args}")
                
                # Execute tool
                tool_result = await execute_tool(func_name, func_args)
                print(f"     Result: {tool_result['data']}")
                
                # Add tool response
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result['data'])
                })
            
            # Get final response
            final_response = await chat_with_tools(messages, tool_schemas)
            final_msg = final_response["choices"][0]["message"]["content"]
            print(f"\n🤖 AI Final Answer: {final_msg}")
        else:
            print(f"🤖 AI: {msg.get('content', 'No response')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: System Information Query
    print("\n" + "=" * 80)
    print("TEST 2: System Information Query")
    print("-" * 80)
    
    messages = [
        {"role": "system", "content": "You are a system administrator assistant. Use the system_info tool to get system information."},
        {"role": "user", "content": "How much memory and disk space is available on this system?"}
    ]
    
    print("👤 User: How much memory and disk space is available on this system?")
    
    try:
        response = await chat_with_tools(messages, tool_schemas)
        choice = response["choices"][0]
        msg = choice["message"]
        
        if "tool_calls" in msg and msg["tool_calls"]:
            print("\n🤖 AI is using tools:")
            messages.append(msg)
            
            for tool_call in msg["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                print(f"  📞 Calling: {func_name}")
                print(f"     Args: {func_args}")
                
                tool_result = await execute_tool(func_name, func_args)
                if tool_result['status'] == 'success':
                    data = tool_result['data']
                    if 'memory' in data:
                        print(f"     Memory: {data['memory']['available_gb']:.1f}GB available of {data['memory']['total_gb']:.1f}GB")
                    if 'disk' in data:
                        print(f"     Disk: {data['disk']['free_gb']:.1f}GB free of {data['disk']['total_gb']:.1f}GB")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result['data'])
                })
            
            final_response = await chat_with_tools(messages, tool_schemas)
            final_msg = final_response["choices"][0]["message"]["content"]
            print(f"\n🤖 AI Final Answer: {final_msg}")
        else:
            print(f"🤖 AI: {msg.get('content', 'No response')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: File Operations
    print("\n" + "=" * 80)
    print("TEST 3: File Operations")
    print("-" * 80)
    
    messages = [
        {"role": "system", "content": "You are a file system assistant. Use file tools to manage files."},
        {"role": "user", "content": "Create a file called /tmp/ai_test.txt with the content 'Hello from AI with tools!' and then read it back to confirm."}
    ]
    
    print("👤 User: Create a file called /tmp/ai_test.txt with 'Hello from AI with tools!' and read it back")
    
    try:
        # First request - write file
        response = await chat_with_tools(messages, tool_schemas)
        choice = response["choices"][0]
        msg = choice["message"]
        
        if "tool_calls" in msg and msg["tool_calls"]:
            print("\n🤖 AI is using tools:")
            messages.append(msg)
            
            for tool_call in msg["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                print(f"  📞 Calling: {func_name}")
                print(f"     Args: {func_args}")
                
                tool_result = await execute_tool(func_name, func_args)
                print(f"     Result: {tool_result.get('data', tool_result.get('error'))}")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result.get('data', tool_result.get('error')))
                })
            
            # Continue conversation - AI might want to read the file
            response2 = await chat_with_tools(messages, tool_schemas)
            msg2 = response2["choices"][0]["message"]
            
            if "tool_calls" in msg2 and msg2["tool_calls"]:
                print("\n🤖 AI is using more tools:")
                messages.append(msg2)
                
                for tool_call in msg2["tool_calls"]:
                    func_name = tool_call["function"]["name"]
                    func_args = json.loads(tool_call["function"]["arguments"])
                    
                    print(f"  📞 Calling: {func_name}")
                    print(f"     Args: {func_args}")
                    
                    tool_result = await execute_tool(func_name, func_args)
                    print(f"     Result: {tool_result.get('data', 'Error')[:100]}")
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tool_result.get('data', tool_result.get('error')))
                    })
                
                # Get final response
                final_response = await chat_with_tools(messages, tool_schemas)
                final_msg = final_response["choices"][0]["message"]["content"]
                print(f"\n🤖 AI Final Answer: {final_msg}")
            else:
                print(f"\n🤖 AI: {msg2.get('content', 'Task completed')}")
        else:
            print(f"🤖 AI: {msg.get('content', 'No response')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Data Processing
    print("\n" + "=" * 80)
    print("TEST 4: JSON Data Processing")
    print("-" * 80)
    
    messages = [
        {"role": "system", "content": "You are a data processing assistant. Use JSON tools to parse and query data."},
        {"role": "user", "content": 'Parse this JSON and tell me the name: {"name": "Tool System", "version": "2.0", "active": true}'}
    ]
    
    print('👤 User: Parse this JSON and tell me the name: {"name": "Tool System", "version": "2.0", "active": true}')
    
    try:
        response = await chat_with_tools(messages, tool_schemas)
        choice = response["choices"][0]
        msg = choice["message"]
        
        if "tool_calls" in msg and msg["tool_calls"]:
            print("\n🤖 AI is using tools:")
            messages.append(msg)
            
            for tool_call in msg["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                print(f"  📞 Calling: {func_name}")
                print(f"     Args: {json.dumps(func_args, indent=2)[:200]}")
                
                tool_result = await execute_tool(func_name, func_args)
                print(f"     Result: {tool_result['data']}")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result['data'])
                })
            
            final_response = await chat_with_tools(messages, tool_schemas)
            final_msg = final_response["choices"][0]["message"]["content"]
            print(f"\n🤖 AI Final Answer: {final_msg}")
        else:
            print(f"🤖 AI: {msg.get('content', 'No response')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Multi-Tool Task
    print("\n" + "=" * 80)
    print("TEST 5: Multi-Tool Task")
    print("-" * 80)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to multiple tools. Use them as needed."},
        {"role": "user", "content": "Calculate the average of these numbers: 15, 25, 35, 45, 55. Also tell me what processes are using the most CPU right now."}
    ]
    
    print("👤 User: Calculate average of 15,25,35,45,55 and show top CPU processes")
    
    try:
        response = await chat_with_tools(messages, tool_schemas)
        choice = response["choices"][0]
        msg = choice["message"]
        
        tool_count = 0
        while "tool_calls" in msg and msg["tool_calls"] and tool_count < 5:
            print(f"\n🤖 AI is using tools (round {tool_count + 1}):")
            messages.append(msg)
            
            for tool_call in msg["tool_calls"]:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                
                print(f"  📞 Calling: {func_name}")
                print(f"     Args: {func_args}")
                
                tool_result = await execute_tool(func_name, func_args)
                
                # Display result based on tool type
                if func_name == "statistics":
                    if tool_result['status'] == 'success':
                        print(f"     Mean: {tool_result['data'].get('mean', 'N/A')}")
                elif func_name == "process_list":
                    if tool_result['status'] == 'success':
                        processes = tool_result['data'][:3]
                        for p in processes:
                            print(f"     - {p['name']} (CPU: {p['cpu_percent']}%)")
                else:
                    print(f"     Result: {str(tool_result.get('data', 'Done'))[:100]}")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result.get('data', tool_result.get('error')))
                })
            
            # Get next response
            response = await chat_with_tools(messages, tool_schemas)
            msg = response["choices"][0]["message"]
            tool_count += 1
        
        # Final answer
        if "content" in msg:
            print(f"\n🤖 AI Final Answer: {msg['content']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("✅ ALL REAL-WORLD TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_scenarios())