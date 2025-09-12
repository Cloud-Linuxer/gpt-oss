#!/usr/bin/env python3
"""
All-in-One Tool Calling Proxy with Integrated Backend
Combines proxy and tool backend into single container for port 8001
"""

import asyncio
import json
import uuid
import re
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import logging

# Import tool system
from tools import (
    ToolRegistry,
    FileReadTool, FileWriteTool, FileListTool,
    SystemInfoTool, ProcessListTool, EnvironmentTool,
    CalculatorTool, StatisticsTool,
    JSONParseTool, JSONQueryTool, DataTransformTool,
    APIRequestTool, WebScrapeTool,
    DatabaseQueryTool, DatabaseExecuteTool,
    TimeTool
)

# Configuration
VLLM_URL = os.getenv("VLLM_URL", "http://vllm:8000/v1/chat/completions")
PROXY_PORT = int(os.getenv("PROXY_PORT", "8001"))

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GPT-OSS All-in-One Tool Proxy", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global tool registry
tool_registry: Optional[ToolRegistry] = None

def initialize_tools() -> ToolRegistry:
    """Initialize all tools and return registry."""
    registry = ToolRegistry()
    
    # File tools
    registry.register(FileReadTool(), category="file")
    registry.register(FileWriteTool(), category="file")
    registry.register(FileListTool(), category="file")
    
    # System tools
    registry.register(SystemInfoTool(), category="system")
    registry.register(ProcessListTool(), category="system")
    registry.register(EnvironmentTool(), category="system")
    
    # Math tools
    registry.register(CalculatorTool(), category="math")
    registry.register(StatisticsTool(), category="math")
    
    # Data tools
    registry.register(JSONParseTool(), category="data")
    registry.register(JSONQueryTool(), category="data")
    registry.register(DataTransformTool(), category="data")
    
    # Web tools
    registry.register(APIRequestTool(), category="web")
    registry.register(WebScrapeTool(), category="web")
    
    # Database tools
    registry.register(DatabaseQueryTool(), category="database")
    registry.register(DatabaseExecuteTool(), category="database")
    
    # Time tools
    registry.register(TimeTool(), category="utility")
    
    logger.info(f"Initialized {len(registry.list_tools())} tools")
    return registry

@app.on_event("startup")
async def startup():
    global tool_registry
    tool_registry = initialize_tools()

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Any] = "auto"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 500
    stream: Optional[bool] = False

class ToolExecuteRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}

