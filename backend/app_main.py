#!/usr/bin/env python3
"""Main FastAPI application with comprehensive tool system."""

import logging
import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import get_vllm_config, get_settings
from vllm_client import VLLMClient
from version import __version__

# Import tool system
from tools import (
    ToolRegistry,
    FileReadTool, FileWriteTool, FileListTool,
    SystemInfoTool, ProcessListTool, EnvironmentTool,
    CalculatorTool, StatisticsTool,
    JSONParseTool, JSONQueryTool, DataTransformTool,
    APIRequestTool, WebScrapeTool,
    DatabaseQueryTool, DatabaseExecuteTool
)

# Import API routes
from api_routes import create_api_router, create_openai_router

# Setup logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format=settings.log_format
)
logger = logging.getLogger(__name__)

# Global instances
vllm_client: Optional[VLLMClient] = None
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
    
    logger.info(f"Initialized {len(registry.list_tools())} tools in {len(registry._categories)} categories")
    return registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global vllm_client, tool_registry
    
    # Startup
    logger.info("Starting application...")
    
    # Initialize vLLM client
    config = get_vllm_config()
    vllm_client = VLLMClient(
        config["base_url"],
        config["model"],
        max_tokens=config.get("max_tokens", 1000),
        temperature=config.get("temperature", 0.7),
        timeout=config.get("timeout", 60),
    )
    logger.info(f"vLLM client initialized: {config['base_url']}")
    
    # Initialize tools
    tool_registry = initialize_tools()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if vllm_client:
        await vllm_client.close()


# Create FastAPI app
app = FastAPI(
    title="GPT-OSS Backend with Tools",
    description="Backend service for GPT-OSS with comprehensive tool system",
    version=__version__,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
@app.on_event("startup")
async def mount_routers():
    """Mount API routers after initialization."""
    if tool_registry and vllm_client:
        # Tool API routes
        tool_router = create_api_router(tool_registry, vllm_client)
        app.include_router(tool_router, prefix="/api/tools", tags=["Tools"])
        
        # OpenAI-compatible routes
        openai_router = create_openai_router(tool_registry, vllm_client)
        app.include_router(openai_router, tags=["OpenAI Compatible"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "GPT-OSS Backend",
        "version": __version__,
        "status": "online",
        "endpoints": {
            "tools": {
                "list": "/api/tools/tools",
                "execute": "/api/tools/execute",
                "stats": "/api/tools/stats",
                "info": "/api/tools/tools/{tool_name}"
            },
            "openai": {
                "chat": "/v1/chat/completions"
            },
            "health": "/health"
        }
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if vllm_client and tool_registry else "initializing",
        "vllm_connected": vllm_client is not None,
        "tools_available": len(tool_registry.list_tools()) if tool_registry else 0,
        "version": __version__
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    # Run with uvicorn when executed directly
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "app_main:app",
        host=host,
        port=port,
        reload=True,
        log_level=settings.log_level.lower()
    )