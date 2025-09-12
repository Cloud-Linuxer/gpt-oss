"""Enhanced FastAPI backend with comprehensive tool system."""

import json
import asyncio
import logging
from typing import Annotated, Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import get_vllm_config, get_settings
from vllm_client import VLLMClient
from version import __version__

# Import new tool system
from tools import (
    ToolRegistry,
    FileReadTool, FileWriteTool, FileListTool,
    SystemInfoTool, ProcessListTool, EnvironmentTool,
    CalculatorTool, StatisticsTool,
    JSONParseTool, JSONQueryTool, DataTransformTool,
    APIRequestTool, WebScrapeTool,
    DatabaseQueryTool, DatabaseExecuteTool
)

# Import legacy MCP tools for backwards compatibility
from mcp_tools import MCPTools

try:
    # LangChain integration (optional)
    from langchain_openai import ChatOpenAI
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.tools import tool as langchain_tool
    _LANGCHAIN_AVAILABLE = True
except Exception:
    _LANGCHAIN_AVAILABLE = False

settings = get_settings()
_level_name = (settings.log_level or "INFO").upper()
_level = getattr(logging, _level_name, logging.INFO)
logging.basicConfig(level=_level, format=settings.log_format)
logger = logging.getLogger(__name__)

app = FastAPI(title="VLLM Chat Backend with Tools", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vllm_client: Optional[VLLMClient] = None
tool_registry: Optional[ToolRegistry] = None
mcp_tools: Optional[MCPTools] = None  # Keep for backwards compatibility
langchain_agent: Optional[Any] = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자 메시지")
    use_tools: bool = Field(default=True, description="도구 사용 여부")


class ChatResponse(BaseModel):
    response: str = Field(..., description="AI 응답")
    tools_used: Optional[List[str]] = Field(default=None, description="사용된 도구 목록")


class ToolExecuteRequest(BaseModel):
    tool_name: str = Field(..., description="도구 이름")
    parameters: Dict[str, Any] = Field(default={}, description="도구 파라미터")


class ToolExecuteResponse(BaseModel):
    status: str = Field(..., description="실행 상태")
    data: Optional[Any] = Field(default=None, description="실행 결과")
    error: Optional[str] = Field(default=None, description="오류 메시지")


def initialize_tool_registry() -> ToolRegistry:
    """Initialize and configure tool registry."""
    registry = ToolRegistry()
    
    # Register file tools
    registry.register(FileReadTool(), category="file")
    registry.register(FileWriteTool(), category="file")
    registry.register(FileListTool(), category="file")
    
    # Register system tools
    registry.register(SystemInfoTool(), category="system")
    registry.register(ProcessListTool(), category="system")
    registry.register(EnvironmentTool(), category="system")
    
    # Register math tools
    registry.register(CalculatorTool(), category="math")
    registry.register(StatisticsTool(), category="math")
    
    # Register data tools
    registry.register(JSONParseTool(), category="data")
    registry.register(JSONQueryTool(), category="data")
    registry.register(DataTransformTool(), category="data")
    
    # Register web tools
    registry.register(APIRequestTool(), category="web")
    registry.register(WebScrapeTool(), category="web")
    
    # Register database tools (placeholders)
    registry.register(DatabaseQueryTool(), category="database")
    registry.register(DatabaseExecuteTool(), category="database")
    
    logger.info(f"Registered {len(registry.list_tools())} tools")
    return registry


@app.on_event("startup")
async def startup() -> None:
    global vllm_client, tool_registry, mcp_tools, langchain_agent
    
    # Initialize vLLM client
    config = get_vllm_config()
    vllm_client = VLLMClient(
        config["base_url"],
        config["model"],
        max_tokens=config.get("max_tokens", 1000),
        temperature=config.get("temperature", 0.7),
        timeout=config.get("timeout", 60),
    )
    
    # Initialize tool registry
    tool_registry = initialize_tool_registry()
    
    # Initialize legacy MCP tools for backwards compatibility
    mcp_tools = MCPTools()
    
    # Initialize LangChain agent if available
    if _LANGCHAIN_AVAILABLE:
        llm = ChatOpenAI(
            api_key="unused",
            base_url=f"{config['base_url']}/v1",
            model=config["model"],
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 60),
        )
        
        # Create LangChain tools from registry
        langchain_tools = []
        for tool_name in tool_registry.list_tools():
            tool_obj = tool_registry.get_tool(tool_name)
            
            @langchain_tool(name=tool_name)
            async def lc_tool_wrapper(**kwargs) -> str:
                """Execute tool through registry."""
                result = await tool_registry.execute_tool(tool_name, **kwargs)
                return result.to_string()
            
            # Fix the name binding issue
            lc_tool_wrapper.name = tool_name
            lc_tool_wrapper.description = tool_obj.description
            langchain_tools.append(lc_tool_wrapper)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "한국어로 답하고 필요 시 도구를 사용하라.\n\n사용 가능한 도구: {tool_names}\n\n{tools}"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        langchain_agent = AgentExecutor(
            agent=create_react_agent(llm=llm, tools=langchain_tools, prompt=prompt),
            tools=langchain_tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=6,
        )


