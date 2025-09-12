"""단순 채팅용 FastAPI 백엔드"""

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

try:
    # LangChain integration (optional at import time)
    from langchain_openai import ChatOpenAI
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.tools import tool
    _LANGCHAIN_AVAILABLE = True
except Exception:
    _LANGCHAIN_AVAILABLE = False

settings = get_settings()
_level_name = (settings.log_level or "INFO").upper()
_level = getattr(logging, _level_name, logging.INFO)
logging.basicConfig(level=_level, format=settings.log_format)
logger = logging.getLogger(__name__)

app = FastAPI(title="VLLM Chat Backend", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vllm_client: Optional[VLLMClient] = None
tool_registry: Optional[ToolRegistry] = None
langchain_agent: Optional[Any] = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자 메시지")


class ChatResponse(BaseModel):
    response: str = Field(..., description="AI 응답")


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
    
    logger.info(f"Initialized {len(registry.list_tools())} tools in {len(registry._categories)} categories")
    return registry


@app.on_event("startup")
async def startup() -> None:
    global vllm_client, tool_registry, langchain_agent
    config = get_vllm_config()
    vllm_client = VLLMClient(
        config["base_url"],
        config["model"],
        max_tokens=config.get("max_tokens", 1000),
        temperature=config.get("temperature", 0.7),
        timeout=config.get("timeout", 60),
    )
    
    # Initialize tool registry
    tool_registry = initialize_tools()
    
    # Initialize LangChain agent backed by vLLM's OpenAI-compatible API
    if _LANGCHAIN_AVAILABLE:
        # vLLM exposes OpenAI-compatible API, so set base_url and dummy key
        llm = ChatOpenAI(
            api_key="unused",
            base_url=f"{config['base_url']}/v1",
            model=config["model"],
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 60),
        )

        # Wrap MCPTools methods as LangChain tools
        # Create LangChain tools from all available tools
        tools = []
        
        # Add legacy tools
        @tool("http_request")
        async def lc_http_request(
            method: str,
            url: str,
            headers: Optional[Dict[str, str]] = None,
            query: Optional[Dict[str, Any]] = None,
            json_body: Annotated[Optional[Any], Field(alias="json")] = None,
            timeout_s: int = 5,
        ) -> str:
            """Make HTTP requests to internal/external APIs."""
            return await mcp_tools.execute_tool(
                "http_request",
                method=method,
                url=url,
                headers=headers,
                query=query,
                json=json_body,
                timeout_s=timeout_s,
            )

        @tool("time_now")
        async def lc_time_now(timezone: str = "UTC") -> str:
            """Get current time in specified timezone."""
            return await mcp_tools.execute_tool("time_now", timezone=timezone)

        tools = [lc_http_request, lc_time_now]
        
        # Add new registry tools
        registry_schemas = mcp_tools.tool_registry.get_openai_schemas(max_safety_level="safe")
        for schema in registry_schemas:
            func_info = schema["function"]
            tool_name = func_info["name"]
            tool_description = func_info["description"]
            
            # Create a dynamic LangChain tool
            async def make_registry_tool(name: str, desc: str):
                @tool(name)
                async def registry_tool(**kwargs) -> str:
                    return await mcp_tools.execute_tool(name, **kwargs)
                registry_tool.__doc__ = desc
                return registry_tool
            
            registry_tool = await make_registry_tool(tool_name, tool_description)
            tools.append(registry_tool)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "간결한 한국어로 답하고 필요 시 도구를 사용하라.\n\n사용 가능한 도구: {tool_names}\n\n{tools}"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        langchain_agent = AgentExecutor(
            agent=create_react_agent(llm=llm, tools=tools, prompt=prompt),
            tools=tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=6,
        )


@app.on_event("shutdown")
async def shutdown() -> None:
    if vllm_client:
        await vllm_client.close()
    # LangChain agent has no explicit close


