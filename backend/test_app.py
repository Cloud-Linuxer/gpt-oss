"""Simple test app with tools."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import logging
import sys
sys.path.insert(0, '/home/gpt-oss/backend')

from tools.base import ToolRegistry
from tools.file_tools import FileReadTool, FileWriteTool, FileListTool
from tools.system_tools import SystemInfoTool, ProcessListTool, EnvironmentTool
from tools.math_tools import CalculatorTool, StatisticsTool
from tools.data_tools_simple import JSONParseTool, JSONQueryTool, DataTransformTool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Tool System Test API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize tool registry
tool_registry = ToolRegistry()

@app.on_event("startup")
async def startup():
    """Initialize tools on startup."""
    tool_registry.register(FileReadTool(), category="file")
    tool_registry.register(FileWriteTool(), category="file")
    tool_registry.register(FileListTool(), category="file")
    tool_registry.register(SystemInfoTool(), category="system")
    tool_registry.register(ProcessListTool(), category="system")
    tool_registry.register(EnvironmentTool(), category="system")
    tool_registry.register(CalculatorTool(), category="math")
    tool_registry.register(StatisticsTool(), category="math")
    tool_registry.register(JSONParseTool(), category="data")
    tool_registry.register(JSONQueryTool(), category="data")
    tool_registry.register(DataTransformTool(), category="data")
    logger.info(f"Registered {len(tool_registry.list_tools())} tools")

class ToolRequest(BaseModel):
    tool_name: str
    parameters: dict = {}

class ToolResponse(BaseModel):
    status: str
    data: dict = None
    error: str = None

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Tool System Test API",
        "status": "running",
        "tools_available": len(tool_registry.list_tools())
    }

@app.get("/tools")
async def list_tools():
    """List available tools."""
    tools = []
    for name in tool_registry.list_tools():
        tool = tool_registry.get_tool(name)
        if tool:
            tools.append({
                "name": name,
                "description": tool.description,
                "timeout": tool.timeout
            })
    return {"tools": tools, "count": len(tools)}

@app.post("/execute")
async def execute_tool(request: ToolRequest):
    """Execute a tool."""
    try:
        result = await tool_registry.execute_tool(request.tool_name, **request.parameters)
        return {
            "status": result.status.value,
            "data": result.data,
            "error": result.error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get tool usage statistics."""
    return tool_registry.get_stats()

@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy", "tools": len(tool_registry.list_tools())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)