"""
Data Processing Tools

Provides data transformation, formatting, and processing capabilities.
"""

import json
import csv
import base64
import hashlib
import re
from io import StringIO
from typing import Dict, Any, List, Union, Optional
from datetime import datetime, timezone
from ..base import BaseTool, ToolResult, ToolError


class DataProcessingTool(BaseTool):
    """Data processing and transformation operations."""
    
    @property
    def name(self) -> str:
        return "data_processing"
    
    @property
    def description(self) -> str:
        return "Data processing: JSON, CSV, encoding, hashing, text manipulation"
    
    @property
    def category(self) -> str:
        return "processing"
    
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
                        "json_parse", "json_stringify", "json_validate",
                        "csv_parse", "csv_generate", "csv_to_json",
                        "base64_encode", "base64_decode",
                        "hash_md5", "hash_sha1", "hash_sha256",
                        "text_clean", "text_extract", "text_count",
                        "url_encode", "url_decode",
                        "format_date", "parse_date",
                        "regex_match", "regex_replace"
                    ],
                    "description": "데이터 처리 연산 유형"
                },
                "data": {
                    "type": "string",
                    "description": "처리할 데이터"
                },
                "options": {
                    "type": "object",
                    "description": "추가 옵션",
                    "additionalProperties": True
                }
            },
            "required": ["operation", "data"]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        operation = kwargs.get("operation")
        data = kwargs.get("data", "")
        options = kwargs.get("options", {})
        
        try:
            if operation.startswith("json_"):
                result = await self._handle_json_operation(operation, data, options)
            elif operation.startswith("csv_"):
                result = await self._handle_csv_operation(operation, data, options)
            elif operation.startswith("base64_"):
                result = await self._handle_base64_operation(operation, data, options)
            elif operation.startswith("hash_"):
                result = await self._handle_hash_operation(operation, data, options)
            elif operation.startswith("text_"):
                result = await self._handle_text_operation(operation, data, options)
            elif operation.startswith("url_"):
                result = await self._handle_url_operation(operation, data, options)
            elif operation.endswith("_date"):
                result = await self._handle_date_operation(operation, data, options)
            elif operation.startswith("regex_"):
                result = await self._handle_regex_operation(operation, data, options)
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    message=f"Unknown operation: {operation}"
                )
            
            return ToolResult(
                success=True,
                result=result,
                message=f"Completed {operation} operation",
                metadata={"operation": operation, "data_length": len(str(data))}
            )
            
        except Exception as e:
            raise ToolError(f"Data processing failed: {str(e)}", self.name)
    
    async def _handle_json_operation(self, operation: str, data: str, options: Dict[str, Any]) -> Any:
        """Handle JSON operations."""
        if operation == "json_parse":
            return json.loads(data)
        elif operation == "json_stringify":
            # Assume data is already parsed JSON
            indent = options.get("indent")
            ensure_ascii = options.get("ensure_ascii", True)
            return json.dumps(json.loads(data) if isinstance(data, str) else data, 
                            indent=indent, ensure_ascii=ensure_ascii)
        elif operation == "json_validate":
            try:
                json.loads(data)
                return {"valid": True, "message": "Valid JSON"}
            except json.JSONDecodeError as e:
                return {"valid": False, "error": str(e)}
    
    async def _handle_csv_operation(self, operation: str, data: str, options: Dict[str, Any]) -> Any:
        """Handle CSV operations."""
        if operation == "csv_parse":
            delimiter = options.get("delimiter", ",")
            has_header = options.get("has_header", True)
            
            csv_file = StringIO(data)
            reader = csv.reader(csv_file, delimiter=delimiter)
            rows = list(reader)
            
            if not rows:
                return []
            
            if has_header:
                headers = rows[0]
                return [dict(zip(headers, row)) for row in rows[1:]]
            else:
                return rows
        
        elif operation == "csv_generate":
            # Expect data to be JSON array
            json_data = json.loads(data) if isinstance(data, str) else data
            if not json_data:
                return ""
            
            delimiter = options.get("delimiter", ",")
            include_header = options.get("include_header", True)
            
            output = StringIO()
            
            if isinstance(json_data[0], dict):
                fieldnames = list(json_data[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
                
                if include_header:
                    writer.writeheader()
                writer.writerows(json_data)
            else:
                writer = csv.writer(output, delimiter=delimiter)
                writer.writerows(json_data)
            
            return output.getvalue()
        
        elif operation == "csv_to_json":
            csv_result = await self._handle_csv_operation("csv_parse", data, options)
            return json.dumps(csv_result, indent=options.get("indent"))
    
    async def _handle_base64_operation(self, operation: str, data: str, options: Dict[str, Any]) -> str:
        """Handle Base64 operations."""
        if operation == "base64_encode":
            encoding = options.get("encoding", "utf-8")
            return base64.b64encode(data.encode(encoding)).decode("ascii")
        elif operation == "base64_decode":
            encoding = options.get("encoding", "utf-8")
            return base64.b64decode(data).decode(encoding)
    
    async def _handle_hash_operation(self, operation: str, data: str, options: Dict[str, Any]) -> str:
        """Handle hashing operations."""
        encoding = options.get("encoding", "utf-8")
        data_bytes = data.encode(encoding)
        
        if operation == "hash_md5":
            return hashlib.md5(data_bytes).hexdigest()
        elif operation == "hash_sha1":
            return hashlib.sha1(data_bytes).hexdigest()
        elif operation == "hash_sha256":
            return hashlib.sha256(data_bytes).hexdigest()
    
    async def _handle_text_operation(self, operation: str, data: str, options: Dict[str, Any]) -> Any:
        """Handle text operations."""
        if operation == "text_clean":
            # Clean whitespace, remove special characters
            remove_extra_spaces = options.get("remove_extra_spaces", True)
            strip = options.get("strip", True)
            remove_special = options.get("remove_special", False)
            
            result = data
            if strip:
                result = result.strip()
            if remove_extra_spaces:
                result = re.sub(r'\s+', ' ', result)
            if remove_special:
                result = re.sub(r'[^\w\s]', '', result)
            
            return result
        
        elif operation == "text_extract":
            # Extract specific patterns
            pattern = options.get("pattern", r'\b\w+\b')  # Default: words
            flags = options.get("flags", 0)
            
            matches = re.findall(pattern, data, flags)
            return matches
        
        elif operation == "text_count":
            # Count various text metrics
            return {
                "characters": len(data),
                "characters_no_spaces": len(data.replace(" ", "")),
                "words": len(data.split()),
                "lines": len(data.splitlines()),
                "paragraphs": len([p for p in data.split("\n\n") if p.strip()])
            }
    
    async def _handle_url_operation(self, operation: str, data: str, options: Dict[str, Any]) -> str:
        """Handle URL operations."""
        import urllib.parse
        
        if operation == "url_encode":
            return urllib.parse.quote(data)
        elif operation == "url_decode":
            return urllib.parse.unquote(data)
    
    async def _handle_date_operation(self, operation: str, data: str, options: Dict[str, Any]) -> str:
        """Handle date operations."""
        if operation == "parse_date":
            input_format = options.get("input_format", "%Y-%m-%d")
            output_format = options.get("output_format", "%Y-%m-%d %H:%M:%S")
            
            try:
                # Try parsing with provided format
                dt = datetime.strptime(data, input_format)
            except ValueError:
                # Try common formats
                common_formats = [
                    "%Y-%m-%d",
                    "%Y-%m-%d %H:%M:%S",
                    "%d/%m/%Y",
                    "%m/%d/%Y",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%SZ"
                ]
                
                dt = None
                for fmt in common_formats:
                    try:
                        dt = datetime.strptime(data, fmt)
                        break
                    except ValueError:
                        continue
                
                if dt is None:
                    raise ValueError(f"Unable to parse date: {data}")
            
            return dt.strftime(output_format)
        
        elif operation == "format_date":
            # Assume data is ISO format or timestamp
            output_format = options.get("output_format", "%Y-%m-%d %H:%M:%S")
            timezone_name = options.get("timezone", "UTC")
            
            try:
                # Try as timestamp
                timestamp = float(data)
                dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            except ValueError:
                # Try as ISO format
                dt = datetime.fromisoformat(data.replace('Z', '+00:00'))
            
            return dt.strftime(output_format)
    
    async def _handle_regex_operation(self, operation: str, data: str, options: Dict[str, Any]) -> Any:
        """Handle regex operations."""
        pattern = options.get("pattern", "")
        if not pattern:
            raise ValueError("Pattern required for regex operations")
        
        flags = options.get("flags", 0)
        
        if operation == "regex_match":
            matches = re.findall(pattern, data, flags)
            return {
                "matches": matches,
                "count": len(matches),
                "has_matches": len(matches) > 0
            }
        
        elif operation == "regex_replace":
            replacement = options.get("replacement", "")
            count = options.get("count", 0)  # 0 means replace all
            
            result = re.sub(pattern, replacement, data, count=count, flags=flags)
            return result