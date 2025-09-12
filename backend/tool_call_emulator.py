#!/usr/bin/env python3
"""
Tool Call Emulator - Make gpt-oss-20b look like it has native tool calling.
Creates OpenAI-compatible responses by parsing model output and wrapping as tool_calls.
"""

import httpx
import json
import asyncio
import re
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

VLLM_URL = "http://localhost:8000/v1/chat/completions"
BACKEND_URL = "http://localhost:8001"

class ToolCallEmulator:
    """Emulates OpenAI tool calling format using text parsing."""
    
    def __init__(self):
        self.available_tools = {
            "get_weather": {
                "description": "도시의 현재 날씨를 조회한다",
                "parameters": ["location", "unit"],
                "required": ["location"]
            },
            "calculator": {
                "description": "수학 계산을 수행한다", 
                "parameters": ["expression"],
                "required": ["expression"]
            },
            "system_info": {
                "description": "시스템 정보를 조회한다",
                "parameters": ["info_type"],
                "required": []
            }
        }
    
    async def should_use_tool(self, messages: List[Dict], tools: List[Dict]) -> Tuple[bool, str, Dict]:
        """Determine if request should use tools by asking model to output JSON."""
        
        # Create tool routing prompt
        tool_descriptions = []
        for tool in tools:
            func = tool["function"]
            tool_descriptions.append(f"- {func['name']}: {func['description']}")
        
        tools_text = "\n".join(tool_descriptions)
        
        routing_prompt = f"""You are a tool router. Given the user's request, decide if any tool should be used.

Available tools:
{tools_text}

User request: {messages[-1]['content']}

If a tool should be used, output ONLY a JSON object like this:
{{"tool_name": "tool_name", "parameters": {{"param": "value"}}}}

If no tool is needed, output ONLY:
{{"tool_name": null}}

Output ONLY the JSON, no other text."""

        # Ask model to route
        route_request = {
            "model": "openai/gpt-oss-20b",
            "messages": [{"role": "user", "content": routing_prompt}],
            "temperature": 0,
            "max_tokens": 150
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(VLLM_URL, json=route_request)
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"].strip()
                    
                    # Try to parse JSON
                    try:
                        route_result = json.loads(content)
                        tool_name = route_result.get("tool_name")
                        parameters = route_result.get("parameters", {})
                        
                        if tool_name and tool_name != "null":
                            return True, tool_name, parameters
                        else:
                            return False, "", {}
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try to extract from text
                        return self._parse_tool_from_text(content, tools)
                
            except Exception as e:
                print(f"Tool routing error: {e}")
        
        return False, "", {}
    
    def _parse_tool_from_text(self, text: str, tools: List[Dict]) -> Tuple[bool, str, Dict]:
        """Fallback: parse tool intent from free text."""
        
        text_lower = text.lower()
        
        # Weather detection
        if any(word in text_lower for word in ["날씨", "기온", "weather", "temperature"]):
            if any(city in text_lower for city in ["서울", "seoul", "부산", "busan"]):
                location = "서울" if "서울" in text_lower else "부산"
                return True, "get_weather", {"location": location, "unit": "celsius"}
        
        # Calculator detection  
        if any(word in text_lower for word in ["계산", "곱하기", "더하기", "calculate", "*", "+", "-", "/"]):
            # Extract mathematical expression
            math_patterns = [
                r'(\d+\s*[+\-*/]\s*\d+)',
                r'(\d+\s*곱하기\s*\d+)',
                r'(\d+\s*×\s*\d+)',
            ]
            
            for pattern in math_patterns:
                match = re.search(pattern, text)
                if match:
                    expression = match.group(1)
                    # Convert Korean to math symbols
                    expression = expression.replace("곱하기", "*").replace("×", "*")
                    return True, "calculator", {"expression": expression}
        
        # System info detection
        if any(word in text_lower for word in ["시스템", "cpu", "메모리", "memory", "system"]):
            return True, "system_info", {"info_type": "all"}
        
        return False, "", {}
    
    async def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute tool via backend API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{BACKEND_URL}/execute",
                    json={"tool_name": tool_name, "parameters": parameters}
                )
                return response.json()
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Tool execution failed: {e}"
                }
    
    def create_openai_tool_response(self, tool_name: str, parameters: Dict, tool_result: Dict) -> Dict:
        """Create OpenAI-compatible tool_calls response."""
        
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex}",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": "openai/gpt-oss-20b",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": json.dumps(parameters, ensure_ascii=False)
                                }
                            }
                        ]
                    },
                    "finish_reason": "tool_calls"
                }
            ],
            "usage": {
                "prompt_tokens": 100,  # Estimated
                "total_tokens": 120,   # Estimated  
                "completion_tokens": 20
            }
        }
    
    async def chat_completions(self, request_data: Dict) -> Dict:
        """Main entry point - handles OpenAI chat completions with tool emulation."""
        
        messages = request_data.get("messages", [])
        tools = request_data.get("tools", [])
        tool_choice = request_data.get("tool_choice", "auto")
        
        # If no tools provided, pass through to vLLM normally
        if not tools:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(VLLM_URL, json=request_data)
                return response.json()
        
        # Check if we should use a tool
        should_use, tool_name, parameters = await self.should_use_tool(messages, tools)
        
        if should_use and tool_name:
            print(f"🔧 Emulating tool call: {tool_name} with {parameters}")
            
            # Execute the tool
            tool_result = await self.execute_tool(tool_name, parameters)
            
            if tool_result.get("status") == "success":
                # Return OpenAI-compatible tool_calls response
                return self.create_openai_tool_response(tool_name, parameters, tool_result)
            else:
                # Tool execution failed, fall back to regular response
                print(f"Tool execution failed: {tool_result.get('error')}")
        
        # No tool used - pass through to vLLM normally  
        request_data_copy = request_data.copy()
        request_data_copy.pop("tools", None)  # Remove tools to avoid vLLM errors
        request_data_copy.pop("tool_choice", None)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(VLLM_URL, json=request_data_copy)
            return response.json()


