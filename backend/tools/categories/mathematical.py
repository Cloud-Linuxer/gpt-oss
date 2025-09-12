"""
Mathematical Operations Tools

Provides mathematical calculations and statistical operations.
"""

import math
import statistics
from typing import Dict, Any, List, Union
from ..base import BaseTool, ToolResult, ToolError


class MathematicalTool(BaseTool):
    """Mathematical calculations and statistical operations."""
    
    @property
    def name(self) -> str:
        return "mathematical"
    
    @property
    def description(self) -> str:
        return "Mathematical calculations: arithmetic, statistics, trigonometry"
    
    @property
    def category(self) -> str:
        return "computation"
    
    @property
    def safety_level(self) -> str:
        return "safe"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "add", "subtract", "multiply", "divide", "power", "sqrt", 
                        "sin", "cos", "tan", "log", "ln", "factorial",
                        "mean", "median", "mode", "stdev", "variance",
                        "min", "max", "sum", "abs", "round", "floor", "ceil"
                    ],
                    "description": "수학 연산 유형"
                },
                "values": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "계산할 숫자 배열"
                },
                "precision": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 15,
                    "description": "소수점 정밀도"
                },
                "angle_unit": {
                    "type": "string",
                    "enum": ["radians", "degrees"],
                    "default": "radians",
                    "description": "삼각함수 각도 단위"
                }
            },
            "required": ["operation", "values"]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        operation = kwargs.get("operation")
        values = kwargs.get("values", [])
        precision = kwargs.get("precision", 10)
        angle_unit = kwargs.get("angle_unit", "radians")
        
        if not values:
            return ToolResult(
                success=False,
                result=None,
                message="No values provided for calculation"
            )
        
        try:
            # Validate values
            numeric_values = [float(v) for v in values]
            
            # Perform operation
            result = await self._perform_operation(
                operation, numeric_values, precision, angle_unit
            )
            
            return ToolResult(
                success=True,
                result=result,
                message=f"Calculated {operation} with {len(values)} values",
                metadata={
                    "operation": operation,
                    "input_count": len(values),
                    "precision": precision
                }
            )
            
        except ValueError as e:
            return ToolResult(
                success=False,
                result=None,
                message=f"Invalid values for calculation: {str(e)}"
            )
        except Exception as e:
            raise ToolError(f"Mathematical operation failed: {str(e)}", self.name)
    
    async def _perform_operation(
        self, 
        operation: str, 
        values: List[float], 
        precision: int,
        angle_unit: str
    ) -> float:
        """Perform the specified mathematical operation."""
        
        # Basic arithmetic operations
        if operation == "add":
            result = sum(values)
        elif operation == "subtract":
            if len(values) < 2:
                raise ValueError("Subtraction requires at least 2 values")
            result = values[0]
            for v in values[1:]:
                result -= v
        elif operation == "multiply":
            result = 1
            for v in values:
                result *= v
        elif operation == "divide":
            if len(values) < 2:
                raise ValueError("Division requires at least 2 values")
            if any(v == 0 for v in values[1:]):
                raise ValueError("Division by zero")
            result = values[0]
            for v in values[1:]:
                result /= v
        elif operation == "power":
            if len(values) != 2:
                raise ValueError("Power operation requires exactly 2 values (base, exponent)")
            result = values[0] ** values[1]
        
        # Single value operations
        elif operation == "sqrt":
            if len(values) != 1:
                raise ValueError("Square root requires exactly 1 value")
            if values[0] < 0:
                raise ValueError("Cannot calculate square root of negative number")
            result = math.sqrt(values[0])
        elif operation == "abs":
            if len(values) != 1:
                raise ValueError("Absolute value requires exactly 1 value")
            result = abs(values[0])
        elif operation == "factorial":
            if len(values) != 1:
                raise ValueError("Factorial requires exactly 1 value")
            if values[0] < 0 or values[0] != int(values[0]):
                raise ValueError("Factorial requires non-negative integer")
            result = float(math.factorial(int(values[0])))
        elif operation == "ln":
            if len(values) != 1:
                raise ValueError("Natural logarithm requires exactly 1 value")
            if values[0] <= 0:
                raise ValueError("Logarithm requires positive number")
            result = math.log(values[0])
        elif operation == "log":
            if len(values) not in [1, 2]:
                raise ValueError("Logarithm requires 1 or 2 values (number, optional base)")
            if values[0] <= 0:
                raise ValueError("Logarithm requires positive number")
            base = values[1] if len(values) == 2 else 10
            if base <= 0 or base == 1:
                raise ValueError("Logarithm base must be positive and not equal to 1")
            result = math.log(values[0], base)
        
        # Trigonometric functions
        elif operation in ["sin", "cos", "tan"]:
            if len(values) != 1:
                raise ValueError(f"{operation} requires exactly 1 value")
            angle = values[0]
            if angle_unit == "degrees":
                angle = math.radians(angle)
            
            if operation == "sin":
                result = math.sin(angle)
            elif operation == "cos":
                result = math.cos(angle)
            else:  # tan
                result = math.tan(angle)
        
        # Rounding operations
        elif operation == "round":
            if len(values) != 1:
                raise ValueError("Round requires exactly 1 value")
            result = round(values[0], precision)
        elif operation == "floor":
            if len(values) != 1:
                raise ValueError("Floor requires exactly 1 value")
            result = math.floor(values[0])
        elif operation == "ceil":
            if len(values) != 1:
                raise ValueError("Ceil requires exactly 1 value")
            result = math.ceil(values[0])
        
        # Statistical operations
        elif operation == "mean":
            result = statistics.mean(values)
        elif operation == "median":
            result = statistics.median(values)
        elif operation == "mode":
            try:
                result = statistics.mode(values)
            except statistics.StatisticsError:
                # No unique mode
                result = float('nan')
        elif operation == "stdev":
            if len(values) < 2:
                raise ValueError("Standard deviation requires at least 2 values")
            result = statistics.stdev(values)
        elif operation == "variance":
            if len(values) < 2:
                raise ValueError("Variance requires at least 2 values")
            result = statistics.variance(values)
        
        # Aggregate operations
        elif operation == "min":
            result = min(values)
        elif operation == "max":
            result = max(values)
        elif operation == "sum":
            result = sum(values)
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        # Round result to specified precision
        if precision > 0 and not math.isnan(result) and not math.isinf(result):
            result = round(result, precision)
        
        return result