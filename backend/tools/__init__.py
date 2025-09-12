"""Tool system for backend."""

from .base import Tool, ToolRegistry, ToolResult
from .file_tools import FileReadTool, FileWriteTool, FileListTool
from .system_tools import SystemInfoTool, ProcessListTool, EnvironmentTool
from .data_tools_simple import JSONParseTool, JSONQueryTool, DataTransformTool
from .math_tools import CalculatorTool, StatisticsTool
from .web_tools import WebScrapeTool, APIRequestTool
from .database_tools import DatabaseQueryTool, DatabaseExecuteTool
from .time_tool import TimeTool

# Global registry instance
_global_registry = None

def get_registry():
    """Get or create global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry

__all__ = [
    "Tool",
    "ToolRegistry",
    "ToolResult",
    "get_registry",
    "FileReadTool",
    "FileWriteTool",
    "FileListTool",
    "SystemInfoTool",
    "ProcessListTool",
    "EnvironmentTool",
    "JSONParseTool",
    "JSONQueryTool",
    "DataTransformTool",
    "CalculatorTool",
    "StatisticsTool",
    "WebScrapeTool",
    "APIRequestTool",
    "DatabaseQueryTool",
    "DatabaseExecuteTool",
    "TimeTool",
]