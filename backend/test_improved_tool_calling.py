#!/usr/bin/env python3
"""
Improved tool calling strategies based on analysis.
Implements better prompting, complexity induction, and fallback mechanisms.
"""

import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional

VLLM_URL = "http://localhost:8000/v1/chat/completions"
TOOL_API_URL = "http://localhost:8001"


class ToolCallStrategy:
    """Base class for tool calling strategies."""
    
    def __init__(self, name: str):
        self.name = name
        self.success_count = 0
        self.total_attempts = 0
    
    def get_success_rate(self) -> float:
        return self.success_count / max(1, self.total_attempts)
    
    async def test_strategy(self, client: httpx.AsyncClient, tools: List[Dict]) -> Dict[str, Any]:
        """Test this strategy and return results."""
        raise NotImplementedError


class GentleGuidanceStrategy(ToolCallStrategy):
    """Strategy 1: Gentle guidance instead of forcing."""
    
    def __init__(self):
        super().__init__("Gentle Guidance")
    
    async def test_strategy(self, client: httpx.AsyncClient, tools: List[Dict]) -> Dict[str, Any]:
        self.total_attempts += 1
        
        # Softer system prompt
        system_prompt = (
            "You are a helpful assistant with access to tools. "
            "When tools are available for a task, prefer using them over direct calculation. "
            "Tools provide more accurate and reliable results."
        )
        
        # Complex query to induce tool use
        user_query = "Calculate the square root of 144, multiply by 3 to the power of 4, then divide by 2. Also tell me the current CPU usage."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        response = await client.post(VLLM_URL, json={
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.3,
            "max_tokens": 800
        })
        
        result = response.json()
        tool_used = False
        
        if "choices" in result:
            msg = result["choices"][0]["message"]
            if msg.get("tool_calls"):
                tool_used = True
                self.success_count += 1
        
        return {
            "strategy": self.name,
            "tool_used": tool_used,
            "response": result,
            "success_rate": self.get_success_rate()
        }


