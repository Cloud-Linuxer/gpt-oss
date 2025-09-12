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
VLLM_URL = os.getenv("VLLM_URL", "http://host.docker.internal:8000/v1/chat/completions")
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
        
        # If no tools, pass through directly
        if not request.tools:
            logger.info("📝 No tools provided, passing through to vLLM")
            self.stats["direct_responses"] += 1
            return await self._passthrough_to_vllm(request)
        
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
        
        # Create OpenAI-compatible response
        openai_response = self._create_openai_tool_response(tool_name, parameters, tool_result)
        logger.info("🎭 Created OpenAI-compatible tool_calls response")
        return True, openai_response
    
    async def _get_tool_routing_decision(self, request: ChatCompletionRequest) -> Tuple[bool, str, Dict]:
        """Get tool routing decision using structured prompt."""
        
        user_message = request.messages[-1]["content"]
        tools_desc = []
        for tool in request.tools:
            func = tool["function"]
            tools_desc.append(f"- {func['name']}: {func['description']}")
        
        routing_prompt = f"""다음 요청에 대해 도구를 사용해야 하는지 판단하고 JSON으로 출력하세요.

사용 가능한 도구:
{chr(10).join(tools_desc)}

사용자 요청: {user_message}

도구가 필요한 경우:
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
                # Try pattern detection as fallback
                return self._fallback_pattern_detection(user_message, request.tools)
        
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