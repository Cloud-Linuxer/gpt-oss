"""Mathematical and calculation tools."""

import math
import statistics
from typing import Any, Dict, List, Union
import numpy as np
import logging

from .base import Tool, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class CalculatorTool(Tool):
    """Tool for mathematical calculations."""
    
    def __init__(self):
        """Initialize calculator tool."""
        super().__init__(
            name="calculator",
            description="Perform mathematical calculations",
            timeout=5.0
        )
    
    async def execute(self, expression: str = None, 
                     operation: str = None,
                     values: List[Union[int, float]] = None) -> ToolResult:
        """Perform calculation."""
        try:
            if expression:
                # Evaluate mathematical expression (safely)
                # Only allow safe operations
                allowed_names = {
                    k: v for k, v in math.__dict__.items() 
                    if not k.startswith("_")
                }
                allowed_names.update({
                    "abs": abs, "round": round, "min": min, "max": max,
                    "sum": sum, "len": len, "pow": pow
                })
                
                # Evaluate expression
                result = eval(expression, {"__builtins__": {}}, allowed_names)
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "expression": expression,
                        "result": result
                    }
                )
            
            elif operation and values:
                # Perform specific operation
                if operation == "add":
                    result = sum(values)
                elif operation == "subtract":
                    result = values[0] - sum(values[1:]) if len(values) > 1 else values[0]
                elif operation == "multiply":
                    result = 1
                    for v in values:
                        result *= v
                elif operation == "divide":
                    result = values[0]
                    for v in values[1:]:
                        if v == 0:
                            return ToolResult(
                                status=ToolStatus.ERROR,
                                error="Division by zero"
                            )
                        result /= v
                elif operation == "power":
                    if len(values) != 2:
                        return ToolResult(
                            status=ToolStatus.ERROR,
                            error="Power operation requires exactly 2 values"
                        )
                    result = values[0] ** values[1]
                elif operation == "sqrt":
                    if len(values) != 1:
                        return ToolResult(
                            status=ToolStatus.ERROR,
                            error="Square root requires exactly 1 value"
                        )
                    if values[0] < 0:
                        return ToolResult(
                            status=ToolStatus.ERROR,
                            error="Cannot take square root of negative number"
                        )
                    result = math.sqrt(values[0])
                elif operation == "log":
                    if len(values) == 1:
                        result = math.log(values[0])
                    elif len(values) == 2:
                        result = math.log(values[0], values[1])
                    else:
                        return ToolResult(
                            status=ToolStatus.ERROR,
                            error="Log requires 1 or 2 values"
                        )
                else:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error=f"Unknown operation: {operation}"
                    )
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "operation": operation,
                        "values": values,
                        "result": result
                    }
                )
            else:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error="Provide either 'expression' or both 'operation' and 'values'"
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
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 2 * 3')"
                        },
                        "operation": {
                            "type": "string",
                            "description": "Mathematical operation",
                            "enum": ["add", "subtract", "multiply", "divide", "power", "sqrt", "log"]
                        },
                        "values": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Values to perform operation on"
                        }
                    },
                    "required": []
                }
            }
        }


class StatisticsTool(Tool):
    """Tool for statistical calculations."""
    
    def __init__(self):
        """Initialize statistics tool."""
        super().__init__(
            name="statistics",
            description="Perform statistical calculations on data",
            timeout=5.0
        )
    
    async def execute(self, data: List[Union[int, float]], 
                     operations: List[str] = None) -> ToolResult:
        """Perform statistical calculations."""
        try:
            if not data:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error="No data provided"
                )
            
            # Default to all operations if none specified
            if not operations:
                operations = ["mean", "median", "mode", "std", "variance", "min", "max", "sum"]
            
            results = {}
            
            for op in operations:
                try:
                    if op == "mean":
                        results["mean"] = statistics.mean(data)
                    elif op == "median":
                        results["median"] = statistics.median(data)
                    elif op == "mode":
                        try:
                            results["mode"] = statistics.mode(data)
                        except statistics.StatisticsError:
                            results["mode"] = "No unique mode"
                    elif op == "std":
                        if len(data) > 1:
                            results["std"] = statistics.stdev(data)
                        else:
                            results["std"] = 0
                    elif op == "variance":
                        if len(data) > 1:
                            results["variance"] = statistics.variance(data)
                        else:
                            results["variance"] = 0
                    elif op == "min":
                        results["min"] = min(data)
                    elif op == "max":
                        results["max"] = max(data)
                    elif op == "sum":
                        results["sum"] = sum(data)
                    elif op == "count":
                        results["count"] = len(data)
                    elif op == "range":
                        results["range"] = max(data) - min(data)
                    elif op == "percentiles":
                        results["percentiles"] = {
                            "25th": np.percentile(data, 25),
                            "50th": np.percentile(data, 50),
                            "75th": np.percentile(data, 75),
                            "90th": np.percentile(data, 90),
                            "95th": np.percentile(data, 95),
                            "99th": np.percentile(data, 99)
                        }
                    else:
                        results[op] = f"Unknown operation: {op}"
                except Exception as e:
                    results[op] = f"Error: {str(e)}"
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=results,
                metadata={"data_points": len(data)}
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
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Numerical data to analyze"
                        },
                        "operations": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["mean", "median", "mode", "std", "variance", 
                                        "min", "max", "sum", "count", "range", "percentiles"]
                            },
                            "description": "Statistical operations to perform"
                        }
                    },
                    "required": ["data"]
                }
            }
        }