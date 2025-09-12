#!/usr/bin/env python3
"""
Simple Tool Emulator - Direct approach without complex routing.
Parse user intent directly and create tool calls.
"""

import httpx
import json
import asyncio
import re
import uuid
from datetime import datetime

BACKEND_URL = "http://localhost:8001"

class SimpleToolEmulator:
    """Simple pattern-based tool call emulation."""
    
    def __init__(self):
        pass
    
    def detect_tool_intent(self, user_message: str) -> tuple:
        """Detect tool intent from user message using simple patterns."""
        
        text = user_message.lower()
        
        # Calculator patterns
        calc_patterns = [
            r'(\d+)\s*[×*곱하기]\s*(\d+)',  # "25 × 4", "25 * 4", "25 곱하기 4"
            r'계산[해줘]*.*?(\d+)\s*[×*]\s*(\d+)',  # "계산해줘 25 * 4"
            r'(\d+)\s*\+\s*(\d+)',  # Addition
            r'(\d+)\s*-\s*(\d+)',   # Subtraction  
            r'(\d+)\s*/\s*(\d+)',   # Division
        ]
        
        for pattern in calc_patterns:
            match = re.search(pattern, text)
            if match:
                if '곱하기' in text or '×' in text or '*' in text:
                    expr = f"{match.group(1)} * {match.group(2)}"
                elif '+' in text:
                    expr = f"{match.group(1)} + {match.group(2)}"
                elif '-' in text:
                    expr = f"{match.group(1)} - {match.group(2)}"
                elif '/' in text:
                    expr = f"{match.group(1)} / {match.group(2)}"
                else:
                    expr = f"{match.group(1)} * {match.group(2)}"  # Default to multiplication
                
                return "calculator", {"expression": expr}
        
        # Weather patterns
        if any(word in text for word in ['날씨', '기온', 'weather', 'temperature']):
            location = "서울"  # Default
            if '부산' in text:
                location = "부산"
            elif 'seoul' in text:
                location = "Seoul"
            elif 'busan' in text:
                location = "Busan"
            
            return "system_info", {"info_type": "all"}  # Use system_info as weather substitute
        
        # System info patterns  
        if any(word in text for word in ['시스템', 'cpu', '메모리', 'memory']):
            return "system_info", {"info_type": "all"}
        
        return None, {}
    
    async def execute_tool(self, tool_name: str, parameters: dict) -> dict:
        """Execute tool via backend API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{BACKEND_URL}/execute",
                    json={"tool_name": tool_name, "parameters": parameters}
                )
                result = response.json()
                print(f"🔧 Tool {tool_name} executed: {result.get('status')}")
                return result
            except Exception as e:
                print(f"❌ Tool execution error: {e}")
                return {
                    "status": "error", 
                    "error": f"Backend connection failed: {e}"
                }
    
    def create_tool_call_response(self, tool_name: str, parameters: dict, execution_result: dict = None) -> dict:
        """Create OpenAI-compatible tool_calls response."""
        
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        
        response = {
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
                "prompt_tokens": 50,
                "total_tokens": 70, 
                "completion_tokens": 20
            }
        }
        
        return response
    
    async def process_request(self, request_data: dict) -> dict:
        """Process chat completion request with tool emulation."""
        
        messages = request_data.get("messages", [])
        tools = request_data.get("tools", [])
        
        if not messages:
            return {"error": "No messages provided"}
        
        # Get last user message
        user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        if not user_message:
            return {"error": "No user message found"}
        
        print(f"📝 User message: {user_message}")
        
        # Detect tool intent
        tool_name, parameters = self.detect_tool_intent(user_message)
        
        if tool_name and tools:  # Only use tools if they're provided
            print(f"🎯 Tool detected: {tool_name} with parameters: {parameters}")
            
            # Check if detected tool is available in the tools list
            available_tool_names = [t["function"]["name"] for t in tools]
            if tool_name in available_tool_names:
                
                # Execute the tool  
                execution_result = await self.execute_tool(tool_name, parameters)
                
                if execution_result.get("status") == "success":
                    print("✅ Tool execution successful")
                    return self.create_tool_call_response(tool_name, parameters, execution_result)
                else:
                    print(f"❌ Tool execution failed: {execution_result.get('error')}")
            else:
                print(f"⚠️ Tool '{tool_name}' not available in provided tools")
        
        print("🔄 No tool detected or available, falling back to normal response")
        return {"message": "No tool call needed - would return normal chat response"}


async def test_simple_emulation():
    """Test the simple emulation approach."""
    
    print("🎭 SIMPLE TOOL EMULATION TEST")
    print("=" * 70)
    
    emulator = SimpleToolEmulator()
    
    test_cases = [
        {
            "name": "Calculator Test",
            "request": {
                "messages": [
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
                                }
                            }
                        }
                    }
                ]
            }
        },
        {
            "name": "System Info Test", 
            "request": {
                "messages": [
                    {"role": "user", "content": "현재 시스템 CPU 사용량 알려줘"}
                ],
                "tools": [
                    {
                        "type": "function", 
                        "function": {
                            "name": "system_info",
                            "description": "시스템 정보를 조회한다",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "info_type": {"type": "string"}
                                }
                            }
                        }
                    }
                ]
            }
        },
        {
            "name": "Pattern Detection Test",
            "request": {
                "messages": [
                    {"role": "user", "content": "100 × 25는 얼마야?"}
                ],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "calculator", 
                            "description": "계산기",
                            "parameters": {}
                        }
                    }
                ]
            }
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\n🧪 {test_case['name']}")
        print("-" * 50)
        
        try:
            response = await emulator.process_request(test_case["request"])
            print(f"📦 Response: {json.dumps(response, indent=2, ensure_ascii=False)}")
            
            # Check if response contains tool_calls
            has_tool_calls = (
                "choices" in response and
                len(response["choices"]) > 0 and
                "tool_calls" in response["choices"][0]["message"] and
                len(response["choices"][0]["message"]["tool_calls"]) > 0
            )
            
            results[test_case["name"]] = has_tool_calls
            print(f"Result: {'✅ TOOL CALL' if has_tool_calls else '❌ NO TOOL CALL'}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results[test_case["name"]] = False
    
    # Summary
    print("\n" + "=" * 70) 
    print("📊 SIMPLE EMULATION RESULTS")
    print("=" * 70)
    
    success_count = sum(results.values())
    total = len(results)
    
    for name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{name:<25} {status}")
    
    print(f"\nSuccess Rate: {success_count}/{total}")
    
    if success_count > 0:
        print("🎉 Simple emulation works!")
        print("→ Ready to implement full proxy server")
    else:
        print("🔧 Need to debug pattern detection")


if __name__ == "__main__":
    asyncio.run(test_simple_emulation())