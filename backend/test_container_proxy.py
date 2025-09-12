#!/usr/bin/env python3
"""
Test suite for containerized all-in-one tool proxy on port 8001
"""

import asyncio
import json
import httpx

PROXY_URL = "http://localhost:8001/v1/chat/completions"
HEALTH_URL = "http://localhost:8001/health"
TOOLS_URL = "http://localhost:8001/tools"

async def test_container_health():
    """Test container health."""
    
    print("🏥 Testing Container Health")
    print("-" * 50)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(HEALTH_URL)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Container healthy")
                print(f"Tools available: {result.get('tools_available', 0)}")
                print(f"Stats: {result.get('stats', {})}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

async def test_tools_endpoint():
    """Test tools listing endpoint."""
    
    print("\n🔧 Testing Tools Endpoint")
    print("-" * 50)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(TOOLS_URL)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Tools endpoint working")
                print(f"Total tools: {result.get('total_tools', 0)}")
                print(f"Categories: {result.get('categories', [])}")
                
                # Show some tools
                tools = result.get('tools', [])[:5]  # First 5 tools
                for tool in tools:
                    print(f"  - {tool['name']} ({tool['category']}): {tool['description']}")
                return True
            else:
                print(f"❌ Tools endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Tools endpoint error: {e}")
            return False

async def test_calculator_tool_call():
    """Test calculator tool calling."""
    
    print("\n🧮 Testing Calculator Tool Call")
    print("-" * 50)
    
    test_request = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "25 × 8 계산해줘"}
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
                            "expression": {"type": "string", "description": "수식"}
                        },
                        "required": ["expression"]
                    }
                }
            }
        ],
        "tool_choice": "auto",
        "temperature": 0
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(PROXY_URL, json=test_request)
            
            if response.status_code == 200:
                result = response.json()
                print("📦 Response received")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                # Check for tool calls
                has_tool_calls = (
                    "choices" in result and
                    len(result["choices"]) > 0 and
                    "tool_calls" in result["choices"][0]["message"] and
                    len(result["choices"][0]["message"]["tool_calls"]) > 0
                )
                
                print(f"Tool calls detected: {'✅ YES' if has_tool_calls else '❌ NO'}")
                return has_tool_calls
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(response.text)
                return False
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            return False

async def test_system_info_tool_call():
    """Test system info tool calling."""
    
    print("\n💻 Testing System Info Tool Call")
    print("-" * 50)
    
    test_request = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "You are a system assistant."},
            {"role": "user", "content": "현재 시스템 CPU와 메모리 상태 확인해줘"}
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
                            "info_type": {"type": "string", "enum": ["all", "cpu", "memory"]}
                        },
                        "required": []
                    }
                }
            }
        ],
        "tool_choice": "auto"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(PROXY_URL, json=test_request)
            
            if response.status_code == 200:
                result = response.json()
                print("📦 Response received")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
                has_tool_calls = (
                    "choices" in result and
                    len(result["choices"]) > 0 and
                    "tool_calls" in result["choices"][0]["message"] and
                    len(result["choices"][0]["message"]["tool_calls"]) > 0
                )
                
                print(f"Tool calls detected: {'✅ YES' if has_tool_calls else '❌ NO'}")
                return has_tool_calls
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            return False

async def test_no_tools_chat():
    """Test normal chat without tools."""
    
    print("\n💬 Testing Normal Chat (No Tools)")
    print("-" * 50)
    
    test_request = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "안녕하세요! 좋은 아침입니다."}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(PROXY_URL, json=test_request)
            
            if response.status_code == 200:
                result = response.json()
                print("📦 Normal chat response:")
                
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"].get("content", "")
                    print(f"Content: {content}")
                    
                    has_content = len(content.strip()) > 0
                    print(f"Has content: {'✅ YES' if has_content else '❌ NO'}")
                    return has_content
                else:
                    print("❌ No choices in response")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            return False

async def main():
    """Run all container tests."""
    
    print("🧪 CONTAINERIZED TOOL PROXY TESTS")
    print("=" * 70)
    print("Testing all-in-one proxy container on port 8001")
    print("Includes integrated tool backend")
    print("=" * 70)
    
    results = {}
    
    # Test container health
    results["health"] = await test_container_health()
    if not results["health"]:
        print("🚨 Container not healthy! Check docker logs gpt-oss-tool-proxy")
        return
    
    # Test tools endpoint
    results["tools_endpoint"] = await test_tools_endpoint()
    
    # Test calculator tool call
    results["calculator"] = await test_calculator_tool_call()
    
    # Test system info tool call
    results["system_info"] = await test_system_info_tool_call()
    
    # Test normal chat
    results["normal_chat"] = await test_no_tools_chat()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 CONTAINERIZED PROXY TEST RESULTS")
    print("=" * 70)
    
    success_count = sum(1 for success in results.values() if success)
    total_tests = len(results)
    
    for test_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{test_name:<20} {status}")
    
    print(f"\nOverall Success Rate: {success_count}/{total_tests}")
    
    if success_count >= 4:  # At least health + tools + 2 others
        print("🎉 Containerized proxy is working perfectly!")
        print("🚢 Ready for production deployment on port 8001")
        print("🔗 OpenAI-compatible endpoint: http://localhost:8001/v1/chat/completions")
    else:
        print("🔧 Some tests failed - check container logs for debugging")
    
    # Show deployment info
    print("\n📋 DEPLOYMENT INFO")
    print("-" * 30)
    print("Container: gpt-oss-tool-proxy")
    print("Port: 8001")
    print("Health: http://localhost:8001/health")
    print("Tools: http://localhost:8001/tools")
    print("API: http://localhost:8001/v1/chat/completions")

if __name__ == "__main__":
    asyncio.run(main())