async def test_emulated_tool_calling():
    """Test the emulation approach."""
    
    print("🎭 Testing Emulated Tool Calling")
    print("=" * 70)
    
    emulator = ToolCallEmulator()
    
    # Test cases
    test_cases = [
        {
            "name": "Weather Query",
            "request": {
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that calls functions when needed."},
                    {"role": "user", "content": "서울의 현재 기온을 섭씨로 알려줘"}
                ],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "description": "도시의 현재 날씨를 조회한다",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "location": {"type": "string"},
                                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                                },
                                "required": ["location"]
                            }
                        }
                    }
                ],
                "tool_choice": "auto"
            }
        },
        {
            "name": "Calculator Query", 
            "request": {
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "25 곱하기 4 계산해줘"}
                ],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "description": "수학 계산을 수행한다",
                            "parameters": {
                                "type": "object", 
                                "properties": {
                                    "expression": {"type": "string"}
                                },
                                "required": ["expression"]
                            }
                        }
                    }
                ],
                "tool_choice": "auto"
            }
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print("-" * 50)
        
        try:
            response = await emulator.chat_completions(test_case["request"])
            print("✅ Response generated")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            
            # Check if it looks like OpenAI tool calling
            has_tool_calls = (
                "choices" in response and 
                len(response["choices"]) > 0 and
                "tool_calls" in response["choices"][0]["message"] and
                len(response["choices"][0]["message"]["tool_calls"]) > 0
            )
            
            results[test_case["name"]] = has_tool_calls
            print(f"Tool calls detected: {'✅ YES' if has_tool_calls else '❌ NO'}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            results[test_case["name"]] = False
    
    # Summary
    print(f"\n📊 EMULATION TEST RESULTS")
    print("=" * 50)
    success_count = sum(results.values())
    total_tests = len(results)
    
    for test_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"  
        print(f"{test_name:<20} {status}")
    
    print(f"\nSuccess Rate: {success_count}/{total_tests}")
    
    if success_count > 0:
        print("🎉 Emulation approach working!")
        print("→ Can provide OpenAI-compatible tool calling")
    else:
        print("🚨 Emulation also failed")
        print("→ Need to debug tool routing logic")


if __name__ == "__main__":
    asyncio.run(test_emulated_tool_calling())