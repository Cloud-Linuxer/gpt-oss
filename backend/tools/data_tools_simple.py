"""Simple data processing tools without pandas dependency."""

import json
import csv
import io
from typing import Any, Dict, List, Optional, Union
import logging

from .base import Tool, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class JSONParseTool(Tool):
    """Tool for parsing and validating JSON."""
    
    def __init__(self):
        """Initialize JSON parse tool."""
        super().__init__(
            name="json_parse",
            description="Parse and validate JSON string",
            timeout=5.0
        )
    
    async def execute(self, json_string: str, validate_schema: Optional[Dict] = None) -> ToolResult:
        """Parse JSON string."""
        try:
            # Parse JSON
            data = json.loads(json_string)
            
            # Optional schema validation
            if validate_schema:
                # Basic schema validation
                errors = []
                
                # Check required fields
                if "required" in validate_schema:
                    for field in validate_schema["required"]:
                        if field not in data:
                            errors.append(f"Missing required field: {field}")
                
                if errors:
                    return ToolResult(
                        status=ToolStatus.PARTIAL,
                        data=data,
                        error="; ".join(errors)
                    )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=data,
                metadata={"type": type(data).__name__, "size": len(json_string)}
            )
            
        except json.JSONDecodeError as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"JSON parse error at line {e.lineno}, column {e.colno}: {e.msg}"
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "json_string": {
                            "type": "string",
                            "description": "JSON string to parse"
                        },
                        "validate_schema": {
                            "type": "object",
                            "description": "Optional JSON schema for validation"
                        }
                    },
                    "required": ["json_string"]
                }
            }
        }


class JSONQueryTool(Tool):
    """Simple JSON query tool."""
    
    def __init__(self):
        """Initialize JSON query tool."""
        super().__init__(
            name="json_query",
            description="Query JSON data with simple path expressions",
            timeout=5.0
        )
    
    async def execute(self, data: Union[str, Dict, List], path: str) -> ToolResult:
        """Query JSON data with simple path."""
        try:
            # Parse data if string
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError as e:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error=f"Invalid JSON data: {e}"
                    )
            
            # Simple path query (e.g., "users.0.name")
            result = data
            for key in path.split('.'):
                if isinstance(result, dict):
                    result = result.get(key)
                elif isinstance(result, list):
                    try:
                        idx = int(key)
                        result = result[idx]
                    except (ValueError, IndexError):
                        result = None
                else:
                    result = None
                
                if result is None:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error=f"Path not found: {path}"
                    )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=result,
                metadata={"path": path}
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": ["string", "object", "array"],
                            "description": "JSON data to query"
                        },
                        "path": {
                            "type": "string",
                            "description": "Simple path expression (e.g., 'users.0.name')"
                        }
                    },
                    "required": ["data", "path"]
                }
            }
        }


class DataTransformTool(Tool):
    """Simple data transformation tool."""
    
    def __init__(self):
        """Initialize data transform tool."""
        super().__init__(
            name="data_transform",
            description="Transform data between JSON and CSV formats",
            timeout=10.0
        )
    
    async def execute(self, data: Any, from_format: str, to_format: str) -> ToolResult:
        """Transform data between formats."""
        try:
            # Parse input data
            if from_format == "json":
                if isinstance(data, str):
                    parsed_data = json.loads(data)
                else:
                    parsed_data = data
                    
            elif from_format == "csv":
                if isinstance(data, str):
                    reader = csv.DictReader(io.StringIO(data))
                    parsed_data = list(reader)
                else:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error="CSV data must be string"
                    )
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Unknown from_format: {from_format}"
                )
            
            # Convert to target format
            if to_format == "json":
                result = json.dumps(parsed_data, indent=2)
                
            elif to_format == "csv":
                if isinstance(parsed_data, list) and len(parsed_data) > 0:
                    output = io.StringIO()
                    if isinstance(parsed_data[0], dict):
                        writer = csv.DictWriter(output, fieldnames=parsed_data[0].keys())
                        writer.writeheader()
                        writer.writerows(parsed_data)
                    else:
                        writer = csv.writer(output)
                        writer.writerows(parsed_data)
                    result = output.getvalue()
                else:
                    result = ""
                    
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Unknown to_format: {to_format}"
                )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=result,
                metadata={
                    "from_format": from_format,
                    "to_format": to_format
                }
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "description": "Data to transform"
                        },
                        "from_format": {
                            "type": "string",
                            "description": "Input format",
                            "enum": ["json", "csv"]
                        },
                        "to_format": {
                            "type": "string",
                            "description": "Output format",
                            "enum": ["json", "csv"]
                        }
                    },
                    "required": ["data", "from_format", "to_format"]
                }
            }
        }