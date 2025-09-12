#!/usr/bin/env python3
"""
Production Tool Calling Proxy for gpt-oss-20b
Implements prioritized fallback strategy for maximum success rate with OpenAI compatibility.

Priority 1: Named Function 강제 호출 (Native)
Priority 2: Auto + Guided Decoding (Native) 
Priority 3: 구조적 출력 브리지 (Server Wrapping)
Priority 4: Two-Pass 라우터 (Server-Driven)
"""

import asyncio
import json
import uuid
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import logging

# Configuration  
import os
VLLM_URL = os.getenv("VLLM_URL", "http://localhost:8000/v1/chat/completions")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001") 
PROXY_PORT = int(os.getenv("PROXY_PORT", "8001"))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GPT-OSS Tool Calling Proxy", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Any] = "auto"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500
    stream: Optional[bool] = False


class ToolCallProxy:
    """Main proxy handler with prioritized fallback strategy."""
    
    def __init__(self):
        self.stats = {
            "total_requests": 0,
            "priority_1_success": 0,
            "priority_2_success": 0, 
            "priority_3_success": 0,
            "priority_4_success": 0,
            "fallback_rate": 0
        }
    
    async def process_request(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """Main entry point - processes request with prioritized fallback."""
        
        self.stats["total_requests"] += 1
        start_time = time.time()
        
        logger.info(f"🚀 Processing request #{self.stats['total_requests']}")
        logger.info(f"Tools provided: {len(request.tools) if request.tools else 0}")
        
        # If no tools, pass through directly
        if not request.tools:
            logger.info("📝 No tools provided, passing through to vLLM")
            return await self._passthrough_to_vllm(request)
        
        # Try priorities in order
        strategies = [
            ("Priority 1: Named Function Force", self._try_priority_1),
            ("Priority 2: Auto + Guided", self._try_priority_2),
            ("Priority 3: Structured Bridge", self._try_priority_3),
            ("Priority 4: Two-Pass Router", self._try_priority_4)
        ]
        
        for strategy_name, strategy_func in strategies:
            logger.info(f"🔬 Trying {strategy_name}")
            
            try:
                success, result = await strategy_func(request)
                
                if success:
                    elapsed = time.time() - start_time
                    logger.info(f"✅ {strategy_name} succeeded in {elapsed:.2f}s")
                    self._update_stats(strategy_name)
                    return result
                else:
                    logger.warning(f"❌ {strategy_name} failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"💥 {strategy_name} exception: {e}")
        
        # All strategies failed
        logger.error("🚨 All strategies failed, returning error")
        return {
            "error": {
                "message": "All tool calling strategies failed",
                "type": "InternalServerError", 
                "code": 500
            }
        }
    
    def _update_stats(self, strategy_name: str):
        """Update success statistics."""
        if "Priority 1" in strategy_name:
            self.stats["priority_1_success"] += 1
        elif "Priority 2" in strategy_name:
            self.stats["priority_2_success"] += 1
        elif "Priority 3" in strategy_name:
            self.stats["priority_3_success"] += 1
        elif "Priority 4" in strategy_name:
            self.stats["priority_4_success"] += 1
    
    async def _try_priority_1(self, request: ChatCompletionRequest) -> Tuple[bool, Dict]:
        """Priority 1: Named Function 강제 호출 (Native vLLM)."""
        
        # Detect primary tool intent
        tool_name = self._detect_primary_tool(request.messages, request.tools)
        
        if not tool_name:
            return False, {"error": "Could not determine primary tool"}
        
        # Force specific tool choice
        vllm_request = {
            "model": request.model,
            "messages": request.messages,
            "tools": request.tools,
            "tool_choice": {
                "type": "function",
                "function": {"name": tool_name}
            },
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(VLLM_URL, json=vllm_request)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check if tool_calls were generated
                    if self._has_tool_calls(result):
                        logger.info(f"🎯 Priority 1 success: {tool_name} called")
                        return True, result
                    else:
                        return False, {"error": "No tool_calls in response despite forced choice"}
                else:
                    return False, {"error": f"HTTP {response.status_code}: {response.text}"}
                    
            except Exception as e:
                return False, {"error": f"Request failed: {e}"}
    
    async def _try_priority_2(self, request: ChatCompletionRequest) -> Tuple[bool, Dict]:
        """Priority 2: Auto + Guided Decoding (Native vLLM)."""
        
        # Use auto choice with complexity-induced prompt
        enhanced_messages = self._enhance_messages_for_tool_use(request.messages)
        
        vllm_request = {
            "model": request.model,
            "messages": enhanced_messages,
            "tools": request.tools,
            "tool_choice": "auto",
            "temperature": 0.1,  # Lower temp for more consistent tool use
            "max_tokens": request.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(VLLM_URL, json=vllm_request)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if self._has_tool_calls(result):
                        logger.info("🤖 Priority 2 success: Auto choice worked")
                        return True, result
                    else:
                        return False, {"error": "Auto choice did not generate tool calls"}
                else:
                    return False, {"error": f"HTTP {response.status_code}: {response.text}"}
                    
            except Exception as e:
                return False, {"error": f"Request failed: {e}"}
    
    async def _try_priority_3(self, request: ChatCompletionRequest) -> Tuple[bool, Dict]:
        """Priority 3: 구조적 출력 브리지 (Server Wrapping)."""
        
        logger.info("🌉 Using structured output bridge")
        
        # Step 1: Get tool routing decision from model
        should_use_tool, tool_name, parameters = await self._get_tool_routing_decision(request)
        
        if not should_use_tool:
            # No tool needed, return normal response
            return await self._get_normal_response(request)
        
        # Step 2: Execute the tool
        tool_result = await self._execute_backend_tool(tool_name, parameters)
        
        if tool_result.get("status") != "success":
            return False, {"error": f"Tool execution failed: {tool_result.get('error')}"}
        
        # Step 3: Create OpenAI-compatible response
        openai_response = self._create_openai_tool_response(tool_name, parameters, tool_result)
        logger.info("🎭 Created OpenAI-compatible tool_calls response")
        return True, openai_response
    
    async def _try_priority_4(self, request: ChatCompletionRequest) -> Tuple[bool, Dict]:
        """Priority 4: Two-Pass 라우터 (Server-Driven Separation)."""
        
        logger.info("🔄 Using two-pass router")
        
        # Pass 1: Tool vs Direct decision
        use_tool_decision = await self._pass_1_tool_decision(request)
        
        if not use_tool_decision["use_tool"]:
            return await self._get_normal_response(request)
        
        # Pass 2: Tool parameters extraction
        tool_name = use_tool_decision["tool_name"]
        parameters = await self._pass_2_extract_parameters(request, tool_name)
        
        # Execute tool
        tool_result = await self._execute_backend_tool(tool_name, parameters)
        
        if tool_result.get("status") != "success":
            return False, {"error": f"Tool execution failed: {tool_result.get('error')}"}
        
        # Pass 3: Generate final summary
        final_response = await self._pass_3_generate_summary(request, tool_result)
        
        # Format as OpenAI tool_calls
        openai_response = self._create_openai_tool_response(tool_name, parameters, tool_result)
        return True, openai_response
    
    def _detect_primary_tool(self, messages: List[Dict], tools: List[Dict]) -> Optional[str]:
        """Detect which tool is most likely needed for Priority 1."""
        
        if not messages:
            return None
        
        # Get last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "").lower()
                break
        
        available_tools = [tool["function"]["name"] for tool in tools]
        
        # Pattern matching for tool detection
        if any(word in user_message for word in ["계산", "곱하기", "더하기", "*", "+", "-", "/", "×"]):
            if "calculator" in available_tools:
                return "calculator"
        
        if any(word in user_message for word in ["날씨", "기온", "weather", "temperature"]):
            if "get_weather" in available_tools:
                return "get_weather"
        
        if any(word in user_message for word in ["시스템", "cpu", "메모리", "memory"]):
            if "system_info" in available_tools:
                return "system_info"
        
        # Default to first available tool
        return available_tools[0] if available_tools else None
    
    def _enhance_messages_for_tool_use(self, messages: List[Dict]) -> List[Dict]:
        """Enhance messages to encourage tool use for Priority 2."""
        
        enhanced = messages.copy()
        
        # Modify system message to encourage tool use
        system_msg_found = False
        for i, msg in enumerate(enhanced):
            if msg.get("role") == "system":
                enhanced[i] = {
                    "role": "system",
                    "content": f"{msg['content']} 정확성을 위해 가능한 경우 항상 제공된 도구를 사용하세요."
                }
                system_msg_found = True
                break
        
        if not system_msg_found:
            enhanced.insert(0, {
                "role": "system",
                "content": "정확성을 위해 가능한 경우 항상 제공된 도구를 사용하세요."
            })
        
        return enhanced
    
    async def _get_tool_routing_decision(self, request: ChatCompletionRequest) -> Tuple[bool, str, Dict]:
        """Get tool routing decision for Priority 3."""
        
        # Create routing prompt
        user_message = request.messages[-1]["content"]
        tools_desc = []
        for tool in request.tools:
            func = tool["function"]
            tools_desc.append(f"- {func['name']}: {func['description']}")
        
        routing_prompt = f"""다음 요청에 대해 도구를 사용해야 하는지 판단하고, 필요한 경우 도구 이름과 매개변수를 JSON으로 출력하세요.

사용 가능한 도구:
{chr(10).join(tools_desc)}

사용자 요청: {user_message}

도구가 필요한 경우 다음 형식으로만 출력:
{{"use_tool": true, "tool_name": "도구명", "parameters": {{"매개변수": "값"}}}}

도구가 불필요한 경우:
{{"use_tool": false}}

JSON만 출력하세요."""
        
        routing_request = {
            "model": request.model,
            "messages": [{"role": "user", "content": routing_prompt}],
            "temperature": 0,
            "max_tokens": 150
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(VLLM_URL, json=routing_request)
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"].strip()
                    
                    # Parse JSON response
                    try:
                        decision = json.loads(content)
                        if decision.get("use_tool", False):
                            return True, decision.get("tool_name", ""), decision.get("parameters", {})
                        else:
                            return False, "", {}
                    except json.JSONDecodeError:
                        # Fallback to pattern matching
                        return self._fallback_pattern_detection(user_message, request.tools)
            except Exception as e:
                logger.error(f"Tool routing failed: {e}")
        
        return False, "", {}
    
    def _fallback_pattern_detection(self, user_message: str, tools: List[Dict]) -> Tuple[bool, str, Dict]:
        """Fallback pattern detection when JSON parsing fails."""
        
        text = user_message.lower()
        available_tools = [tool["function"]["name"] for tool in tools]
        
        # Calculator patterns
        calc_patterns = [
            r'(\d+)\s*[×*곱하기]\s*(\d+)',
            r'(\d+)\s*\+\s*(\d+)',
            r'(\d+)\s*-\s*(\d+)',
            r'(\d+)\s*/\s*(\d+)'
        ]
        
        if "calculator" in available_tools:
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
                        expr = f"{match.group(1)} * {match.group(2)}"
                    
                    return True, "calculator", {"expression": expr}
        
        # System info patterns
        if "system_info" in available_tools:
            if any(word in text for word in ['시스템', 'cpu', '메모리', 'memory']):
                return True, "system_info", {"info_type": "all"}
        
        return False, "", {}
    
    async def _execute_backend_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute tool via backend API."""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{BACKEND_URL}/execute",
                    json={"tool_name": tool_name, "parameters": parameters}
                )
                result = response.json()
                logger.info(f"🔧 Tool {tool_name} executed: {result.get('status')}")
                return result
            except Exception as e:
                logger.error(f"Backend tool execution failed: {e}")
                return {
                    "status": "error",
                    "error": f"Backend connection failed: {e}"
                }
    
    def _create_openai_tool_response(self, tool_name: str, parameters: Dict, tool_result: Dict) -> Dict:
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
    
    async def _get_normal_response(self, request: ChatCompletionRequest) -> Tuple[bool, Dict]:
        """Get normal response without tools."""
        
        normal_request = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(VLLM_URL, json=normal_request)
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, {"error": f"HTTP {response.status_code}: {response.text}"}
            except Exception as e:
                return False, {"error": f"Request failed: {e}"}
    
    async def _pass_1_tool_decision(self, request: ChatCompletionRequest) -> Dict:
        """Two-pass router: Pass 1 - Tool decision."""
        # Simplified implementation - would expand in production
        should_use, tool_name, _ = await self._get_tool_routing_decision(request)
        return {"use_tool": should_use, "tool_name": tool_name}
    
    async def _pass_2_extract_parameters(self, request: ChatCompletionRequest, tool_name: str) -> Dict:
        """Two-pass router: Pass 2 - Parameter extraction."""
        # Would implement detailed parameter extraction logic
        return self._fallback_pattern_detection(request.messages[-1]["content"], request.tools)[2]
    
    async def _pass_3_generate_summary(self, request: ChatCompletionRequest, tool_result: Dict) -> Dict:
        """Two-pass router: Pass 3 - Summary generation."""
        # Would implement summary generation
        return {"summary": "Tool execution completed"}
    
    async def _passthrough_to_vllm(self, request: ChatCompletionRequest) -> Dict:
        """Pass request directly to vLLM without tool processing."""
        
        vllm_request = {
            "model": request.model,
            "messages": request.messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(VLLM_URL, json=vllm_request)
                return response.json()
            except Exception as e:
                return {
                    "error": {
                        "message": f"Passthrough failed: {e}",
                        "type": "BadRequestError",
                        "code": 400
                    }
                }
    
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


# Global proxy instance
proxy = ToolCallProxy()


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint with tool calling."""
    
    try:
        result = await proxy.process_request(request)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Request processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/models")
async def list_models():
    """List available models."""
    return {
        "object": "list",
        "data": [
            {
                "id": "openai/gpt-oss-20b",
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "gpt-oss-proxy"
            }
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "proxy_version": "1.0.0",
        "stats": proxy.stats
    }


@app.get("/stats")
async def get_stats():
    """Get proxy statistics."""
    total = proxy.stats["total_requests"]
    
    if total > 0:
        proxy.stats["fallback_rate"] = (
            (proxy.stats["priority_3_success"] + proxy.stats["priority_4_success"]) / total
        )
    
    return {
        "statistics": proxy.stats,
        "success_rates": {
            "priority_1": proxy.stats["priority_1_success"] / max(1, total),
            "priority_2": proxy.stats["priority_2_success"] / max(1, total),
            "priority_3": proxy.stats["priority_3_success"] / max(1, total),
            "priority_4": proxy.stats["priority_4_success"] / max(1, total)
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting GPT-OSS Tool Calling Proxy")
    logger.info(f"📡 vLLM Backend: {VLLM_URL}")
    logger.info(f"🔧 Tool Backend: {BACKEND_URL}")
    logger.info(f"🌐 Proxy Port: {PROXY_PORT}")
    
    uvicorn.run(app, host="0.0.0.0", port=PROXY_PORT, log_level="info")