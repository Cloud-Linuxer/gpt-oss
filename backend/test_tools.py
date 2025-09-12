#!/usr/bin/env python3
"""Test script for the new tool system."""

import asyncio
import json
import sys
import os
sys.path.insert(0, '/home/gpt-oss/backend')

from tools import (
    ToolRegistry,
    FileReadTool, FileWriteTool, FileListTool,
    SystemInfoTool, ProcessListTool, EnvironmentTool,
    CalculatorTool, StatisticsTool,
    JSONParseTool, JSONQueryTool, DataTransformTool
)


async def test_tools():
    """Test all tools."""
    print("=" * 80)
    print("TOOL SYSTEM TEST SUITE")
    print("=" * 80)
    
    # Initialize registry
    registry = ToolRegistry()
    
    # Register tools
    print("\n📋 Registering tools...")
    registry.register(FileReadTool(), category="file")
    registry.register(FileWriteTool(), category="file")
    registry.register(FileListTool(), category="file")
    registry.register(SystemInfoTool(), category="system")
    registry.register(ProcessListTool(), category="system")
    registry.register(EnvironmentTool(), category="system")
    registry.register(CalculatorTool(), category="math")
    registry.register(StatisticsTool(), category="math")
    registry.register(JSONParseTool(), category="data")
    registry.register(JSONQueryTool(), category="data")
    registry.register(DataTransformTool(), category="data")
    
    print(f"✅ Registered {len(registry.list_tools())} tools")
    print(f"📁 Categories: {list(registry._categories.keys())}")
    
    # Test 1: File List Tool
    print("\n" + "=" * 80)
    print("TEST 1: File List Tool")
    print("-" * 80)
    result = await registry.execute_tool("file_list", 
                                        directory="/home/gpt-oss/backend",
                                        pattern="*.py")
    print(f"Status: {result.status.value}")
    if result.status.value == "success":
        files = result.data
        print(f"Found {len(files)} Python files:")
        for f in files[:5]:  # Show first 5
            print(f"  - {f['name']} ({f['size']} bytes)")
    else:
        print(f"Error: {result.error}")
    
    # Test 2: File Write Tool
    print("\n" + "=" * 80)
    print("TEST 2: File Write Tool")
    print("-" * 80)
    test_content = "# Test file created by tool system\nHello from the tool system!\n"
    result = await registry.execute_tool("file_write",
                                        file_path="/tmp/test_tool_output.txt",
                                        content=test_content)
    print(f"Status: {result.status.value}")
    print(f"Result: {result.data}")
    
    # Test 3: File Read Tool
    print("\n" + "=" * 80)
    print("TEST 3: File Read Tool")
    print("-" * 80)
    result = await registry.execute_tool("file_read",
                                        file_path="/tmp/test_tool_output.txt")
    print(f"Status: {result.status.value}")
    if result.status.value == "success":
        print(f"Content:\n{result.data}")
    else:
        print(f"Error: {result.error}")
    
    # Test 4: System Info Tool
    print("\n" + "=" * 80)
    print("TEST 4: System Info Tool")
    print("-" * 80)
    result = await registry.execute_tool("system_info", info_type="all")
    print(f"Status: {result.status.value}")
    if result.status.value == "success":
        info = result.data
        print(f"OS: {info['os']['system']} {info['os']['release']}")
        print(f"CPU: {info['cpu']['logical_cores']} cores, {info['cpu']['usage_percent']}% usage")
        print(f"Memory: {info['memory']['used_gb']}/{info['memory']['total_gb']} GB ({info['memory']['percent']}%)")
        print(f"Disk: {info['disk']['used_gb']}/{info['disk']['total_gb']} GB ({info['disk']['percent']}%)")
    
    # Test 5: Process List Tool
    print("\n" + "=" * 80)
    print("TEST 5: Process List Tool")
    print("-" * 80)
    result = await registry.execute_tool("process_list", sort_by="cpu", limit=5)
    print(f"Status: {result.status.value}")
    if result.status.value == "success":
        processes = result.data
        print(f"Top {len(processes)} processes by CPU:")
        for p in processes:
            print(f"  - {p['name']} (PID: {p['pid']}, CPU: {p['cpu_percent']}%, Mem: {p['memory_percent']}%)")
    
    # Test 6: Calculator Tool
    print("\n" + "=" * 80)
    print("TEST 6: Calculator Tool")
    print("-" * 80)
    test_expressions = [
        "2 + 2 * 3",
        "sqrt(16)",
        "pow(2, 10)",
        "sin(3.14159/2)"
    ]
    for expr in test_expressions:
        result = await registry.execute_tool("calculator", expression=expr)
        if result.status.value == "success":
            print(f"  {expr} = {result.data['result']}")
        else:
            print(f"  {expr} = ERROR: {result.error}")
    
    # Test 7: Statistics Tool
    print("\n" + "=" * 80)
    print("TEST 7: Statistics Tool")
    print("-" * 80)
    test_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    result = await registry.execute_tool("statistics", 
                                        data=test_data,
                                        operations=["mean", "median", "std", "min", "max"])
    print(f"Status: {result.status.value}")
    if result.status.value == "success":
        stats = result.data
        print(f"Data: {test_data}")
        print(f"Statistics:")
        for key, value in stats.items():
            print(f"  - {key}: {value}")
    
    # Test 8: JSON Parse Tool
    print("\n" + "=" * 80)
    print("TEST 8: JSON Parse Tool")
    print("-" * 80)
    test_json = '{"name": "Tool System", "version": "1.0", "features": ["file", "system", "math"]}'
    result = await registry.execute_tool("json_parse", json_string=test_json)
    print(f"Status: {result.status.value}")
    if result.status.value == "success":
        print(f"Parsed JSON: {json.dumps(result.data, indent=2)}")
    
    # Test 9: JSON Query Tool
    print("\n" + "=" * 80)
    print("TEST 9: JSON Query Tool")
    print("-" * 80)
    test_data = {
        "users": [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35}
        ]
    }
    result = await registry.execute_tool("json_query",
                                        data=test_data,
                                        query=".users[] | select(.age > 25)")
    print(f"Status: {result.status.value}")
    if result.status.value == "success":
        print(f"Query result: {json.dumps(result.data, indent=2)}")
    
    # Test 10: Data Transform Tool
    print("\n" + "=" * 80)
    print("TEST 10: Data Transform Tool")
    print("-" * 80)
    csv_data = "name,age,city\nAlice,30,Seoul\nBob,25,Busan\nCharlie,35,Daegu"
    result = await registry.execute_tool("data_transform",
                                        data=csv_data,
                                        from_format="csv",
                                        to_format="json")
    print(f"Status: {result.status.value}")
    if result.status.value == "success":
        print(f"CSV to JSON:\n{result.data[:200]}...")  # Show first 200 chars
    
    # Test 11: Environment Tool
    print("\n" + "=" * 80)
    print("TEST 11: Environment Tool")
    print("-" * 80)
    result = await registry.execute_tool("env_get")
    print(f"Status: {result.status.value}")
    if result.status.value == "success":
        env_vars = result.data
        print(f"Available environment variables:")
        for key, value in list(env_vars.items())[:5]:  # Show first 5
            print(f"  - {key}: {value[:50]}...")  # Show first 50 chars
    
    # Test Statistics
    print("\n" + "=" * 80)
    print("TOOL USAGE STATISTICS")
    print("-" * 80)
    stats = registry.get_stats()
    print(f"Total tools: {stats['total_tools']}")
    print(f"Tool performance:")
    for tool_stat in stats['tools']:
        if tool_stat['usage_count'] > 0:
            print(f"  - {tool_stat['name']}: {tool_stat['usage_count']} calls, "
                  f"{tool_stat['success_rate']*100:.0f}% success rate")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_tools())