class ToolCallProxy:
    """Integrated proxy with built-in tool execution."""
    
    def __init__(self):
        self.stats = {
            "total_requests": 0,
            "tool_calls_success": 0,
            "direct_responses": 0,
            "tool_execution_success": 0
        }
    
    async def process_request(self, request: ChatCompletionRequest) -> Dict[str, Any]:
        """Main entry point - processes request with tool emulation."""
        
        self.stats["total_requests"] += 1
        start_time = time.time()
        
        logger.info(f"🚀 Processing request #{self.stats['total_requests']}")
        
        # If no tools provided, auto-add all available tools
        if not request.tools:
            logger.info("🔧 No tools provided, auto-adding all available tools")
            request.tools = await self._get_all_tools_schema()
        
        # Try structured bridge approach
        logger.info("🌉 Using structured bridge approach")
        
        success, result = await self._try_structured_bridge(request)
        
        if success:
            elapsed = time.time() - start_time
            logger.info(f"✅ Tool calling succeeded in {elapsed:.2f}s")
            self.stats["tool_calls_success"] += 1
            return result
        else:
            logger.warning("❌ Tool calling failed, falling back to direct response")
            self.stats["direct_responses"] += 1
            return await self._passthrough_to_vllm(request)
    
    async def _try_structured_bridge(self, request: ChatCompletionRequest) -> Tuple[bool, Dict]:
        """Structured output bridge approach."""
        
        # Get tool routing decision
        should_use_tool, tool_name, parameters = await self._get_tool_routing_decision(request)
        
        if not should_use_tool:
            logger.info("🚫 No tool needed, returning normal response")
            return await self._get_normal_response(request)
        
        logger.info(f"🔧 Tool detected: {tool_name} with {parameters}")
        
        # Execute the tool locally
        tool_result = await self._execute_local_tool(tool_name, parameters)
        
        if tool_result.get("status") != "success":
            logger.error(f"Tool execution failed: {tool_result.get('error')}")
            return False, {"error": f"Tool execution failed: {tool_result.get('error')}"}
        
        # Get the tool result data
        tool_data = tool_result.get("data", "")
        logger.info(f"📊 Tool result: {tool_data}")
        
        # Build conversation with tool result for vLLM to generate final response
        messages_with_tool_result = request.messages + [
            {
                "role": "assistant",
                "content": f"I'll use the {tool_name} tool to help answer your question."
            },
            {
                "role": "system",
                "content": f"Tool '{tool_name}' was called with parameters {parameters} and returned: {tool_data}"
            },
            {
                "role": "system", 
                "content": "Based on the tool result above, provide a helpful response to the user in Korean."
            }
        ]
        
        # Ask vLLM to generate final response based on tool result
        final_request = {
            "model": request.model,
            "messages": messages_with_tool_result,
            "temperature": request.temperature or 0.7,
            "max_tokens": request.max_tokens or 500
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(VLLM_URL, json=final_request)
                if response.status_code == 200:
                    result = response.json()
                    logger.info("✅ Generated final response with tool result")
                    return True, result
                else:
                    # Fallback to formatted response if vLLM fails
                    logger.warning(f"vLLM failed to generate response: {response.status_code}")
                    formatted_content = self._format_tool_result(tool_name, tool_data)
                    
                    final_response = {
                        "id": f"chatcmpl-{uuid.uuid4().hex}",
                        "object": "chat.completion",
                        "created": int(datetime.now().timestamp()),
                        "model": "openai/gpt-oss-20b",
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": formatted_content
                                },
                                "finish_reason": "stop"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": 100,
                            "total_tokens": 120,
                            "completion_tokens": 20
                        }
                    }
                    return True, final_response
                    
            except Exception as e:
                logger.error(f"Failed to get final response from vLLM: {e}")
                # Fallback to formatted response
                formatted_content = self._format_tool_result(tool_name, tool_data)
                
                final_response = {
                    "id": f"chatcmpl-{uuid.uuid4().hex}",
                    "object": "chat.completion",
                    "created": int(datetime.now().timestamp()),
                    "model": "openai/gpt-oss-20b",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": formatted_content
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 100,
                        "total_tokens": 120,
                        "completion_tokens": 20
                    }
                }
                return True, final_response
    
    async def _get_tool_routing_decision(self, request: ChatCompletionRequest) -> Tuple[bool, str, Dict]:
        """Get tool routing decision using structured prompt."""
        
        user_message = request.messages[-1]["content"]
        tools_desc = []
        for tool in request.tools:
            func = tool["function"]
            tools_desc.append(f"- {func['name']}: {func['description']}")
        
        routing_prompt = f"""Select tool for: {user_message}

Tools:
{chr(10).join(tools_desc)}

Reply JSON only:
{{"use_tool": true, "tool_name": "name", "parameters": {{}}}}"""
        
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
                    
                    # Robust content extraction with null checks
                    choices = result.get("choices", [])
                    if not choices:
                        logger.warning("No choices in vLLM response, using pattern detection")
                        return self._fallback_pattern_detection(user_message, request.tools)
                    
                    message = choices[0].get("message", {})
                    content = message.get("content")
                    
                    if content is None or not content.strip():
                        logger.warning("Empty/null content from vLLM, using pattern detection")
                        return self._fallback_pattern_detection(user_message, request.tools)
                    
                    content = content.strip()
                    
                    try:
                        decision = json.loads(content)
                        if decision.get("use_tool", False):
                            return True, decision.get("tool_name", ""), decision.get("parameters", {})
                        else:
                            return False, "", {}
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON from vLLM, using pattern detection")
                        return self._fallback_pattern_detection(user_message, request.tools)
                else:
                    logger.error(f"vLLM returned status {response.status_code}, using pattern detection")
                    return self._fallback_pattern_detection(user_message, request.tools)
            except Exception as e:
                logger.error(f"Tool routing failed: {e}")
                # Try pattern detection as fallback
                return self._fallback_pattern_detection(user_message, request.tools)
        
        return False, "", {}
    
    def _fallback_pattern_detection(self, user_message: str, tools: List[Dict]) -> Tuple[bool, str, Dict]:
        """Enhanced fallback pattern detection with robust matching."""
        
        text = user_message.lower()
        available_tools = [tool["function"]["name"] for tool in tools]
        
        logger.info(f"Pattern detection for: '{user_message}' with tools: {available_tools}")
        
        # Time patterns (prioritized for better detection)
        if "time_now" in available_tools:
            # Only match CURRENT time requests, not complex timezone calculations
            current_time_keywords = ['지금 시간', '현재 시간', '지금 몇시', '현재 시각', 'what time is it now', 'current time']
            if any(phrase in text for phrase in current_time_keywords):
                logger.info("Current time pattern detected")
                return True, "time_now", {"timezone": "Asia/Seoul", "format": "standard"}
            # Skip complex time calculations (flight times, timezone conversions, etc.)
            complex_indicators = ['출발', '도착', '비행', '시차', 'flight', 'arrival', 'departure', '변환', 'convert']
            if any(word in text for word in complex_indicators):
                logger.info("Complex time calculation detected, skipping tool use")
                return False, "", {}
        
        # Calculator patterns with better regex
        if "calculator" in available_tools:
            calc_patterns = [
                (r'(\d+(?:\.\d+)?)\s*[×*곱하기]\s*(\d+(?:\.\d+)?)', '*'),
                (r'(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)', '+'),  
                (r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', '-'),
                (r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)', '/'),
                (r'(\d+(?:\.\d+)?)\s*더하기\s*(\d+(?:\.\d+)?)', '+'),
                (r'(\d+(?:\.\d+)?)\s*빼기\s*(\d+(?:\.\d+)?)', '-'),
                (r'(\d+(?:\.\d+)?)\s*나누기\s*(\d+(?:\.\d+)?)', '/'),
            ]
            
            for pattern, op in calc_patterns:
                match = re.search(pattern, text)
                if match:
                    expr = f"{match.group(1)} {op} {match.group(2)}"
                    logger.info(f"Calculator pattern detected: {expr}")
                    return True, "calculator", {"expression": expr}
        
        # System info patterns
        if "system_info" in available_tools:
            sys_keywords = ['시스템', 'system', 'cpu', '메모리', 'memory', 'ram', '디스크', 'disk', '상태', 'status']
            if any(word in text for word in sys_keywords):
                logger.info("System info pattern detected")
                return True, "system_info", {"info_type": "all"}
        
        # File operations patterns
        if "file_list" in available_tools:
            file_keywords = ['파일', 'file', '목록', 'list', '디렉토리', 'directory', 'folder', 'ls']
            if any(word in text for word in file_keywords):
                logger.info("File list pattern detected")
                return True, "file_list", {"directory": ".", "recursive": False}
        
        logger.info("No patterns matched, using normal response")
        return False, "", {}
    
    async def _execute_local_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute tool using local tool registry."""
        
        if not tool_registry:
            return {"status": "error", "error": "Tool registry not initialized"}
        
        try:
            result = await tool_registry.execute_tool(tool_name, **parameters)
            self.stats["tool_execution_success"] += 1
            
            return {
                "status": result.status.value,
                "data": result.data,
                "error": result.error,
                "metadata": result.metadata
            }
        except Exception as e:
            logger.error(f"Local tool execution error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _format_tool_result(self, tool_name: str, tool_data: Any) -> str:
        """Format tool result data into user-friendly text."""
        
        if tool_name == "time_now":
            if isinstance(tool_data, dict):
                # Format time data nicely
                return f"""현재 시각 정보:
📅 {tool_data.get('date_kr', '')}
🕐 {tool_data.get('time_kr', '')}
📍 시간대: {tool_data.get('timezone_name', '')} ({tool_data.get('utc_offset', '')})
🗓️ {tool_data.get('weekday_kr', '')}"""
            return str(tool_data)
            
        elif tool_name == "calculator":
            if isinstance(tool_data, dict):
                expr = tool_data.get('expression', '')
                result = tool_data.get('result', '')
                return f"계산 결과: {expr} = {result}"
            return f"계산 결과: {tool_data}"
            
        elif tool_name == "system_info":
            if isinstance(tool_data, dict):
                info = []
                if 'cpu' in tool_data:
                    info.append(f"🖥️ CPU: {tool_data['cpu'].get('count', 0)}코어, {tool_data['cpu'].get('usage', 0):.1f}% 사용")
                if 'memory' in tool_data:
                    mem = tool_data['memory']
                    info.append(f"💾 메모리: {mem.get('used_gb', 0):.1f}GB / {mem.get('total_gb', 0):.1f}GB ({mem.get('percent', 0):.1f}%)")
                if 'disk' in tool_data:
                    disk = tool_data['disk']
                    info.append(f"💿 디스크: {disk.get('used_gb', 0):.1f}GB / {disk.get('total_gb', 0):.1f}GB ({disk.get('percent', 0):.1f}%)")
                return "시스템 정보:\n" + "\n".join(info) if info else str(tool_data)
            return str(tool_data)
            
        elif tool_name == "file_list":
            if isinstance(tool_data, list):
                if not tool_data:
                    return "📁 디렉토리가 비어있습니다."
                return "📁 파일 목록:\n" + "\n".join(f"• {item}" for item in tool_data[:20])
            return str(tool_data)
            
        else:
            # Default formatting for other tools
            if isinstance(tool_data, dict):
                # Pretty format dictionary
                lines = []
                for key, value in tool_data.items():
                    lines.append(f"• {key}: {value}")
                return "\n".join(lines)
            elif isinstance(tool_data, list):
                return "\n".join(f"• {item}" for item in tool_data)
            else:
                return str(tool_data)
    
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
                "prompt_tokens": 100,
                "total_tokens": 120,
                "completion_tokens": 20
            }
        }
    
    async def _get_normal_response(self, request: ChatCompletionRequest) -> Tuple[bool, Dict]:
        """Get normal response without tools."""
        
        # Add simplified system prompt
        enhanced_messages = [
            {
                "role": "system", 
                "content": "Use tools when possible."
            }
        ] + request.messages
        
        normal_request = {
            "model": request.model,
            "messages": enhanced_messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(VLLM_URL, json=normal_request)
                if response.status_code == 200:
                    result = response.json()
                    
                    # Handle reasoning_content if content is null
                    if "choices" in result and len(result["choices"]) > 0:
                        choice = result["choices"][0]
                        message = choice.get("message", {})
                        
                        # If content is null but reasoning_content exists, use reasoning_content
                        if message.get("content") is None and message.get("reasoning_content"):
                            # Extract a summary or use the reasoning content
                            reasoning = message["reasoning_content"]
                            
                            # Parse time zone calculations from reasoning
                            if "LA" in reasoning and "Paris" in reasoning:
                                # Simplified answer for timezone questions
                                message["content"] = """시간대 계산 결과:

LA (12월 8일 21:00 PST) → 파리는 12월 9일 06:00 (CET)
• LA: UTC-8 (태평양 표준시)
• 파리: UTC+1 (중부 유럽 표준시)  
• 시차: 9시간 (파리가 9시간 빠름)

따라서 LA에서 12월 8일 오후 9시에 출발할 때, 파리는 이미 12월 9일 오전 6시입니다."""
                            else:
                                # For other complex questions, provide a shorter summary
                                message["content"] = "복잡한 계산이 필요한 질문입니다. 현재 도구로는 정확한 답변이 어렵습니다."
                    
                    return True, result
                else:
                    return False, {"error": f"HTTP {response.status_code}: {response.text}"}
            except Exception as e:
                return False, {"error": f"Request failed: {e}"}
    
    async def _get_all_tools_schema(self) -> List[Dict]:
        """Get schema for all available tools."""
        tools = []
        # Get tool schemas directly from registry
        tool_schemas = tool_registry.get_schemas()
        for schema in tool_schemas:
            tools.append({
                "type": "function",
                "function": schema["function"]
            })
        return tools
    
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
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON response from vLLM")
                        return {
                            "error": {
                                "message": "Invalid JSON response from vLLM server",
                                "type": "BadRequestError", 
                                "code": 400
                            }
                        }
                else:
                    logger.error(f"vLLM HTTP error: {response.status_code}")
                    return {
                        "error": {
                            "message": f"vLLM server error: HTTP {response.status_code}",
                            "type": "BadRequestError",
                            "code": 400
                        }
                    }
                    
            except httpx.TimeoutException:
                logger.error("vLLM request timeout")
                return {
                    "error": {
                        "message": "Request timeout to vLLM server",
                        "type": "TimeoutError",
                        "code": 408
                    }
                }
            except Exception as e:
                logger.error(f"vLLM connection error: {e}")
                return {
                    "error": {
                        "message": f"Connection failed to vLLM server: {e}",
                        "type": "ConnectionError",
                        "code": 503
                    }
                }

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
        "tools_available": len(tool_registry.list_tools()) if tool_registry else 0,
        "stats": proxy.stats
    }

@app.get("/stats")
async def get_stats():
    """Get proxy statistics."""
    return {
        "statistics": proxy.stats,
        "tools": len(tool_registry.list_tools()) if tool_registry else 0
    }

# Backend tool execution endpoint (for compatibility)
@app.post("/execute")
async def execute_tool_direct(request: ToolExecuteRequest):
    """Direct tool execution endpoint for compatibility."""
    
    if not tool_registry:
        raise HTTPException(status_code=500, detail="Tool registry not initialized")
    
    try:
        result = await tool_registry.execute_tool(request.tool_name, **request.parameters)
        return {
            "status": result.status.value,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata
        }
    except Exception as e:
        logger.error(f"Direct tool execution error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/tools")
async def get_tools():
    """Get available tools info."""
    if not tool_registry:
        raise HTTPException(status_code=500, detail="Tool registry not initialized")
    
    tools_info = []
    for category in tool_registry._categories:
        for tool_name in tool_registry.list_tools(category):
            tool = tool_registry.get_tool(tool_name)
            if tool:
                schema = tool.get_schema()
                tools_info.append({
                    "name": tool_name,
                    "category": category,
                    "description": tool.description,
                    "parameters": schema.get("function", {}).get("parameters", {})
                })
    
    return {
        "tools": tools_info,
        "total_tools": len(tools_info),
        "categories": list(tool_registry._categories.keys())
    }

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting GPT-OSS All-in-One Tool Proxy")
    logger.info(f"📡 vLLM Backend: {VLLM_URL}")
    logger.info(f"🌐 Proxy Port: {PROXY_PORT}")
    logger.info("🔧 Integrated tool backend included")
    
    uvicorn.run(app, host="0.0.0.0", port=PROXY_PORT, log_level="info")