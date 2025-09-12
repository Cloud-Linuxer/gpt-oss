"""File operation tools with safety constraints."""

import os
import glob
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiofiles
import logging

from .base import Tool, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class FileReadTool(Tool):
    """Tool for reading files with safety constraints."""
    
    def __init__(self, allowed_paths: List[str] = None, max_size_mb: float = 10):
        """Initialize file read tool."""
        super().__init__(
            name="file_read",
            description="Read contents of a file",
            timeout=10.0
        )
        self.allowed_paths = allowed_paths or ["/home/gpt-oss/", "/tmp/"]
        self.max_size_mb = max_size_mb
    
    def _is_allowed_path(self, path: str) -> bool:
        """Check if path is allowed."""
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(os.path.abspath(allowed)) 
                  for allowed in self.allowed_paths)
    
    async def execute(self, file_path: str, encoding: str = "utf-8") -> ToolResult:
        """Read file contents."""
        try:
            # Security check
            if not self._is_allowed_path(file_path):
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Access denied: {file_path} is outside allowed paths"
                )
            
            # Check file exists
            if not os.path.exists(file_path):
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"File not found: {file_path}"
                )
            
            # Check file size
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > self.max_size_mb:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"File too large: {size_mb:.2f}MB > {self.max_size_mb}MB"
                )
            
            # Read file
            async with aiofiles.open(file_path, mode='r', encoding=encoding) as f:
                content = await f.read()
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=content,
                metadata={"file_path": file_path, "size_bytes": os.path.getsize(file_path)}
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
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding",
                            "default": "utf-8"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }


class FileWriteTool(Tool):
    """Tool for writing files with safety constraints."""
    
    def __init__(self, allowed_paths: List[str] = None, max_size_mb: float = 10):
        """Initialize file write tool."""
        super().__init__(
            name="file_write",
            description="Write content to a file",
            timeout=10.0
        )
        self.allowed_paths = allowed_paths or ["/home/gpt-oss/", "/tmp/"]
        self.max_size_mb = max_size_mb
    
    def _is_allowed_path(self, path: str) -> bool:
        """Check if path is allowed."""
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(os.path.abspath(allowed)) 
                  for allowed in self.allowed_paths)
    
    async def execute(self, file_path: str, content: str, 
                     mode: str = "w", encoding: str = "utf-8") -> ToolResult:
        """Write content to file."""
        try:
            # Security check
            if not self._is_allowed_path(file_path):
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Access denied: {file_path} is outside allowed paths"
                )
            
            # Check content size
            size_mb = len(content.encode(encoding)) / (1024 * 1024)
            if size_mb > self.max_size_mb:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Content too large: {size_mb:.2f}MB > {self.max_size_mb}MB"
                )
            
            # Validate mode
            if mode not in ["w", "a", "x"]:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Invalid mode: {mode}. Use 'w', 'a', or 'x'"
                )
            
            # Create directory if needed
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # Write file
            async with aiofiles.open(file_path, mode=mode, encoding=encoding) as f:
                await f.write(content)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=f"Successfully wrote {len(content)} characters to {file_path}",
                metadata={"file_path": file_path, "size_bytes": len(content.encode(encoding))}
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
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        },
                        "mode": {
                            "type": "string",
                            "description": "Write mode: 'w' (overwrite), 'a' (append), 'x' (exclusive)",
                            "enum": ["w", "a", "x"],
                            "default": "w"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding",
                            "default": "utf-8"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            }
        }


class FileListTool(Tool):
    """Tool for listing files in a directory."""
    
    def __init__(self, allowed_paths: List[str] = None):
        """Initialize file list tool."""
        super().__init__(
            name="file_list",
            description="List files in a directory",
            timeout=5.0
        )
        self.allowed_paths = allowed_paths or ["/home/gpt-oss/", "/tmp/"]
    
    def _is_allowed_path(self, path: str) -> bool:
        """Check if path is allowed."""
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(os.path.abspath(allowed)) 
                  for allowed in self.allowed_paths)
    
    async def execute(self, directory: str, pattern: str = "*", 
                     recursive: bool = False) -> ToolResult:
        """List files in directory."""
        try:
            # Security check
            if not self._is_allowed_path(directory):
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Access denied: {directory} is outside allowed paths"
                )
            
            # Check directory exists
            if not os.path.exists(directory):
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Directory not found: {directory}"
                )
            
            if not os.path.isdir(directory):
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Not a directory: {directory}"
                )
            
            # List files
            if recursive:
                pattern = os.path.join(directory, "**", pattern)
                files = glob.glob(pattern, recursive=True)
            else:
                pattern = os.path.join(directory, pattern)
                files = glob.glob(pattern)
            
            # Get file info
            file_info = []
            for file_path in files:
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    file_info.append({
                        "path": file_path,
                        "name": os.path.basename(file_path),
                        "size": stat.st_size,
                        "modified": stat.st_mtime
                    })
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=file_info,
                metadata={"directory": directory, "count": len(file_info)}
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
                        "directory": {
                            "type": "string",
                            "description": "Directory path to list files from"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "File pattern to match (e.g., '*.py')",
                            "default": "*"
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Search recursively in subdirectories",
                            "default": False
                        }
                    },
                    "required": ["directory"]
                }
            }
        }