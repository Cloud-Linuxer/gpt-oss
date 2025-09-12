"""Enhanced tool implementations with extensible registry system."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from zoneinfo import ZoneInfo
import httpx
from tools import (
    ToolRegistry, 
    FileReadTool, FileWriteTool, FileListTool,
    SystemInfoTool, ProcessListTool, EnvironmentTool,
    CalculatorTool, StatisticsTool,
    JSONParseTool, JSONQueryTool, DataTransformTool
)

logger = logging.getLogger(__name__)


class MCPTools:
    """Enhanced tools with extensible registry system."""

    def __init__(self) -> None:
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.tool_registry = get_registry()
        
        # Register all built-in tools
        self._register_builtin_tools()
        
        # Legacy method mapping for backward compatibility
        self._legacy_methods = {
            'http_request': self.http_request,
            'time_now': self.time_now
        }

    def _register_builtin_tools(self) -> None:
        """Register all built-in tool categories."""
        try:
            self.tool_registry.register_tool(FileOperationsTool())
            self.tool_registry.register_tool(MathematicalTool())
            self.tool_registry.register_tool(SystemInfoTool())
            self.tool_registry.register_tool(DataProcessingTool())
            self.tool_registry.register_tool(ValidationTool())
            logger.info("Registered all built-in tools successfully")
        except Exception as e:
            logger.error(f"Failed to register built-in tools: {e}")

    async def close(self) -> None:
        await self.http_client.aclose()

    async def http_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        query: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        timeout_s: int = 5,
    ) -> str:
        """Call an HTTP API and return the first 1000 chars of the response."""
        try:
            resp = await self.http_client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=query,
                json=json,
                timeout=timeout_s,
            )
            resp.raise_for_status()
            return resp.text[:1000]
        except Exception as e:  # pragma: no cover - network dependent
            logger.error("http_request error: %s", e)
            return f"http_request failed: {e}"

    async def time_now(self, timezone: str = "UTC") -> str:
        """Return current time for the given timezone in ISO format."""
        try:
            now = datetime.now(ZoneInfo(timezone))
            return now.isoformat()
        except Exception as e:  # pragma: no cover - tz dependent
            logger.error("time_now error: %s", e)
            return f"time_now failed: {e}"

    def get_schemas(self, max_safety_level: str = "restricted") -> List[Dict[str, Any]]:
        """Return JSON schemas for available tools."""
        # Get schemas from registry
        registry_schemas = self.tool_registry.get_openai_schemas(max_safety_level=max_safety_level)
        
        # Add legacy tool schemas for backward compatibility
        legacy_schemas = [
            {
                "type": "function",
                "function": {
                    "name": "http_request",
                    "description": "사내/외부 HTTP API 호출",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "method": {
                                "type": "string",
                                "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                            },
                            "url": {"type": "string", "format": "uri"},
                            "headers": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                            "query": {
                                "type": "object",
                                "additionalProperties": {},
                            },
                            "json": {"type": ["object", "array", "null"]},
                            "timeout_s": {
                                "type": "number",
                                "minimum": 1,
                                "maximum": 30,
                            },
                        },
                        "required": ["method", "url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "time_now",
                    "description": "지정된 시간대의 현재 시각을 ISO 형식으로 반환",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "timezone": {
                                "type": "string",
                                "default": "UTC",
                            }
                        },
                        "required": [],
                    },
                },
            },
        ]
        
        return legacy_schemas + registry_schemas

    async def execute_tool(self, name: str, **kwargs) -> str:
        """Execute a tool by name with parameters."""
        # Check legacy methods first for backward compatibility
        if name in self._legacy_methods:
            try:
                result = await self._legacy_methods[name](**kwargs)
                return str(result)
            except Exception as e:
                logger.error(f"Legacy tool execution error for {name}: {e}")
                return f"Tool execution failed: {e}"
        
        # Use registry for new tools
        tool_result = await self.tool_registry.execute_tool(name, **kwargs)
        return str(tool_result)

    def get_tool_info(self) -> Dict[str, Any]:
        """Get information about all available tools."""
        registry_stats = self.tool_registry.get_stats()
        legacy_tools = list(self._legacy_methods.keys())
        
        return {
            "legacy_tools": legacy_tools,
            "registry_tools": registry_stats,
            "total_tools": len(legacy_tools) + registry_stats["total_tools"],
            "categories": registry_stats["categories"]
        }

