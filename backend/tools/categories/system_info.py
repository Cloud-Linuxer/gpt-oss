"""
System Information Tools

Provides safe system information retrieval.
"""

import os
import platform
import psutil
import socket
from datetime import datetime
from typing import Dict, Any
from ..base import BaseTool, ToolResult, ToolError


class SystemInfoTool(BaseTool):
    """System information retrieval with security constraints."""
    
    @property
    def name(self) -> str:
        return "system_info"
    
    @property
    def description(self) -> str:
        return "System information: CPU, memory, disk, network, process info"
    
    @property
    def category(self) -> str:
        return "system"
    
    @property
    def safety_level(self) -> str:
        return "safe"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "info_type": {
                    "type": "string",
                    "enum": [
                        "cpu", "memory", "disk", "network", "platform", 
                        "processes", "uptime", "load", "temperature"
                    ],
                    "description": "조회할 시스템 정보 유형"
                },
                "detailed": {
                    "type": "boolean",
                    "default": False,
                    "description": "상세 정보 포함 여부"
                }
            },
            "required": ["info_type"]
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        info_type = kwargs.get("info_type")
        detailed = kwargs.get("detailed", False)
        
        try:
            if info_type == "cpu":
                result = await self._get_cpu_info(detailed)
            elif info_type == "memory":
                result = await self._get_memory_info(detailed)
            elif info_type == "disk":
                result = await self._get_disk_info(detailed)
            elif info_type == "network":
                result = await self._get_network_info(detailed)
            elif info_type == "platform":
                result = await self._get_platform_info(detailed)
            elif info_type == "processes":
                result = await self._get_process_info(detailed)
            elif info_type == "uptime":
                result = await self._get_uptime_info()
            elif info_type == "load":
                result = await self._get_load_info()
            elif info_type == "temperature":
                result = await self._get_temperature_info()
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    message=f"Unknown info type: {info_type}"
                )
            
            return ToolResult(
                success=True,
                result=result,
                message=f"Retrieved {info_type} information",
                metadata={"info_type": info_type, "detailed": detailed}
            )
            
        except Exception as e:
            raise ToolError(f"System info retrieval failed: {str(e)}", self.name)
    
    async def _get_cpu_info(self, detailed: bool) -> Dict[str, Any]:
        """Get CPU information."""
        info = {
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
            "usage_percent": psutil.cpu_percent(interval=1),
            "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
        
        if detailed:
            info.update({
                "per_cpu_usage": psutil.cpu_percent(interval=1, percpu=True),
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
                "architecture": platform.machine(),
                "processor": platform.processor()
            })
        
        return info
    
    async def _get_memory_info(self, detailed: bool) -> Dict[str, Any]:
        """Get memory information."""
        virtual_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()
        
        info = {
            "total": virtual_mem.total,
            "available": virtual_mem.available,
            "used": virtual_mem.used,
            "percentage": virtual_mem.percent,
            "swap_total": swap_mem.total,
            "swap_used": swap_mem.used,
            "swap_percentage": swap_mem.percent
        }
        
        if detailed:
            info.update({
                "buffers": getattr(virtual_mem, 'buffers', 0),
                "cached": getattr(virtual_mem, 'cached', 0),
                "shared": getattr(virtual_mem, 'shared', 0),
                "swap_free": swap_mem.free,
                "swap_sin": swap_mem.sin,
                "swap_sout": swap_mem.sout
            })
        
        return info
    
    async def _get_disk_info(self, detailed: bool) -> Dict[str, Any]:
        """Get disk information."""
        partitions = psutil.disk_partitions()
        disk_info = []
        
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partition_info = {
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percentage": (usage.used / usage.total * 100) if usage.total > 0 else 0
                }
                
                if detailed:
                    partition_info["options"] = partition.opts
                
                disk_info.append(partition_info)
            except PermissionError:
                # Skip inaccessible partitions
                continue
        
        result = {"partitions": disk_info}
        
        if detailed:
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    result["io_stats"] = disk_io._asdict()
            except:
                pass
        
        return result
    
    async def _get_network_info(self, detailed: bool) -> Dict[str, Any]:
        """Get network information."""
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        network_info = {}
        for interface, addresses in interfaces.items():
            interface_info = {
                "addresses": [addr._asdict() for addr in addresses],
                "is_up": stats[interface].isup if interface in stats else False,
                "speed": stats[interface].speed if interface in stats else None
            }
            
            if detailed and interface in stats:
                interface_info.update({
                    "mtu": stats[interface].mtu,
                    "duplex": stats[interface].duplex.name if hasattr(stats[interface].duplex, 'name') else str(stats[interface].duplex)
                })
            
            network_info[interface] = interface_info
        
        result = {"interfaces": network_info}
        
        if detailed:
            try:
                net_io = psutil.net_io_counters()
                if net_io:
                    result["io_stats"] = net_io._asdict()
                
                connections = len(psutil.net_connections())
                result["active_connections"] = connections
            except:
                pass
        
        return result
    
    async def _get_platform_info(self, detailed: bool) -> Dict[str, Any]:
        """Get platform information."""
        info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": socket.gethostname(),
            "python_version": platform.python_version()
        }
        
        if detailed:
            info.update({
                "platform": platform.platform(),
                "architecture": platform.architecture(),
                "node": platform.node(),
                "uname": platform.uname()._asdict(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
            })
        
        return info
    
    async def _get_process_info(self, detailed: bool) -> Dict[str, Any]:
        """Get process information."""
        current_process = psutil.Process()
        
        info = {
            "current_pid": current_process.pid,
            "current_name": current_process.name(),
            "current_memory_percent": current_process.memory_percent(),
            "current_cpu_percent": current_process.cpu_percent(),
            "total_processes": len(psutil.pids())
        }
        
        if detailed:
            # Get top 10 processes by CPU usage
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage and take top 10
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            info["top_processes"] = processes[:10]
            
            info.update({
                "current_threads": current_process.num_threads(),
                "current_status": current_process.status(),
                "current_create_time": datetime.fromtimestamp(current_process.create_time()).isoformat()
            })
        
        return info
    
    async def _get_uptime_info(self) -> Dict[str, Any]:
        """Get system uptime information."""
        boot_time = psutil.boot_time()
        current_time = datetime.now().timestamp()
        uptime_seconds = current_time - boot_time
        
        return {
            "boot_time": datetime.fromtimestamp(boot_time).isoformat(),
            "uptime_seconds": uptime_seconds,
            "uptime_hours": uptime_seconds / 3600,
            "uptime_days": uptime_seconds / 86400
        }
    
    async def _get_load_info(self) -> Dict[str, Any]:
        """Get system load information."""
        if hasattr(os, 'getloadavg'):
            load1, load5, load15 = os.getloadavg()
            return {
                "load_1min": load1,
                "load_5min": load5,
                "load_15min": load15,
                "cpu_count": psutil.cpu_count()
            }
        else:
            return {"error": "Load average not available on this platform"}
    
    async def _get_temperature_info(self) -> Dict[str, Any]:
        """Get temperature information."""
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                return {"error": "Temperature sensors not available"}
            
            temp_info = {}
            for name, entries in temps.items():
                temp_info[name] = [
                    {
                        "label": entry.label or "Unknown",
                        "current": entry.current,
                        "high": entry.high,
                        "critical": entry.critical
                    }
                    for entry in entries
                ]
            
            return temp_info
            
        except AttributeError:
            return {"error": "Temperature monitoring not supported on this platform"}