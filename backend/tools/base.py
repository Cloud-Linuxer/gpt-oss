"""Base classes for tool system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging
import json
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Tool execution status."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    TIMEOUT = "timeout"


@dataclass
class ToolResult:
    """Result from tool execution."""
    status: ToolStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata or {}
        }
    
    def to_string(self) -> str:
        """Convert to string for LLM consumption."""
        if self.status == ToolStatus.SUCCESS:
            if isinstance(self.data, str):
                return self.data
            return json.dumps(self.data, ensure_ascii=False, indent=2)
        elif self.status == ToolStatus.ERROR:
            return f"Error: {self.error}"
        elif self.status == ToolStatus.PARTIAL:
            return f"Partial result: {self.data}\nWarning: {self.error}"
        else:
            return f"Timeout: {self.error}"


class Tool(ABC):
    """Base class for all tools."""
    
    def __init__(self, name: str, description: str, timeout: float = 30.0):
        """Initialize tool."""
        self.name = name
        self.description = description
        self.timeout = timeout
        self._usage_count = 0
        self._last_used = None
        self._success_count = 0
        self._error_count = 0
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for the tool."""
        pass
    
    async def safe_execute(self, **kwargs) -> ToolResult:
        """Execute with timeout and error handling."""
        self._usage_count += 1
        self._last_used = datetime.now()
        
        try:
            # Apply timeout
            result = await asyncio.wait_for(
                self.execute(**kwargs),
                timeout=self.timeout
            )
            if result.status == ToolStatus.SUCCESS:
                self._success_count += 1
            else:
                self._error_count += 1
            return result
            
        except asyncio.TimeoutError:
            self._error_count += 1
            logger.error(f"Tool {self.name} timed out after {self.timeout}s")
            return ToolResult(
                status=ToolStatus.TIMEOUT,
                error=f"Tool execution timed out after {self.timeout} seconds"
            )
        except Exception as e:
            self._error_count += 1
            logger.error(f"Tool {self.name} failed with error: {e}")
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "name": self.name,
            "usage_count": self._usage_count,
            "success_count": self._success_count,
            "error_count": self._error_count,
            "last_used": self._last_used.isoformat() if self._last_used else None,
            "success_rate": (
                self._success_count / self._usage_count 
                if self._usage_count > 0 else 0
            )
        }
    
    def validate_params(self, params: Dict[str, Any]) -> Optional[str]:
        """Validate parameters against schema."""
        schema = self.get_schema()
        required = schema.get("function", {}).get("parameters", {}).get("required", [])
        properties = schema.get("function", {}).get("parameters", {}).get("properties", {})
        
        # Check required parameters
        for req in required:
            if req not in params:
                return f"Missing required parameter: {req}"
        
        # Check parameter types (basic validation)
        for key, value in params.items():
            if key in properties:
                prop = properties[key]
                expected_type = prop.get("type")
                
                if expected_type == "string" and not isinstance(value, str):
                    return f"Parameter {key} must be a string"
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return f"Parameter {key} must be a number"
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return f"Parameter {key} must be a boolean"
                elif expected_type == "array" and not isinstance(value, list):
                    return f"Parameter {key} must be an array"
                elif expected_type == "object" and not isinstance(value, dict):
                    return f"Parameter {key} must be an object"
        
        return None


class ToolRegistry:
    """Registry for managing tools."""
    
    def __init__(self):
        """Initialize registry."""
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, tool: Tool, category: str = "general") -> None:
        """Register a tool."""
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} already registered, overwriting")
        
        self._tools[tool.name] = tool
        
        if category not in self._categories:
            self._categories[category] = []
        if tool.name not in self._categories[category]:
            self._categories[category].append(tool.name)
        
        logger.info(f"Registered tool: {tool.name} in category: {category}")
    
    def unregister(self, name: str) -> bool:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]
            # Remove from categories
            for category in self._categories.values():
                if name in category:
                    category.remove(name)
            logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """List all tool names, optionally filtered by category."""
        if category:
            return self._categories.get(category, [])
        return list(self._tools.keys())
    
    def get_schemas(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get schemas for all tools."""
        tool_names = self.list_tools(category)
        schemas = []
        for name in tool_names:
            tool = self._tools.get(name)
            if tool:
                schemas.append(tool.get_schema())
        return schemas
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Tool '{name}' not found"
            )
        
        # Validate parameters
        validation_error = tool.validate_params(kwargs)
        if validation_error:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=validation_error
            )
        
        # Execute tool
        return await tool.safe_execute(**kwargs)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all tools."""
        return {
            "total_tools": len(self._tools),
            "categories": list(self._categories.keys()),
            "tools": [tool.get_stats() for tool in self._tools.values()]
        }
    
    def reset_stats(self) -> None:
        """Reset statistics for all tools."""
        for tool in self._tools.values():
            tool._usage_count = 0
            tool._success_count = 0
            tool._error_count = 0
            tool._last_used = None