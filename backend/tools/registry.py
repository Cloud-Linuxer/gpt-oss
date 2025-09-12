"""
Tool Registry System

Manages registration, discovery, and execution of tools.
Provides security controls and categorization.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set, Any, Type
from .base import BaseTool, ToolError, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all available tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, Set[str]] = {}
        self._safety_levels: Dict[str, Set[str]] = {
            "safe": set(),
            "restricted": set(), 
            "dangerous": set()
        }
        
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool in the registry."""
        name = tool.name
        
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")
            
        # Validate tool
        try:
            schema = tool.get_schema()
        except Exception as e:
            raise ValueError(f"Invalid tool '{name}': {e}") from e
            
        # Register tool
        self._tools[name] = tool
        
        # Update categories
        category = tool.category
        if category not in self._categories:
            self._categories[category] = set()
        self._categories[category].add(name)
        
        # Update safety levels
        safety_level = tool.safety_level
        if safety_level in self._safety_levels:
            self._safety_levels[safety_level].add(name)
            
        logger.info(f"Registered tool: {name} (category: {category}, safety: {safety_level})")
        
    def unregister_tool(self, name: str) -> None:
        """Unregister a tool from the registry."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' is not registered")
            
        tool = self._tools[name]
        
        # Remove from tools
        del self._tools[name]
        
        # Remove from categories
        category = tool.category
        self._categories[category].discard(name)
        if not self._categories[category]:
            del self._categories[category]
            
        # Remove from safety levels
        safety_level = tool.safety_level
        if safety_level in self._safety_levels:
            self._safety_levels[safety_level].discard(name)
            
        logger.info(f"Unregistered tool: {name}")
        
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a registered tool by name."""
        return self._tools.get(name)
        
    def list_tools(
        self, 
        category: Optional[str] = None,
        safety_level: Optional[str] = None,
        include_schemas: bool = False
    ) -> List[Dict[str, Any]]:
        """List available tools with optional filtering."""
        tools = self._tools.values()
        
        # Filter by category
        if category:
            tools = [t for t in tools if t.category == category]
            
        # Filter by safety level
        if safety_level:
            tools = [t for t in tools if t.safety_level == safety_level]
            
        result = []
        for tool in tools:
            tool_info = {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "safety_level": tool.safety_level,
                "requires_confirmation": tool.requires_confirmation
            }
            
            if include_schemas:
                tool_info["schema"] = tool.get_schema().dict()
                
            result.append(tool_info)
            
        return result
        
    def get_categories(self) -> List[str]:
        """Get all available tool categories."""
        return list(self._categories.keys())
        
    def get_tools_by_category(self, category: str) -> List[str]:
        """Get tool names in a specific category."""
        return list(self._categories.get(category, set()))
        
    def get_openai_schemas(
        self,
        category: Optional[str] = None,
        safety_level: Optional[str] = None,
        max_safety_level: str = "restricted"
    ) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible tool schemas."""
        # Define safety level hierarchy
        safety_hierarchy = ["safe", "restricted", "dangerous"]
        max_level_index = safety_hierarchy.index(max_safety_level)
        allowed_levels = safety_hierarchy[:max_level_index + 1]
        
        tools = self._tools.values()
        
        # Filter by category
        if category:
            tools = [t for t in tools if t.category == category]
            
        # Filter by safety level
        if safety_level:
            tools = [t for t in tools if t.safety_level == safety_level]
        else:
            tools = [t for t in tools if t.safety_level in allowed_levels]
            
        return [tool.get_openai_schema() for tool in tools]
        
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with parameters."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                result=None,
                message=f"Tool '{name}' not found",
                metadata={"available_tools": list(self._tools.keys())}
            )
            
        try:
            return await tool.safe_execute(**kwargs)
        except ToolError as e:
            return ToolResult(
                success=False,
                result=None,
                message=e.message,
                metadata=e.details
            )
            
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": len(self._tools),
            "categories": {cat: len(tools) for cat, tools in self._categories.items()},
            "safety_levels": {level: len(tools) for level, tools in self._safety_levels.items()},
            "tools_requiring_confirmation": len([
                t for t in self._tools.values() if t.requires_confirmation
            ])
        }


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(tool: BaseTool) -> None:
    """Register a tool in the global registry."""
    get_registry().register_tool(tool)


def auto_register_tools(module_name: str) -> None:
    """Auto-register all tools from a module."""
    import importlib
    import inspect
    
    try:
        module = importlib.import_module(module_name)
        registry = get_registry()
        
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseTool) and 
                obj != BaseTool):
                try:
                    tool_instance = obj()
                    registry.register_tool(tool_instance)
                except Exception as e:
                    logger.error(f"Failed to register tool {name}: {e}")
                    
    except ImportError as e:
        logger.error(f"Failed to import module {module_name}: {e}")