"""API Routes and endpoint mappings for the backend."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

# API Route Models
class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role (system/user/assistant/tool)")
    content: str = Field(..., description="Message content")
    tool_call_id: Optional[str] = Field(None, description="Tool call ID for tool responses")
    name: Optional[str] = Field(None, description="Tool name for tool responses")

class ChatRequest(BaseModel):
    """Chat request model."""
    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    model: Optional[str] = Field(None, description="Model to use")
    temperature: Optional[float] = Field(0.7, description="Temperature for sampling")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="Available tools")
    tool_choice: Optional[str] = Field("auto", description="Tool selection mode")
    stream: Optional[bool] = Field(False, description="Stream responses")

class ChatResponse(BaseModel):
    """Chat response model."""
    id: str = Field(..., description="Response ID")
    object: str = Field("chat.completion", description="Response type")
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[Dict[str, Any]] = Field(..., description="Response choices")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage")

class ToolCall(BaseModel):
    """Tool call model."""
    id: str = Field(..., description="Tool call ID")
    type: str = Field("function", description="Tool call type")
    function: Dict[str, Any] = Field(..., description="Function details")

class ToolExecuteRequest(BaseModel):
    """Tool execution request."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(default={}, description="Tool parameters")
    timeout: Optional[float] = Field(30.0, description="Execution timeout")

class ToolExecuteResponse(BaseModel):
    """Tool execution response."""
    status: str = Field(..., description="Execution status (success/error/timeout)")
    data: Optional[Any] = Field(None, description="Execution result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ToolInfo(BaseModel):
    """Tool information model."""
    name: str = Field(..., description="Tool name")
    category: str = Field(..., description="Tool category")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(..., description="Parameter schema")
    timeout: float = Field(30.0, description="Default timeout")

class ToolListResponse(BaseModel):
    """Tool list response."""
    tools: List[ToolInfo] = Field(..., description="Available tools")
    total_count: int = Field(..., description="Total number of tools")
    categories: List[str] = Field(..., description="Available categories")

class ToolStatsResponse(BaseModel):
    """Tool statistics response."""
    total_tools: int = Field(..., description="Total number of tools")
    categories: List[str] = Field(..., description="Tool categories")
    tools: List[Dict[str, Any]] = Field(..., description="Per-tool statistics")

# OpenAI-compatible endpoints
class CompletionRequest(BaseModel):
    """OpenAI-compatible completion request."""
    model: str = Field(..., description="Model to use")
    messages: List[Dict[str, Any]] = Field(..., description="Messages")
    temperature: Optional[float] = Field(0.7, description="Temperature")
    max_tokens: Optional[int] = Field(1000, description="Max tokens")
    n: Optional[int] = Field(1, description="Number of completions")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")
    stream: Optional[bool] = Field(False, description="Stream response")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="Available tools")
    tool_choice: Optional[Any] = Field(None, description="Tool choice")