SYSTEM_PROMPT = "한국어로 간결하게 답해."


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not vllm_client or not mcp_tools:
        raise HTTPException(status_code=500, detail="Server not initialized")

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.message},
    ]
    try:
        # 일반 채팅에서는 tools 없이 시도
        response = await vllm_client.chat(messages)
        msg = response["choices"][0]["message"]
        logger.debug("model message: %s", msg)

        if "tool_calls" in msg and msg["tool_calls"]:
            messages.append(msg)
            for call in msg["tool_calls"]:
                try:
                    name = call["function"]["name"]
                    args = call["function"].get("arguments") or "{}"
                    call_id = call.get("id", "unknown")
                    
                    # JSON 파싱 안전하게 처리
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
                    
                    # Use enhanced tool execution
                    try:
                        result = await mcp_tools.execute_tool(name, **params)
                        
                        # 결과를 문자열로 변환
                        if not isinstance(result, str):
                            result = str(result)
                            
                    except Exception as e:
                        logger.error(f"Tool execution error for {name}: {e}")
                        result = f"Tool execution failed: {e}"
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "name": name,
                        "content": result,
                    })
                    
                except Exception as e:
                    logger.error(f"Tool call processing error: {e}")
                    # 기본 오류 응답 추가
                    messages.append({
                        "role": "tool", 
                        "tool_call_id": call.get("id", "error"),
                        "name": call.get("function", {}).get("name", "unknown"),
                        "content": f"Tool call processing failed: {e}"
                    })
            logger.debug("messages before follow-up: %s", [m.get("role") for m in messages])
            followup = await vllm_client.chat(messages)
            final = followup["choices"][0]["message"].get("content", "")
            return ChatResponse(response=final)
        else:
            content = msg.get("content")
            if content is None:
                content = "죄송합니다. 응답을 생성할 수 없습니다."
            return ChatResponse(response=content)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Chat processing failed")


@app.post("/api/agent_chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest) -> ChatResponse:
    """LangChain 기반 에이전트와 채팅 (ReAct + Tools)"""
    if not _LANGCHAIN_AVAILABLE:
        raise HTTPException(status_code=500, detail="LangChain not installed")
    if not langchain_agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    try:
        result = await langchain_agent.ainvoke({"input": request.message})
        output = result.get("output") if isinstance(result, dict) else str(result)
        return ChatResponse(response=output or "")
    except Exception as e:
        logger.error(f"Agent chat error: {e}")
        raise HTTPException(status_code=500, detail="Agent chat failed")


@app.get("/api/tools")
async def get_tools(
    category: Optional[str] = None,
    safety_level: Optional[str] = None,
    detailed: bool = False
) -> dict:
    """등록된 도구 목록 반환"""
    if not mcp_tools:
        raise HTTPException(status_code=500, detail="Server not initialized")
    
    # Get tool information
    tool_info = mcp_tools.get_tool_info()
    
    if detailed:
        # Get detailed information including schemas
        registry_tools = mcp_tools.tool_registry.list_tools(
            category=category,
            safety_level=safety_level,
            include_schemas=True
        )
        
        # Get legacy tools
        legacy_schemas = [
            {
                "name": "http_request",
                "description": "사내/외부 HTTP API 호출",
                "category": "network",
                "safety_level": "safe",
                "requires_confirmation": False
            },
            {
                "name": "time_now", 
                "description": "지정된 시간대의 현재 시각을 ISO 형식으로 반환",
                "category": "utility",
                "safety_level": "safe",
                "requires_confirmation": False
            }
        ]
        
        return {
            "tool_info": tool_info,
            "legacy_tools": legacy_schemas,
            "registry_tools": registry_tools,
            "total_count": len(legacy_schemas) + len(registry_tools)
        }
    else:
        # Simple list for backward compatibility
        schemas = mcp_tools.get_schemas()
        tools_info = []
        
        for schema in schemas:
            func_info = schema["function"]
            tools_info.append({
                "name": func_info["name"],
                "description": func_info["description"],
                "parameters": func_info.get("parameters", {})
            })
        
        return {
            "tools": tools_info,
            "count": len(tools_info),
            "tool_info": tool_info
        }


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