class ComplexityInductionStrategy(ToolCallStrategy):
    """Strategy 2: Artificially complex queries to force tool use."""
    
    def __init__(self):
        super().__init__("Complexity Induction")
    
    async def test_strategy(self, client: httpx.AsyncClient, tools: List[Dict]) -> Dict[str, Any]:
        self.total_attempts += 1
        
        system_prompt = (
            "You are a professional assistant. Use available tools when they can provide "
            "more accurate results than manual calculation."
        )
        
        # Very complex query that's hard to calculate manually
        user_query = (
            "I need you to compare the weather in Seoul, Busan, and New York. "
            "For each city, calculate the average temperature if it's currently 15°C in Seoul, "
            "18°C in Busan, and 42°F in New York. Convert everything to Celsius and Fahrenheit, "
            "then calculate the standard deviation of these temperatures. "
            "This comparison must use the get_weather function to ensure accuracy."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        response = await client.post(VLLM_URL, json={
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.3,
            "max_tokens": 1000
        })
        
        result = response.json()
        tool_used = False
        
        if "choices" in result:
            msg = result["choices"][0]["message"]
            if msg.get("tool_calls"):
                tool_used = True
                self.success_count += 1
        
        return {
            "strategy": self.name,
            "tool_used": tool_used,
            "response": result,
            "success_rate": self.get_success_rate()
        }


class ExplicitRequirementStrategy(ToolCallStrategy):
    """Strategy 3: Explicit requirement in user message."""
    
    def __init__(self):
        super().__init__("Explicit Requirement")
    
    async def test_strategy(self, client: httpx.AsyncClient, tools: List[Dict]) -> Dict[str, Any]:
        self.total_attempts += 1
        
        system_prompt = (
            "You are a helpful assistant with access to various tools. "
            "Follow user instructions carefully."
        )
        
        # User explicitly requires tool use
        user_query = (
            "Calculate 25 * 4 + sqrt(81) - 7^2. "
            "IMPORTANT: This request must be performed using the calculator tool to ensure accuracy. "
            "Do not calculate this manually."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        response = await client.post(VLLM_URL, json={
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.3,
            "max_tokens": 600
        })
        
        result = response.json()
        tool_used = False
        
        if "choices" in result:
            msg = result["choices"][0]["message"]
            if msg.get("tool_calls"):
                tool_used = True
                self.success_count += 1
        
        return {
            "strategy": self.name,
            "tool_used": tool_used,
            "response": result,
            "success_rate": self.get_success_rate()
        }


class FallbackRetryStrategy(ToolCallStrategy):
    """Strategy 4: Retry with hints if no tool use detected."""
    
    def __init__(self):
        super().__init__("Fallback Retry")
    
    async def test_strategy(self, client: httpx.AsyncClient, tools: List[Dict]) -> Dict[str, Any]:
        self.total_attempts += 1
        
        # First attempt - normal request
        system_prompt = "You are a helpful assistant with access to tools."
        user_query = "What's the system memory usage right now?"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        response = await client.post(VLLM_URL, json={
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.3,
            "max_tokens": 500
        })
        
        result = response.json()
        tool_used = False
        
        if "choices" in result:
            msg = result["choices"][0]["message"]
            if msg.get("tool_calls"):
                tool_used = True
                self.success_count += 1
                return {
                    "strategy": self.name,
                    "tool_used": tool_used,
                    "attempts": 1,
                    "response": result,
                    "success_rate": self.get_success_rate()
                }
        
        # If no tool use, retry with hint
        messages.append(msg)
        messages.append({
            "role": "user", 
            "content": "Please use the system_info tool to get accurate real-time system information."
        })
        
        retry_response = await client.post(VLLM_URL, json={
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.3,
            "max_tokens": 500
        })
        
        retry_result = retry_response.json()
        if "choices" in retry_result:
            retry_msg = retry_result["choices"][0]["message"]
            if retry_msg.get("tool_calls"):
                tool_used = True
                self.success_count += 1
        
        return {
            "strategy": self.name,
            "tool_used": tool_used,
            "attempts": 2,
            "first_response": result,
            "retry_response": retry_result,
            "success_rate": self.get_success_rate()
        }


class ForcedToolChoiceStrategy(ToolCallStrategy):
    """Strategy 5: Check forced tool_choice support."""
    
    def __init__(self):
        super().__init__("Forced Tool Choice")
    
    async def test_strategy(self, client: httpx.AsyncClient, tools: List[Dict]) -> Dict[str, Any]:
        self.total_attempts += 1
        
        system_prompt = "You are a helpful assistant."
        user_query = "Calculate 10 + 15 * 2"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        # Test different tool_choice formats
        test_cases = [
            {"type": "function", "function": {"name": "calculator"}},  # Specific function
            "required",  # Any tool required
            {"type": "required"}  # Alternative format
        ]
        
        results = []
        for i, tool_choice in enumerate(test_cases):
            try:
                response = await client.post(VLLM_URL, json={
                    "model": "openai/gpt-oss-20b",
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": tool_choice,
                    "temperature": 0.3,
                    "max_tokens": 500
                })
                
                result = response.json()
                tool_used = False
                
                if "choices" in result:
                    msg = result["choices"][0]["message"]
                    if msg.get("tool_calls"):
                        tool_used = True
                        self.success_count += 1
                
                results.append({
                    "tool_choice_format": tool_choice,
                    "tool_used": tool_used,
                    "response": result
                })
                
            except Exception as e:
                results.append({
                    "tool_choice_format": tool_choice,
                    "error": str(e)
                })
        
        return {
            "strategy": self.name,
            "results": results,
            "success_rate": self.get_success_rate()
        }


async def execute_tool(tool_name: str, parameters: dict):
    """Execute tool through our API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{TOOL_API_URL}/execute",
                json={"tool_name": tool_name, "parameters": parameters}
            )
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}


async def run_comprehensive_tool_calling_test():
    """Run all strategies and compare effectiveness."""
    print("=" * 80)
    print("🧪 COMPREHENSIVE TOOL CALLING STRATEGY TEST")
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
                "description": "Get system information including CPU and memory usage",
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
                "name": "get_weather",
                "description": "Get weather information for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "City name"
                        },
                        "country": {
                            "type": "string", 
                            "description": "Country code"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    ]
    
    # Initialize strategies
    strategies = [
        GentleGuidanceStrategy(),
        ComplexityInductionStrategy(), 
        ExplicitRequirementStrategy(),
        FallbackRetryStrategy(),
        ForcedToolChoiceStrategy()
    ]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for strategy in strategies:
            print(f"\n🔬 Testing Strategy: {strategy.name}")
            print("-" * 50)
            
            try:
                result = await strategy.test_strategy(client, tools)
                
                print(f"✅ Strategy: {result['strategy']}")
                
                if result.get('tool_used'):
                    print("🎯 Tool calling: SUCCESS")
                else:
                    print("❌ Tool calling: FAILED")
                
                print(f"📊 Success rate: {result.get('success_rate', 0):.2%}")
                
                # Show specific results based on strategy
                if strategy.name == "Fallback Retry":
                    print(f"🔄 Attempts needed: {result.get('attempts', 1)}")
                elif strategy.name == "Forced Tool Choice":
                    working_formats = [r for r in result['results'] if r.get('tool_used')]
                    print(f"🛠️  Working tool_choice formats: {len(working_formats)}/3")
                    for fmt in working_formats:
                        print(f"   ✅ {fmt['tool_choice_format']}")
                
            except Exception as e:
                print(f"❌ Strategy failed: {e}")
    
    print("\n" + "=" * 80)
    print("📈 STRATEGY COMPARISON")
    print("=" * 80)
    
    strategies.sort(key=lambda s: s.get_success_rate(), reverse=True)
    
    print(f"{'Strategy':<20} {'Success Rate':<15} {'Attempts':<10}")
    print("-" * 50)
    
    for strategy in strategies:
        print(f"{strategy.name:<20} {strategy.get_success_rate():<15.2%} {strategy.total_attempts:<10}")
    
    print("\n🏆 Best performing strategy:", strategies[0].name if strategies else "None")
    
    # Test the best strategy with actual tool execution
    if strategies and strategies[0].get_success_rate() > 0:
        print(f"\n🚀 LIVE TEST: {strategies[0].name}")
        print("-" * 50)
        await run_live_test_with_execution(strategies[0], tools)


async def run_live_test_with_execution(strategy: ToolCallStrategy, tools: List[Dict]):
    """Run a live test with actual tool execution."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test calculation + system info
        system_prompt = (
            "You are a helpful assistant. When tools are available, prefer using them "
            "for more accurate results than manual calculation."
        )
        
        user_query = (
            "Please calculate 144 * 0.25 + sqrt(81) and also tell me the current system "
            "CPU usage percentage. Use the appropriate tools for accuracy."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        print(f"User: {user_query}")
        
        response = await client.post(VLLM_URL, json={
            "model": "openai/gpt-oss-20b",
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.3,
            "max_tokens": 1000
        })
        
        result = response.json()
        if "choices" in result:
            msg = result["choices"][0]["message"]
            
            if msg.get("tool_calls"):
                print("\n🎯 Model chose to use tools:")
                messages.append(msg)
                
                for call in msg["tool_calls"]:
                    print(f"\n  📞 Calling: {call['function']['name']}")
                    print(f"  📝 Args: {call['function']['arguments']}")
                    
                    # Execute the tool
                    args = json.loads(call['function']['arguments'])
                    tool_result = await execute_tool(call['function']['name'], args)
                    
                    if tool_result.get('status') == 'success':
                        print(f"  ✅ Result: {tool_result['data']}")
                    else:
                        print(f"  ❌ Error: {tool_result.get('error')}")
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": json.dumps(tool_result.get('data', tool_result.get('error')))
                    })
                
                # Get final response
                final_response = await client.post(VLLM_URL, json={
                    "model": "openai/gpt-oss-20b",
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 500
                })
                
                final = final_response.json()
                if "choices" in final:
                    print(f"\n🤖 Final Answer: {final['choices'][0]['message']['content']}")
            else:
                print(f"\n❌ No tool calls made. Direct response: {msg.get('content')}")


if __name__ == "__main__":
    asyncio.run(run_comprehensive_tool_calling_test())