# API Router Factory
def create_api_router(tool_registry, vllm_client, mcp_tools=None):
    """Create API router with all endpoints."""
    router = APIRouter()
    
    @router.post("/execute")
    async def execute_tool(request: ToolExecuteRequest) -> ToolExecuteResponse:
        """Execute a specific tool."""
        try:
            result = await tool_registry.execute_tool(
                request.tool_name, 
                **request.parameters
            )
            return ToolExecuteResponse(
                status=result.status.value,
                data=result.data,
                error=result.error,
                metadata=result.metadata
            )
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolExecuteResponse(
                status="error",
                error=str(e)
            )
    
    @router.get("/tools")
    async def list_tools() -> ToolListResponse:
        """List all available tools."""
        tools_info = []
        
        for category in tool_registry._categories:
            for tool_name in tool_registry.list_tools(category):
                tool = tool_registry.get_tool(tool_name)
                if tool:
                    schema = tool.get_schema()
                    tools_info.append(ToolInfo(
                        name=tool_name,
                        category=category,
                        description=tool.description,
                        parameters=schema.get("function", {}).get("parameters", {}),
                        timeout=tool.timeout
                    ))
        
        # Add MCP tools if available
        if mcp_tools:
            for schema in mcp_tools.get_schemas():
                func_info = schema.get("function", {})
                tools_info.append(ToolInfo(
                    name=func_info.get("name", "unknown"),
                    category="mcp_legacy",
                    description=func_info.get("description", ""),
                    parameters=func_info.get("parameters", {}),
                    timeout=30.0
                ))
        
        return ToolListResponse(
            tools=tools_info,
            total_count=len(tools_info),
            categories=list(tool_registry._categories.keys())
        )
    
    @router.get("/stats")
    async def get_stats() -> ToolStatsResponse:
        """Get tool usage statistics."""
        stats = tool_registry.get_stats()
        return ToolStatsResponse(
            total_tools=stats["total_tools"],
            categories=stats["categories"],
            tools=stats["tools"]
        )
    
    @router.post("/stats/reset")
    async def reset_stats() -> Dict[str, str]:
        """Reset tool usage statistics."""
        tool_registry.reset_stats()
        return {"status": "success", "message": "Statistics reset"}
    
    @router.get("/tools/{tool_name}")
    async def get_tool_info(tool_name: str) -> ToolInfo:
        """Get information about a specific tool."""
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        schema = tool.get_schema()
        
        # Find category
        category = "unknown"
        for cat, tools in tool_registry._categories.items():
            if tool_name in tools:
                category = cat
                break
        
        return ToolInfo(
            name=tool_name,
            category=category,
            description=tool.description,
            parameters=schema.get("function", {}).get("parameters", {}),
            timeout=tool.timeout
        )
    
    @router.post("/tools/{tool_name}/execute")
    async def execute_specific_tool(
        tool_name: str,
        parameters: Dict[str, Any] = {}
    ) -> ToolExecuteResponse:
        """Execute a specific tool by name."""
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        try:
            result = await tool_registry.execute_tool(tool_name, **parameters)
            return ToolExecuteResponse(
                status=result.status.value,
                data=result.data,
                error=result.error,
                metadata=result.metadata
            )
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return ToolExecuteResponse(
                status="error",
                error=str(e)
            )
    
    return router

# OpenAI-compatible router
def create_openai_router(tool_registry, vllm_client):
    """Create OpenAI-compatible API router."""
    router = APIRouter()
    
    @router.post("/v1/chat/completions")
    async def chat_completions(request: CompletionRequest) -> ChatResponse:
        """OpenAI-compatible chat completions endpoint."""
        import time
        import uuid
        
        messages = request.messages
        
        try:
            # Call vLLM
            if request.tools:
                response = await vllm_client.chat(
                    messages=messages,
                    tools=request.tools,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
            else:
                response = await vllm_client.chat(
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
            
            # Handle tool calls if present
            msg = response["choices"][0]["message"]
            
            if "tool_calls" in msg and msg["tool_calls"]:
                # Process tool calls
                for tool_call in msg["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])
                    
                    # Execute tool
                    tool_result = await tool_registry.execute_tool(tool_name, **tool_args)
                    
                    # Add tool response to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(tool_result.data if tool_result.status.value == "success" else {"error": tool_result.error})
                    })
                
                # Get final response
                final_response = await vllm_client.chat(
                    messages=messages,
                    tools=request.tools if request.tools else None,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
                
                return ChatResponse(
                    id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    object="chat.completion",
                    created=int(time.time()),
                    model=request.model,
                    choices=final_response["choices"],
                    usage=final_response.get("usage")
                )
            else:
                # Return direct response
                return ChatResponse(
                    id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                    object="chat.completion",
                    created=int(time.time()),
                    model=request.model,
                    choices=response["choices"],
                    usage=response.get("usage")
                )
                
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router