#!/usr/bin/env python3
"""Test vLLM integration with tool system."""

import asyncio
import json
import sys
sys.path.insert(0, '/home/gpt-oss/backend')

from vllm_client import VLLMClient
from tools import (
    ToolRegistry,
    FileListTool, SystemInfoTool, CalculatorTool,
    JSONParseTool, StatisticsTool
)


async def test_vllm_with_tools():
    """Test vLLM with tool system."""
    print("=" * 80)
    print("vLLM + TOOL SYSTEM INTEGRATION TEST")
    print("=" * 80)
    
    # Initialize vLLM client
    print("\n🔌 Connecting to vLLM...")
    client = VLLMClient(
        base_url="http://localhost:8000",
        model="openai/gpt-oss-20b",
        max_tokens=1000,
        temperature=0.7,
        timeout=60
    )
    
    # Initialize tool registry
    print("📋 Setting up tools...")
    registry = ToolRegistry()
    registry.register(FileListTool(), category="file")
    registry.register(SystemInfoTool(), category="system")
    registry.register(CalculatorTool(), category="math")
    registry.register(JSONParseTool(), category="data")
    registry.register(StatisticsTool(), category="math")
    
    # Get tool schemas for vLLM
    tool_schemas = registry.get_schemas()
    print(f"✅ Registered {len(tool_schemas)} tools")
    
    # Test 1: Simple calculation with tool
    print("\n" + "=" * 80)
    print("TEST 1: Math Calculation Request")
    print("-" * 80)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to tools."},
        {"role": "user", "content": "Calculate the result of: 15 * 23 + sqrt(144)"}
    ]
    
    print("User: Calculate the result of: 15 * 23 + sqrt(144)")
    
    try:
        # Call vLLM with tools
        response = await client.chat(messages, tools=tool_schemas)
        msg = response["choices"][0]["message"]
        
        # Check if model wants to use tools
        if "tool_calls" in msg and msg["tool_calls"]:
            print(f"\n🔧 Model wants to use tools:")
            messages.append(msg)
            
            for call in msg["tool_calls"]:
                name = call["function"]["name"]
                args = json.loads(call["function"].get("arguments", "{}"))
                print(f"  - Tool: {name}")
                print(f"    Args: {args}")
                
                # Execute tool
                result = await registry.execute_tool(name, **args)
                tool_response = result.to_string()
                print(f"    Result: {tool_response}")
                
                # Add tool response to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", "unknown"),
                    "name": name,
                    "content": tool_response
                })
            
            # Get final response
            followup = await client.chat(messages, tools=tool_schemas)
            final_response = followup["choices"][0]["message"]["content"]
            print(f"\n📝 Assistant: {final_response}")
        else:
            print(f"📝 Assistant: {msg.get('content', 'No response')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: System information request
    print("\n" + "=" * 80)
    print("TEST 2: System Information Request")
    print("-" * 80)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to tools."},
        {"role": "user", "content": "What is the current CPU and memory usage of this system?"}
    ]
    
    print("User: What is the current CPU and memory usage of this system?")
    
    try:
        response = await client.chat(messages, tools=tool_schemas)
        msg = response["choices"][0]["message"]
        
        if "tool_calls" in msg and msg["tool_calls"]:
            print(f"\n🔧 Model wants to use tools:")
            messages.append(msg)
            
            for call in msg["tool_calls"]:
                name = call["function"]["name"]
                args = json.loads(call["function"].get("arguments", "{}"))
                print(f"  - Tool: {name}")
                print(f"    Args: {args}")
                
                result = await registry.execute_tool(name, **args)
                tool_response = result.to_string()
                
                # Show abbreviated response for readability
                if len(tool_response) > 200:
                    print(f"    Result: {tool_response[:200]}...")
                else:
                    print(f"    Result: {tool_response}")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", "unknown"),
                    "name": name,
                    "content": tool_response
                })
            
            followup = await client.chat(messages, tools=tool_schemas)
            final_response = followup["choices"][0]["message"]["content"]
            print(f"\n📝 Assistant: {final_response}")
        else:
            print(f"📝 Assistant: {msg.get('content', 'No response')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: File listing request
    print("\n" + "=" * 80)
    print("TEST 3: File Listing Request")
    print("-" * 80)
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant with access to tools."},
        {"role": "user", "content": "List all Python files in /home/gpt-oss/backend directory"}
    ]
    
    print("User: List all Python files in /home/gpt-oss/backend directory")
    
    try:
        response = await client.chat(messages, tools=tool_schemas)
        msg = response["choices"][0]["message"]
        
        if "tool_calls" in msg and msg["tool_calls"]:
            print(f"\n🔧 Model wants to use tools:")
            messages.append(msg)
            
            for call in msg["tool_calls"]:
                name = call["function"]["name"]
                args = json.loads(call["function"].get("arguments", "{}"))
                print(f"  - Tool: {name}")
                print(f"    Args: {args}")
                
                result = await registry.execute_tool(name, **args)
                tool_response = result.to_string()
                
                # Parse and show file list nicely
                if result.status.value == "success" and name == "file_list":
                    files = result.data
                    print(f"    Found {len(files)} files:")
                    for f in files[:5]:
                        print(f"      • {f['name']} ({f['size']} bytes)")
                    if len(files) > 5:
                        print(f"      ... and {len(files)-5} more")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", "unknown"),
                    "name": name,
                    "content": tool_response
                })
            
            followup = await client.chat(messages, tools=tool_schemas)
            final_response = followup["choices"][0]["message"]["content"]
            print(f"\n📝 Assistant: {final_response}")
        else:
            print(f"📝 Assistant: {msg.get('content', 'No response')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Close client
    await client.close()
    
    # Print final statistics
    print("\n" + "=" * 80)
    print("TOOL USAGE SUMMARY")
    print("-" * 80)
    stats = registry.get_stats()
    print(f"Total tools available: {stats['total_tools']}")
    print("Tools used in this session:")
    for tool_stat in stats['tools']:
        if tool_stat['usage_count'] > 0:
            print(f"  - {tool_stat['name']}: {tool_stat['usage_count']} calls")
    
    print("\n" + "=" * 80)
    print("✅ INTEGRATION TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_vllm_with_tools())