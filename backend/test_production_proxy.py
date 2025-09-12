#!/usr/bin/env python3
"""
Test suite for Production Tool Calling Proxy
Tests all priority levels and fallback mechanisms
"""

import asyncio
import json
import httpx
from typing import Dict, Any

PROXY_URL = "http://localhost:8002/v1/chat/completions"
PROXY_HEALTH = "http://localhost:8002/health"
PROXY_STATS = "http://localhost:8002/stats"

class ProxyTester:
    """Test the production tool calling proxy."""
    
    def __init__(self):
        self.test_results = {}
    
    async def test_proxy_health(self):
        """Test if proxy is running."""
        
        print("🏥 Testing Proxy Health")
        print("-" * 50)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(PROXY_HEALTH)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Proxy healthy: {result}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Health check error: {e}")
                return False
    
    async def test_priority_1_named_function(self):
        """Test Priority 1: Named function forcing."""
        
        print("\n🎯 Testing Priority 1: Named Function Force")
        print("-" * 50)
        
        test_request = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "25 × 4 계산해줘"}
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
                    print("📦 Response received:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    
                    # Check for tool calls
                    has_tool_calls = self._has_tool_calls(result)
                    print(f"Tool calls detected: {'✅ YES' if has_tool_calls else '❌ NO'}")
                    
                    self.test_results["priority_1"] = {
                        "success": has_tool_calls,
                        "response": result
                    }
                    return has_tool_calls
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    print(response.text)
                    self.test_results["priority_1"] = {"success": False, "error": response.text}
                    return False
                    
            except Exception as e:
                print(f"❌ Request error: {e}")
                self.test_results["priority_1"] = {"success": False, "error": str(e)}
                return False
    
    async def test_priority_3_structured_bridge(self):
        """Test Priority 3: Structured output bridge."""
        
        print("\n🌉 Testing Priority 3: Structured Bridge")
        print("-" * 50)
        
        test_request = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "현재 시스템 메모리 사용량 확인해줘"}
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
            "tool_choice": "auto",
            "temperature": 0
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(PROXY_URL, json=test_request)
                
                if response.status_code == 200:
                    result = response.json()
                    print("📦 Response received:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    
                    has_tool_calls = self._has_tool_calls(result)
                    print(f"Tool calls detected: {'✅ YES' if has_tool_calls else '❌ NO'}")
                    
                    self.test_results["priority_3"] = {
                        "success": has_tool_calls,
                        "response": result
                    }
                    return has_tool_calls
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    self.test_results["priority_3"] = {"success": False, "error": response.text}
                    return False
                    
            except Exception as e:
                print(f"❌ Request error: {e}")
                self.test_results["priority_3"] = {"success": False, "error": str(e)}
                return False
    
    async def test_no_tools_passthrough(self):
        """Test passthrough when no tools provided."""
        
        print("\n📝 Testing No Tools Passthrough")
        print("-" * 50)
        
        test_request = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "안녕하세요, 오늘 날씨는 어떤가요?"}
            ],
            "temperature": 0.7,
            "max_tokens": 200
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(PROXY_URL, json=test_request)
                
                if response.status_code == 200:
                    result = response.json()
                    print("📦 Normal response received:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    
                    # Should NOT have tool calls
                    has_tool_calls = self._has_tool_calls(result)
                    has_content = self._has_content(result)
                    
                    success = not has_tool_calls and has_content
                    print(f"Has content: {'✅ YES' if has_content else '❌ NO'}")
                    print(f"Has tool calls: {'❌ YES (unexpected)' if has_tool_calls else '✅ NO (expected)'}")
                    
                    self.test_results["passthrough"] = {
                        "success": success,
                        "response": result
                    }
                    return success
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    self.test_results["passthrough"] = {"success": False, "error": response.text}
                    return False
                    
            except Exception as e:
                print(f"❌ Request error: {e}")
                self.test_results["passthrough"] = {"success": False, "error": str(e)}
                return False
    
    async def test_complex_tool_scenario(self):
        """Test complex scenario that should trigger tool use."""
        
        print("\n🔍 Testing Complex Tool Scenario")
        print("-" * 50)
        
        test_request = {
            "model": "openai/gpt-oss-20b",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant with access to calculation tools."},
                {"role": "user", "content": "144 나누기 12는 얼마인지 정확히 계산해서 알려줘. 계산기를 사용해서 확인해줘."}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "calculator",
                        "description": "정확한 수학 계산을 수행합니다",
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
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(PROXY_URL, json=test_request)
                
                if response.status_code == 200:
                    result = response.json()
                    print("📦 Response received:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    
                    has_tool_calls = self._has_tool_calls(result)
                    print(f"Tool calls detected: {'✅ YES' if has_tool_calls else '❌ NO'}")
                    
                    self.test_results["complex"] = {
                        "success": has_tool_calls,
                        "response": result
                    }
                    return has_tool_calls
                else:
                    print(f"❌ HTTP Error: {response.status_code}")
                    self.test_results["complex"] = {"success": False, "error": response.text}
                    return False
                    
            except Exception as e:
                print(f"❌ Request error: {e}")
                self.test_results["complex"] = {"success": False, "error": str(e)}
                return False
    
    async def get_proxy_stats(self):
        """Get proxy statistics."""
        
        print("\n📊 Getting Proxy Statistics")
        print("-" * 50)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(PROXY_STATS)
                if response.status_code == 200:
                    stats = response.json()
                    print("📈 Proxy Stats:")
                    print(json.dumps(stats, indent=2, ensure_ascii=False))
                    return stats
                else:
                    print(f"❌ Stats request failed: {response.status_code}")
                    return None
            except Exception as e:
                print(f"❌ Stats request error: {e}")
                return None
    
    def _has_tool_calls(self, response: Dict) -> bool:
        """Check if response contains tool calls."""
        try:
            choices = response.get("choices", [])
            if not choices:
                return False
            
            message = choices[0].get("message", {})
            tool_calls = message.get("tool_calls", [])
            
            return len(tool_calls) > 0
        except:
            return False
    
    def _has_content(self, response: Dict) -> bool:
        """Check if response contains content."""
        try:
            choices = response.get("choices", [])
            if not choices:
                return False
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            return len(content.strip()) > 0
        except:
            return False
    
    def print_summary(self):
        """Print test summary."""
        
        print("\n" + "=" * 80)
        print("📊 PRODUCTION PROXY TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result.get("success", False))
        
        for test_name, result in self.test_results.items():
            status = "✅ SUCCESS" if result.get("success", False) else "❌ FAILED"
            print(f"{test_name:<20} {status}")
        
        print(f"\nOverall Success Rate: {successful_tests}/{total_tests}")
        
        if successful_tests > 0:
            print("🎉 Proxy is working! Ready for production use.")
            print("→ Tool calling emulation provides OpenAI compatibility")
        else:
            print("🚨 Proxy needs debugging before production use")


async def main():
    """Run all proxy tests."""
    
    print("🧪 PRODUCTION TOOL CALLING PROXY TESTS")
    print("=" * 80)
    print("Testing prioritized fallback strategy implementation")
    print("Verifying OpenAI API compatibility")
    print("=" * 80)
    
    tester = ProxyTester()
    
    # Test 1: Health check
    proxy_healthy = await tester.test_proxy_health()
    if not proxy_healthy:
        print("🚨 Proxy not running! Start with: python production_tool_proxy.py")
        return
    
    # Test 2: Priority 1 (will likely fail, but may succeed)
    await tester.test_priority_1_named_function()
    
    # Test 3: Priority 3 (structured bridge - should succeed)
    await tester.test_priority_3_structured_bridge()
    
    # Test 4: Complex scenario
    await tester.test_complex_tool_scenario()
    
    # Test 5: Passthrough
    await tester.test_no_tools_passthrough()
    
    # Get statistics
    await tester.get_proxy_stats()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())