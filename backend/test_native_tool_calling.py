#!/usr/bin/env python3
"""Native tool calling test - OpenAI format exactly as examples."""

import httpx
import json
import asyncio
from typing import Dict, Any

VLLM_URL = "http://localhost:8000/v1/chat/completions"

async def test_native_openai_format():
    """Test 1) Native approach - exactly as OpenAI examples."""
    
    print("🔬 Testing Native Tool Calling (OpenAI Format)")
    print("=" * 70)
    
    # Exact format from OpenAI docs
    request_data = {
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
                            "location": {"type": "string", "description": "도시명, 예: 서울"},
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                        },
                        "required": ["location"]
                    }
                }
            }
        ],
        "tool_choice": "auto",
        "temperature": 0
    }
    
    print("📤 Request:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(VLLM_URL, json=request_data)
            print(f"\n📥 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("📦 Response:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # Check for tool calls
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0]["message"]
                    
                    if "tool_calls" in message and len(message["tool_calls"]) > 0:
                        print("\n✅ SUCCESS: Native tool calling works!")
                        for call in message["tool_calls"]:
                            print(f"  🔧 Tool: {call['function']['name']}")
                            print(f"  📝 Args: {call['function']['arguments']}")
                        return True, result
                    else:
                        print(f"\n❌ No tool calls detected")
                        print(f"Content: {message.get('content', 'No content')}")
                        if "reasoning_content" in message:
                            print(f"Reasoning: {message['reasoning_content']}")
                        return False, result
                else:
                    print("❌ No choices in response")
                    return False, result
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False, {"error": response.text}
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False, {"error": str(e)}


async def test_simple_calculator():
    """Test simple calculator call."""
    
    print("\n🧮 Testing Calculator Tool")
    print("=" * 70)
    
    request_data = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that calls functions when needed."},
            {"role": "user", "content": "25 곱하기 4는 얼마야? 계산해줘."}
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
                            "expression": {"type": "string", "description": "계산할 수식"}
                        },
                        "required": ["expression"]
                    }
                }
            }
        ],
        "tool_choice": "auto",
        "temperature": 0
    }
    
    print("📤 Request:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(VLLM_URL, json=request_data)
            print(f"\n📥 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("📦 Response:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0]["message"]
                    
                    if "tool_calls" in message and len(message["tool_calls"]) > 0:
                        print("\n✅ Calculator tool call detected!")
                        return True, result
                    else:
                        print(f"\n❌ No tool calls")
                        print(f"Direct answer: {message.get('content', 'No content')}")
                        return False, result
                        
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False, {"error": str(e)}
    
    return False, {}


async def test_no_tools_baseline():
    """Test same request without tools to compare."""
    
    print("\n📝 Baseline Test (No Tools)")
    print("=" * 70)
    
    request_data = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "서울의 현재 기온을 섭씨로 알려줘"}
        ],
        "temperature": 0
    }
    
    print("📤 Request (No Tools):")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(VLLM_URL, json=request_data)
            print(f"\n📥 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("📦 Response:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return True, result
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return False, {"error": str(e)}
    
    return False, {}


async def main():
    """Run all native tool calling tests."""
    
    print("🧪 NATIVE TOOL CALLING TESTS")
    print("=" * 80)
    print("Testing gpt-oss-20b native tool calling capability")
    print("Following exact OpenAI format from documentation")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Weather function call
    print("Test 1: Weather Function Call")
    results["weather"] = await test_native_openai_format()
    
    # Test 2: Calculator function call  
    print("\nTest 2: Calculator Function Call")
    results["calculator"] = await test_simple_calculator()
    
    # Test 3: Baseline without tools
    print("\nTest 3: Baseline Without Tools")
    results["baseline"] = await test_no_tools_baseline()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 NATIVE TOOL CALLING TEST RESULTS")
    print("=" * 80)
    
    success_count = 0
    for test_name, (success, response) in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{test_name:<15} {status}")
        if success:
            success_count += 1
    
    print(f"\nOverall Success Rate: {success_count}/3")
    
    if success_count > 0:
        print("🎉 Native tool calling is partially working!")
        print("→ Can proceed with native implementation")
    else:
        print("🚨 Native tool calling completely failed")  
        print("→ Must implement emulation approach")
    
    # Save results
    with open("native_tool_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": "2025-09-12T23:15:00Z",
            "model": "openai/gpt-oss-20b", 
            "vllm_version": "v0.10.1.1",
            "success_rate": f"{success_count}/3",
            "results": {name: {"success": success, "response": response} 
                       for name, (success, response) in results.items()}
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: native_tool_test_results.json")
    
    return success_count > 0


if __name__ == "__main__":
    asyncio.run(main())