@app.on_event("shutdown")
async def shutdown() -> None:
    if vllm_client:
        await vllm_client.close()
    if mcp_tools:
        await mcp_tools.close()


SYSTEM_PROMPT = "한국어로 간결하게 답해. 필요한 경우 도구를 사용할 수 있습니다."


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Enhanced chat endpoint with new tool system."""
    if not vllm_client or not tool_registry:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    tools_used = []
    
    # Prepare tool schemas for the model if tools are enabled
    tool_schemas = []
    if request.use_tools:
        tool_schemas = tool_registry.get_schemas()
        # Also add legacy MCP tool schemas
        if mcp_tools:
            tool_schemas.extend(mcp_tools.get_schemas())
    
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.message},
    ]
    
    try:
        # Call vLLM with tools if enabled
        if request.use_tools and tool_schemas:
            response = await vllm_client.chat(messages, tools=tool_schemas)
        else:
            response = await vllm_client.chat(messages)
        
        msg = response["choices"][0]["message"]
        logger.debug("model message: %s", msg)
        
        # Handle tool calls
        if "tool_calls" in msg and msg["tool_calls"]:
            messages.append(msg)
            
            for call in msg["tool_calls"]:
                try:
                    name = call["function"]["name"]
                    args = call["function"].get("arguments") or "{}"
                    call_id = call.get("id", "unknown")
                    
                    # Parse arguments
                    try:
                        params = json.loads(args)
                    except json.JSONDecodeError as e:
                        result = f"Invalid JSON arguments: {e}"
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call_id,
                            "content": result,
                        })
                        continue
                    
                    # Try new tool registry first
                    tool = tool_registry.get_tool(name)
                    if tool:
                        tool_result = await tool_registry.execute_tool(name, **params)
                        result = tool_result.to_string()
                        tools_used.append(name)
                    else:
                        # Fall back to legacy MCP tools
                        func = getattr(mcp_tools, name, None)
                        if func:
                            if asyncio.iscoroutinefunction(func):
                                result = await func(**params)
                            else:
                                result = func(**params)
                            
                            if not isinstance(result, str):
                                result = str(result)
                            tools_used.append(f"mcp_{name}")
                        else:
                            result = f"Unknown tool: {name}"
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": name,
                        "content": result,
                    })
                    
                except Exception as e:
                    logger.error(f"Tool call processing error: {e}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id", "error"),
                        "name": call.get("function", {}).get("name", "unknown"),
                        "content": f"Tool call processing failed: {e}"
                    })
            
            # Get follow-up response
            if request.use_tools and tool_schemas:
                followup = await vllm_client.chat(messages, tools=tool_schemas)
            else:
                followup = await vllm_client.chat(messages)
            
            final = followup["choices"][0]["message"].get("content", "")
            return ChatResponse(response=final, tools_used=tools_used if tools_used else None)
        else:
            content = msg.get("content", "죄송합니다. 응답을 생성할 수 없습니다.")
            return ChatResponse(response=content, tools_used=None)
            
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat processing failed")


@app.post("/api/tools/execute", response_model=ToolExecuteResponse)
async def execute_tool(request: ToolExecuteRequest) -> ToolExecuteResponse:
    """Direct tool execution endpoint."""
    if not tool_registry:
        raise HTTPException(status_code=500, detail="Tool registry not initialized")
    
    try:
        result = await tool_registry.execute_tool(request.tool_name, **request.parameters)
        return ToolExecuteResponse(
            status=result.status.value,
            data=result.data,
            error=result.error
        )
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return ToolExecuteResponse(
            status="error",
            error=str(e)
        )


@app.get("/api/tools")
async def get_tools() -> dict:
    """Get information about available tools."""
    if not tool_registry:
        raise HTTPException(status_code=500, detail="Tool registry not initialized")
    
    tools_info = []
    
    # Get tools from registry
    for category in tool_registry._categories:
        for tool_name in tool_registry.list_tools(category):
            tool = tool_registry.get_tool(tool_name)
            if tool:
                schema = tool.get_schema()
                tools_info.append({
                    "name": tool_name,
                    "category": category,
                    "description": tool.description,
                    "parameters": schema["function"].get("parameters", {})
                })
    
    # Add legacy MCP tools
    if mcp_tools:
        for schema in mcp_tools.get_schemas():
            func_info = schema["function"]
            tools_info.append({
                "name": func_info["name"],
                "category": "legacy_mcp",
                "description": func_info["description"],
                "parameters": func_info.get("parameters", {})
            })
    
    return {
        "tools": tools_info,
        "count": len(tools_info),
        "categories": list(tool_registry._categories.keys()) + ["legacy_mcp"]
    }


@app.get("/api/tools/stats")
async def get_tool_stats() -> dict:
    """Get tool usage statistics."""
    if not tool_registry:
        raise HTTPException(status_code=500, detail="Tool registry not initialized")
    
    return tool_registry.get_stats()


@app.post("/api/tools/reset-stats")
async def reset_tool_stats() -> dict:
    """Reset tool usage statistics."""
    if not tool_registry:
        raise HTTPException(status_code=500, detail="Tool registry not initialized")
    
    tool_registry.reset_stats()
    return {"status": "success", "message": "Tool statistics reset"}


@app.post("/api/agent_chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest) -> ChatResponse:
    """LangChain-based agent chat with enhanced tools."""
    if not _LANGCHAIN_AVAILABLE:
        raise HTTPException(status_code=500, detail="LangChain not installed")
    if not langchain_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        result = await langchain_agent.ainvoke({"input": request.message})
        output = result.get("output") if isinstance(result, dict) else str(result)
        
        # Try to extract used tools from agent execution
        tools_used = []
        if "intermediate_steps" in result:
            for step in result["intermediate_steps"]:
                if len(step) >= 2 and hasattr(step[0], "tool"):
                    tools_used.append(step[0].tool)
        
        return ChatResponse(
            response=output or "",
            tools_used=tools_used if tools_used else None
        )
    except Exception as e:
        logger.error(f"Agent chat error: {e}")
        raise HTTPException(status_code=500, detail="Agent chat failed")


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "tools_available": len(tool_registry.list_tools()) if tool_registry else 0,
        "vllm_connected": vllm_client is not None
    }


@app.get("/")
async def root() -> dict:
    return {
        "service": "VLLM Chat Backend with Enhanced Tools",
        "version": __version__,
        "endpoints": [
            "/api/chat",
            "/api/agent_chat",
            "/api/tools",
            "/api/tools/execute",
            "/api/tools/stats",
            "/health"
        ]
    }