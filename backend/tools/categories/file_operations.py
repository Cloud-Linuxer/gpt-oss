"""
File Operations Tools

Provides safe file system operations with security constraints.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..base import BaseTool, ToolResult, ToolError, SafetyMixin


class FileOperationsTool(BaseTool, SafetyMixin):
    """Safe file operations with security constraints."""
    
    def __init__(self):
        super().__init__()
        # Define safe directories (relative to backend root)
        self._safe_directories = {
            "/tmp",
            "/home/gpt-oss/backend/uploads",
            "/home/gpt-oss/backend/temp", 
            "/home/gpt-oss/backend/outputs"
        }
        # Maximum file size (10MB)
        self._max_file_size = 10 * 1024 * 1024
        # Allowed file extensions for reading
        self._allowed_read_extensions = {
            '.txt', '.json', '.csv', '.log', '.md', '.yaml', '.yml', 
            '.xml', '.ini', '.cfg', '.conf', '.py', '.js', '.html',
            '.css', '.sql', '.env'
        }
        # Forbidden patterns
        self._forbidden_patterns = [
            '..',  # Directory traversal
            '/etc/', '/var/', '/root/', '/home/',  # System directories
            'passwd', 'shadow', 'private', 'secret'  # Sensitive files
        ]
    
    @property
    def name(self) -> str:
        return "file_operations"
    
    @property
    def description(self) -> str:
        return "Safe file system operations: read, write, list, get info"
    
    @property
    def category(self) -> str:
        return "file_system"
    
    @property
    def safety_level(self) -> str:
        return "restricted"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "list", "info", "exists"],
                    "description": "파일 연산 유형"
                },
                "path": {
                    "type": "string",
                    "description": "파일 또는 디렉토리 경로"
                },
                "content": {
                    "type": "string",
                    "description": "쓰기 연산 시 파일 내용"
                },
                "encoding": {
                    "type": "string",
                    "default": "utf-8",
                    "description": "파일 인코딩"
                },
                "max_size": {
                    "type": "integer",
                    "default": 1024000,
                    "description": "읽기 시 최대 파일 크기"
                }
            },
            "required": ["operation", "path"]
        }
    
    def _validate_path(self, path: str) -> Path:
        """Validate and sanitize file path."""
        # Convert to Path object
        path_obj = Path(path).resolve()
        
        # Check for forbidden patterns
        path_str = str(path_obj)
        for pattern in self._forbidden_patterns:
            if pattern in path_str.lower():
                raise ToolError(f"Path contains forbidden pattern: {pattern}", self.name)
        
        # Check if path is within safe directories for write operations
        is_safe = False
        for safe_dir in self._safe_directories:
            try:
                path_obj.relative_to(Path(safe_dir).resolve())
                is_safe = True
                break
            except ValueError:
                continue
                
        if not is_safe:
            # For read operations, be more permissive but still check
            if path_str.startswith(('/etc', '/var', '/root')):
                raise ToolError(f"Access denied to system directory: {path_str}", self.name)
        
        return path_obj
    
    def _check_file_extension(self, path: Path, operation: str) -> None:
        """Check if file extension is allowed."""
        if operation == "read":
            suffix = path.suffix.lower()
            if suffix and suffix not in self._allowed_read_extensions:
                raise ToolError(f"File type not allowed for reading: {suffix}", self.name)
    
    async def execute(self, **kwargs) -> ToolResult:
        operation = kwargs.get("operation")
        path_str = kwargs.get("path", "")
        content = kwargs.get("content", "")
        encoding = kwargs.get("encoding", "utf-8")
        max_size = kwargs.get("max_size", 1024000)
        
        try:
            path = self._validate_path(path_str)
            
            if operation == "read":
                return await self._read_file(path, encoding, max_size)
            elif operation == "write":
                return await self._write_file(path, content, encoding)
            elif operation == "list":
                return await self._list_directory(path)
            elif operation == "info":
                return await self._get_file_info(path)
            elif operation == "exists":
                return await self._check_exists(path)
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    message=f"Unknown operation: {operation}"
                )
                
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"File operation failed: {str(e)}", self.name)
    
    async def _read_file(self, path: Path, encoding: str, max_size: int) -> ToolResult:
        """Read file content safely."""
        if not path.exists():
            return ToolResult(
                success=False,
                result=None,
                message=f"File does not exist: {path}"
            )
        
        if not path.is_file():
            return ToolResult(
                success=False,
                result=None,
                message=f"Path is not a file: {path}"
            )
        
        # Check file size
        file_size = path.stat().st_size
        if file_size > max_size:
            return ToolResult(
                success=False,
                result=None,
                message=f"File too large: {file_size} bytes (max: {max_size})"
            )
        
        # Check file extension
        self._check_file_extension(path, "read")
        
        try:
            content = path.read_text(encoding=encoding)
            return ToolResult(
                success=True,
                result=content,
                message=f"Read {len(content)} characters from {path.name}",
                metadata={
                    "file_size": file_size,
                    "encoding": encoding,
                    "path": str(path)
                }
            )
        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                result=None,
                message=f"Unable to decode file with encoding: {encoding}"
            )
    
    async def _write_file(self, path: Path, content: str, encoding: str) -> ToolResult:
        """Write content to file safely."""
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check content size
        content_size = len(content.encode(encoding))
        if content_size > self._max_file_size:
            return ToolResult(
                success=False,
                result=None,
                message=f"Content too large: {content_size} bytes (max: {self._max_file_size})"
            )
        
        try:
            path.write_text(content, encoding=encoding)
            return ToolResult(
                success=True,
                result=str(path),
                message=f"Wrote {len(content)} characters to {path.name}",
                metadata={
                    "content_size": content_size,
                    "encoding": encoding,
                    "path": str(path)
                }
            )
        except Exception as e:
            raise ToolError(f"Failed to write file: {str(e)}", self.name)
    
    async def _list_directory(self, path: Path) -> ToolResult:
        """List directory contents."""
        if not path.exists():
            return ToolResult(
                success=False,
                result=None,
                message=f"Directory does not exist: {path}"
            )
        
        if not path.is_dir():
            return ToolResult(
                success=False,
                result=None,
                message=f"Path is not a directory: {path}"
            )
        
        try:
            items = []
            for item in path.iterdir():
                item_info = {
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": item.stat().st_mtime
                }
                items.append(item_info)
            
            # Sort by type then name
            items.sort(key=lambda x: (x["type"] == "file", x["name"]))
            
            return ToolResult(
                success=True,
                result=items,
                message=f"Listed {len(items)} items in {path.name}",
                metadata={"path": str(path), "item_count": len(items)}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to list directory: {str(e)}", self.name)
    
    async def _get_file_info(self, path: Path) -> ToolResult:
        """Get file/directory information."""
        if not path.exists():
            return ToolResult(
                success=False,
                result=None,
                message=f"Path does not exist: {path}"
            )
        
        try:
            stat = path.stat()
            info = {
                "name": path.name,
                "path": str(path),
                "type": "directory" if path.is_dir() else "file",
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "permissions": oct(stat.st_mode)[-3:]
            }
            
            if path.is_file():
                info["extension"] = path.suffix
                # Calculate file hash for files under 1MB
                if stat.st_size < 1024 * 1024:
                    try:
                        content = path.read_bytes()
                        info["md5"] = hashlib.md5(content).hexdigest()
                    except:
                        pass
            
            return ToolResult(
                success=True,
                result=info,
                message=f"Got info for {path.name}",
                metadata={"path": str(path)}
            )
            
        except Exception as e:
            raise ToolError(f"Failed to get file info: {str(e)}", self.name)
    
    async def _check_exists(self, path: Path) -> ToolResult:
        """Check if path exists."""
        exists = path.exists()
        return ToolResult(
            success=True,
            result=exists,
            message=f"Path {'exists' if exists else 'does not exist'}: {path.name}",
            metadata={"path": str(path), "exists": exists}
        )