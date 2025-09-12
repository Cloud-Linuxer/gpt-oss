"""System information and monitoring tools."""

import os
import platform
import psutil
import socket
from typing import Any, Dict, List, Optional
import logging

from .base import Tool, ToolResult, ToolStatus

logger = logging.getLogger(__name__)


class SystemInfoTool(Tool):
    """Tool for getting system information."""
    
    def __init__(self):
        """Initialize system info tool."""
        super().__init__(
            name="system_info",
            description="Get system information (OS, CPU, memory, disk)",
            timeout=5.0
        )
    
    async def execute(self, info_type: str = "all") -> ToolResult:
        """Get system information."""
        try:
            info = {}
            
            if info_type in ["all", "os"]:
                info["os"] = {
                    "system": platform.system(),
                    "node": platform.node(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version()
                }
            
            if info_type in ["all", "cpu"]:
                info["cpu"] = {
                    "physical_cores": psutil.cpu_count(logical=False),
                    "logical_cores": psutil.cpu_count(logical=True),
                    "usage_percent": psutil.cpu_percent(interval=1),
                    "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None
                }
            
            if info_type in ["all", "memory"]:
                mem = psutil.virtual_memory()
                info["memory"] = {
                    "total_gb": round(mem.total / (1024**3), 2),
                    "available_gb": round(mem.available / (1024**3), 2),
                    "used_gb": round(mem.used / (1024**3), 2),
                    "percent": mem.percent
                }
            
            if info_type in ["all", "disk"]:
                disk = psutil.disk_usage('/')
                info["disk"] = {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": disk.percent
                }
            
            if info_type in ["all", "network"]:
                info["network"] = {
                    "hostname": socket.gethostname(),
                    "interfaces": []
                }
                for interface, addrs in psutil.net_if_addrs().items():
                    for addr in addrs:
                        if addr.family == socket.AF_INET:
                            info["network"]["interfaces"].append({
                                "interface": interface,
                                "ip": addr.address,
                                "netmask": addr.netmask
                            })
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=info
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
                        "info_type": {
                            "type": "string",
                            "description": "Type of information to retrieve",
                            "enum": ["all", "os", "cpu", "memory", "disk", "network"],
                            "default": "all"
                        }
                    },
                    "required": []
                }
            }
        }


class ProcessListTool(Tool):
    """Tool for listing running processes."""
    
    def __init__(self):
        """Initialize process list tool."""
        super().__init__(
            name="process_list",
            description="List running processes",
            timeout=5.0
        )
    
    async def execute(self, sort_by: str = "cpu", limit: int = 10) -> ToolResult:
        """List processes."""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "cpu_percent": pinfo['cpu_percent'],
                        "memory_percent": round(pinfo['memory_percent'], 2)
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort processes
            if sort_by == "cpu":
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            elif sort_by == "name":
                processes.sort(key=lambda x: x['name'])
            
            # Limit results
            processes = processes[:limit]
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=processes,
                metadata={"count": len(processes), "sort_by": sort_by}
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
                        "sort_by": {
                            "type": "string",
                            "description": "Sort processes by",
                            "enum": ["cpu", "memory", "name"],
                            "default": "cpu"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of processes to return",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 10
                        }
                    },
                    "required": []
                }
            }
        }


class EnvironmentTool(Tool):
    """Tool for getting environment variables."""
    
    def __init__(self, allowed_vars: List[str] = None):
        """Initialize environment tool."""
        super().__init__(
            name="env_get",
            description="Get environment variables",
            timeout=2.0
        )
        # Whitelist of safe environment variables
        self.allowed_vars = allowed_vars or [
            "PATH", "HOME", "USER", "SHELL", "PWD", "LANG",
            "PYTHON_PATH", "NODE_ENV", "PORT", "HOST"
        ]
    
    async def execute(self, var_name: Optional[str] = None) -> ToolResult:
        """Get environment variables."""
        try:
            if var_name:
                # Get specific variable
                if var_name not in self.allowed_vars:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error=f"Access denied: {var_name} is not in allowed variables list"
                    )
                
                value = os.environ.get(var_name)
                if value is None:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error=f"Environment variable {var_name} not found"
                    )
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={var_name: value}
                )
            else:
                # Get all allowed variables
                env_vars = {}
                for var in self.allowed_vars:
                    if var in os.environ:
                        env_vars[var] = os.environ[var]
                
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=env_vars,
                    metadata={"count": len(env_vars)}
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
                        "var_name": {
                            "type": "string",
                            "description": "Name of environment variable to get (optional)"
                        }
                    },
                    "required": []
                }
            }
        }