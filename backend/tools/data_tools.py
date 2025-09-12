"""Data processing and transformation tools."""

import json
import csv
import io
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import jq
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
                # Basic schema validation (could use jsonschema library for more complex validation)
                errors = []
                
                # Check required fields
                if "required" in validate_schema:
                    for field in validate_schema["required"]:
                        if field not in data:
                            errors.append(f"Missing required field: {field}")
                
                # Check types
                if "properties" in validate_schema:
                    for field, schema in validate_schema["properties"].items():
                        if field in data:
                            expected_type = schema.get("type")
                            if expected_type:
                                actual_type = type(data[field]).__name__
                                type_map = {
                                    "string": "str",
                                    "number": ["int", "float"],
                                    "boolean": "bool",
                                    "array": "list",
                                    "object": "dict"
                                }
                                
                                if expected_type in type_map:
                                    expected = type_map[expected_type]
                                    if isinstance(expected, list):
                                        if actual_type not in expected:
                                            errors.append(f"Field {field}: expected {expected_type}, got {actual_type}")
                                    elif actual_type != expected:
                                        errors.append(f"Field {field}: expected {expected_type}, got {actual_type}")
                
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
    """Tool for querying JSON data with JQ expressions."""
    
    def __init__(self):
        """Initialize JSON query tool."""
        super().__init__(
            name="json_query",
            description="Query JSON data using JQ expressions",
            timeout=5.0
        )
    
    async def execute(self, data: Union[str, Dict, List], query: str) -> ToolResult:
        """Query JSON data."""
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
            
            # Execute JQ query
            result = jq.compile(query).input(data).all()
            
            # Handle single result vs multiple
            if len(result) == 1:
                result = result[0]
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=result,
                metadata={"query": query}
            )
            
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"JQ query error: {str(e)}"
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
                        "query": {
                            "type": "string",
                            "description": "JQ query expression (e.g., '.items[] | select(.price > 100)')"
                        }
                    },
                    "required": ["data", "query"]
                }
            }
        }


class DataTransformTool(Tool):
    """Tool for data transformation and conversion."""
    
    def __init__(self):
        """Initialize data transform tool."""
        super().__init__(
            name="data_transform",
            description="Transform data between formats (JSON, CSV, DataFrame)",
            timeout=10.0
        )
    
    async def execute(self, data: Any, from_format: str, to_format: str,
                     options: Optional[Dict] = None) -> ToolResult:
        """Transform data between formats."""
        try:
            options = options or {}
            
            # Parse input data based on format
            if from_format == "json":
                if isinstance(data, str):
                    df_data = json.loads(data)
                else:
                    df_data = data
                    
                if isinstance(df_data, list):
                    df = pd.DataFrame(df_data)
                elif isinstance(df_data, dict):
                    df = pd.DataFrame([df_data])
                else:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error="JSON data must be array or object"
                    )
                    
            elif from_format == "csv":
                if isinstance(data, str):
                    df = pd.read_csv(io.StringIO(data), **options.get("read_options", {}))
                else:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error="CSV data must be string"
                    )
                    
            elif from_format == "dataframe":
                if isinstance(data, pd.DataFrame):
                    df = data
                else:
                    df = pd.DataFrame(data)
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Unknown from_format: {from_format}"
                )
            
            # Convert to target format
            if to_format == "json":
                orient = options.get("orient", "records")
                result = df.to_json(orient=orient, indent=2)
                
            elif to_format == "csv":
                index = options.get("index", False)
                result = df.to_csv(index=index)
                
            elif to_format == "dataframe":
                result = df.to_dict("records")
                
            elif to_format == "html":
                index = options.get("index", False)
                result = df.to_html(index=index)
                
            elif to_format == "markdown":
                index = options.get("index", False)
                result = df.to_markdown(index=index)
                
            elif to_format == "summary":
                # Provide data summary
                result = {
                    "shape": df.shape,
                    "columns": df.columns.tolist(),
                    "dtypes": df.dtypes.to_dict(),
                    "head": df.head(5).to_dict("records"),
                    "description": df.describe().to_dict() if df.select_dtypes(include='number').shape[1] > 0 else None,
                    "null_counts": df.isnull().sum().to_dict()
                }
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
                    "to_format": to_format,
                    "rows": len(df),
                    "columns": len(df.columns)
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
                            "enum": ["json", "csv", "dataframe"]
                        },
                        "to_format": {
                            "type": "string",
                            "description": "Output format",
                            "enum": ["json", "csv", "dataframe", "html", "markdown", "summary"]
                        },
                        "options": {
                            "type": "object",
                            "description": "Format-specific options"
                        }
                    },
                    "required": ["data", "from_format", "to_format"]
                }
            }
        }