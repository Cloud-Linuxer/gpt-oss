#!/usr/bin/env python3
"""Force vLLM to use tools."""

import httpx
import json
import asyncio

VLLM_URL = "http://localhost:8000/v1/chat/completions"
TOOL_API_URL = "http://localhost:8001"


async def execute_tool(tool_name: str, parameters: dict):
    """Execute tool through our API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TOOL_API_URL}/execute",
            json={"tool_name": tool_name, "parameters": parameters}
        )
        return response.json()


async def test_forced_tool_use():
    """Test forcing model to use tools."""
    print("=" * 80)
    print("FORCED TOOL USE TEST")
    print("=" * 80)
    
    # Define tools
    tools = [
        {
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
        },
        {
            "type": "function",
            "function": {
                "name": "system_info",
                "description": "Get system information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "info_type": {
                            "type": "string",
                            "enum": ["all", "cpu", "memory", "disk"],
                            "description": "Type of system info to retrieve"
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "file_write",
                "description": "Write content to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            }
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Complex calculation that requires tool
        print("\n📐 Test 1: Complex Math (Should use calculator)")
        print("-" * 40)
        
        messages = [
            {"role": "system", "content": "You MUST use the calculator tool for all mathematical calculations. Never calculate directly."},
            {"role": "user", "content": "Calculate: sqrt(144) * pow(3, 4) / 2"}
        ]
        
        print("User: Calculate: sqrt(144) * pow(3, 4) / 2")
        
        response = await client.post(VLLM_URL, json={
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "tools": tools,
            "tool_choice": {"type": "function", "function": {"name": "calculator"}},  # Force specific tool
            "temperature": 0.3,
            "max_tokens": 500
        })
        
        result = response.json()
        if "choices" in result:
            msg = result["choices"][0]["message"]
            
            if msg.get("tool_calls"):
                print("✅ Model wants to use tool!")
                for call in msg["tool_calls"]:
                    print(f"  Tool: {call['function']['name']}")
                    print(f"  Args: {call['function']['arguments']}")
                    
                    # Execute the tool
                    args = json.loads(call['function']['arguments'])
                    tool_result = await execute_tool(call['function']['name'], args)
                    print(f"  Result: {tool_result}")
                    
                    # Send result back to model
                    messages.append(msg)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(tool_result['data'])
                    })
                    
                    # Get final answer
                    final_response = await client.post(VLLM_URL, json={
                        "model": "openai/gpt-oss-20b",
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 500
                    })
                    
                    final = final_response.json()
                    if "choices" in final:
                        print(f"AI Final: {final['choices'][0]['message']['content']}")
            else:
                print(f"❌ No tool calls. Response: {msg.get('content', 'No response')}")
        
        # Test 2: System info request
        print("\n💻 Test 2: System Information (Should use system_info)")
        print("-" * 40)
        
        messages = [
            {"role": "system", "content": "You are a system assistant. You MUST use the system_info tool to get system information. Never guess or make up information."},
            {"role": "user", "content": "What is the current CPU usage and available memory?"}
        ]
        
        print("User: What is the current CPU usage and available memory?")
        
        response = await client.post(VLLM_URL, json={
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "tools": tools,
            "tool_choice": "required",  # Require tool use
            "temperature": 0.3,
            "max_tokens": 500
        })
        
        result = response.json()
        if "choices" in result:
            msg = result["choices"][0]["message"]
            
            if msg.get("tool_calls"):
                print("✅ Model wants to use tool!")
                for call in msg["tool_calls"]:
                    print(f"  Tool: {call['function']['name']}")
                    print(f"  Args: {call['function']['arguments']}")
                    
                    args = json.loads(call['function']['arguments'])
                    tool_result = await execute_tool(call['function']['name'], args)
                    
                    if tool_result['status'] == 'success' and 'cpu' in tool_result['data']:
                        cpu = tool_result['data']['cpu']
                        mem = tool_result['data']['memory']
                        print(f"  CPU Usage: {cpu['usage_percent']}%")
                        print(f"  Memory Available: {mem['available_gb']:.1f}GB / {mem['total_gb']:.1f}GB")
            else:
                print(f"❌ No tool calls. Response: {msg.get('content', 'No response')}")
        
        # Test 3: Multiple tools in sequence
        print("\n🔧 Test 3: Multiple Tools (Write file then calculate)")
        print("-" * 40)
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Use tools when needed. Always use the appropriate tool for each task."},
            {"role": "user", "content": "First, write 'Test data: 100' to /tmp/test.txt, then calculate 100 * 2.5"}
        ]
        
        print("User: Write 'Test data: 100' to /tmp/test.txt, then calculate 100 * 2.5")
        
        response = await client.post(VLLM_URL, json={
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.3,
            "max_tokens": 500
        })
        
        result = response.json()
        tool_calls_made = 0
        
        while "choices" in result and tool_calls_made < 3:
            msg = result["choices"][0]["message"]
            
            if msg.get("tool_calls"):
                tool_calls_made += 1
                print(f"✅ Tool call #{tool_calls_made}:")
                messages.append(msg)
                
                for call in msg["tool_calls"]:
                    print(f"  Tool: {call['function']['name']}")
                    args = json.loads(call['function']['arguments'])
                    print(f"  Args: {args}")
                    
                    tool_result = await execute_tool(call['function']['name'], args)
                    print(f"  Result: {tool_result.get('data', tool_result.get('error'))}")
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(tool_result.get('data', tool_result.get('error')))
                    })
                
                # Continue conversation
                response = await client.post(VLLM_URL, json={
                    "model": "openai/gpt-oss-20b",
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "temperature": 0.3,
                    "max_tokens": 500
                })
                result = response.json()
            else:
                print(f"Final response: {msg.get('content', 'Done')}")
                break
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_forced_tool_use())