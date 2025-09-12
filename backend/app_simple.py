#!/usr/bin/env python3
"""Simple tool server for Docker testing."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GPT-OSS Tool System", version="1.0.0")

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


class ToolExecuteRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = {}


@app.get("/")
async def root():
    return {
        "service": "Tool System Test API",
        "status": "running",
        "tools_available": len(tool_registry.list_tools()) if tool_registry else 0
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "tools": len(tool_registry.list_tools()) if tool_registry else 0
    }


@app.get("/tools")
async def get_tools():
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


@app.post("/execute")
async def execute_tool(request: ToolExecuteRequest):
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
        logger.error(f"Tool execution error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/stats")
async def get_stats():
    if not tool_registry:
        raise HTTPException(status_code=500, detail="Tool registry not initialized")
    
    return tool_registry.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")