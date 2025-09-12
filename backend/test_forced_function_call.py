#!/usr/bin/env python3
"""Test forced function call with specific function name."""

import httpx
import json
import asyncio

VLLM_URL = "http://localhost:8000/v1/chat/completions"

async def test_forced_function_call():
    """Test (A) forced tool choice with specific function name."""
    
    print("🎯 Testing Strategy A: Forced Function Call")
    print("=" * 60)
    
    # Define calculator tool
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
    
    # Test request with forced function call
    request_data = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "정확성을 위해 가능하면 항상 도구를 우선 사용한다."},
            {"role": "user", "content": "계산해줘: 25 * 4 + 10"}
        ],
        "tools": tools,
        "tool_choice": {
            "type": "function",
            "function": {"name": "calculator"}
        },
        "parallel_tool_calls": False,
        "temperature": 0
    }
    
    print("📡 Request:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    print("\n🔄 Sending...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(VLLM_URL, json=request_data)
            print(f"\n📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("📦 Response:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0]["message"]
                    
                    if "tool_calls" in message and len(message["tool_calls"]) > 0:
                        print("\n✅ SUCCESS: Tool calls detected!")
                        for call in message["tool_calls"]:
                            print(f"  🔧 Tool: {call['function']['name']}")
                            print(f"  📝 Args: {call['function']['arguments']}")
                        return True
                    else:
                        print(f"\n❌ FAILED: No tool calls")
                        print(f"Content: {message.get('content', 'No content')}")
                        return False
                else:
                    print("❌ FAILED: No choices in response")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False


async def test_complex_weather_task():
    """Test (B) complex task that requires tools."""
    
    print("\n🌤️  Testing Strategy B: Complex Weather Task")
    print("=" * 60)
    
    # Define weather tool
    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "도시 현재 날씨 조회",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        }
    }]
    
    request_data = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "직접 계산하지 말고, 제공된 도구를 우선 사용한다."},
            {"role": "user", "content": "서울·부산·뉴욕의 현재 기온과 체감온도를 섭씨로 조회해 평균/최댓값을 함께 요약해줘. 각 도시는 반드시 get_weather 함수로 조회해."}
        ],
        "tools": tools,
        "tool_choice": "auto",
        "parallel_tool_calls": True,
        "temperature": 0
    }
    
    print("📡 Request:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    print("\n🔄 Sending...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(VLLM_URL, json=request_data)
            print(f"\n📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("📦 Response:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0]["message"]
                    
                    if "tool_calls" in message and len(message["tool_calls"]) > 0:
                        print(f"\n✅ SUCCESS: {len(message['tool_calls'])} tool calls detected!")
                        for i, call in enumerate(message["tool_calls"]):
                            print(f"  🔧 Tool #{i+1}: {call['function']['name']}")
                            print(f"  📝 Args: {call['function']['arguments']}")
                        return True
                    else:
                        print(f"\n❌ FAILED: No tool calls")
                        print(f"Content: {message.get('content', 'No content')}")
                        return False
                else:
                    print("❌ FAILED: No choices in response")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False


async def test_system_info_forced():
    """Test forced system info call."""
    
    print("\n💻 Testing Strategy C: Forced System Info")
    print("=" * 60)
    
    tools = [{
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
    }]
    
    request_data = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "시스템 정보 조회는 반드시 도구를 사용한다."},
            {"role": "user", "content": "현재 시스템의 CPU와 메모리 사용량을 알려줘"}
        ],
        "tools": tools,
        "tool_choice": {
            "type": "function",
            "function": {"name": "system_info"}
        },
        "temperature": 0
    }
    
    print("📡 Request:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    print("\n🔄 Sending...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(VLLM_URL, json=request_data)
            print(f"\n📥 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("📦 Response:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0]["message"]
                    
                    if "tool_calls" in message and len(message["tool_calls"]) > 0:
                        print(f"\n✅ SUCCESS: Tool calls detected!")
                        for call in message["tool_calls"]:
                            print(f"  🔧 Tool: {call['function']['name']}")
                            print(f"  📝 Args: {call['function']['arguments']}")
                        return True
                    else:
                        print(f"\n❌ FAILED: No tool calls")
                        print(f"Content: {message.get('content', 'No content')}")
                        return False
                else:
                    print("❌ FAILED: No choices in response")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False


async def main():
    """Run all tests."""
    print("🧪 vLLM Tool Calling Diagnosis")
    print("=" * 80)
    print("Key insight: gpt-oss model auto-enables tool use per logs")
    print("Testing forced function calls vs. complexity induction")
    print("=" * 80)
    
    results = {}
    
    # Test A: Forced function call
    results["forced_calculator"] = await test_forced_function_call()
    
    # Test B: Complex weather task
    results["complex_weather"] = await test_complex_weather_task()
    
    # Test C: Forced system info
    results["forced_system_info"] = await test_system_info_forced()
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    for test_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{test_name:<20} {status}")
    
    total_success = sum(results.values())
    print(f"\nOverall: {total_success}/3 tests passed")
    
    if total_success > 0:
        print("🎉 Tool calling IS working with the right approach!")
    else:
        print("🚨 Tool calling still not working - may need server restart with parser")


if __name__ == "__main__":
    asyncio.run(main())