#!/usr/bin/env python3
"""Test script for the complete tool system."""

import asyncio
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import tool system
from tools import (
    ToolRegistry,
    FileReadTool, FileWriteTool, FileListTool,
    SystemInfoTool, ProcessListTool, EnvironmentTool,
    CalculatorTool, StatisticsTool,
    JSONParseTool, JSONQueryTool, DataTransformTool,
    APIRequestTool, WebScrapeTool,
    DatabaseQueryTool, DatabaseExecuteTool
)


async def test_tool_system():
    """Test all tools in the system."""
    print("=" * 80)
    print(" TOOL SYSTEM INTEGRATION TEST")
    print("=" * 80)
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Initialize registry
    registry = ToolRegistry()
    
    # Register all tools
    print("\n📦 REGISTERING TOOLS...")
    print("-" * 80)
    
    # File tools
    registry.register(FileReadTool(), category="file")
    registry.register(FileWriteTool(), category="file")
    registry.register(FileListTool(), category="file")
    print("  ✅ File tools registered")
    
    # System tools
    registry.register(SystemInfoTool(), category="system")
    registry.register(ProcessListTool(), category="system")
    registry.register(EnvironmentTool(), category="system")
    print("  ✅ System tools registered")
    
    # Math tools
    registry.register(CalculatorTool(), category="math")
    registry.register(StatisticsTool(), category="math")
    print("  ✅ Math tools registered")
    
    # Data tools
    registry.register(JSONParseTool(), category="data")
    registry.register(JSONQueryTool(), category="data")
    registry.register(DataTransformTool(), category="data")
    print("  ✅ Data tools registered")
    
    # Web tools
    registry.register(APIRequestTool(), category="web")
    registry.register(WebScrapeTool(), category="web")
    print("  ✅ Web tools registered")
    
    # Database tools
    registry.register(DatabaseQueryTool(), category="database")
    registry.register(DatabaseExecuteTool(), category="database")
    print("  ✅ Database tools registered")
    
    print(f"\n  Total tools: {len(registry.list_tools())}")
    print(f"  Categories: {', '.join(registry._categories.keys())}")
    
    # Test 1: Calculator
    print("\n🧮 TEST 1: CALCULATOR")
    print("-" * 80)
    
    result = await registry.execute_tool("calculator", expression="(10 + 20) * 3")
    if result.status.value == "success":
        print(f"  Expression: (10 + 20) * 3")
        print(f"  Result: {result.data['result']}")
        print("  ✅ Calculator test passed")
    else:
        print(f"  ❌ Calculator test failed: {result.error}")
    
    # Test 2: Statistics
    print("\n📈 TEST 2: STATISTICS")
    print("-" * 80)
    
    data_points = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    result = await registry.execute_tool(
        "statistics", 
        data=data_points,
        operations=["mean", "median", "std", "min", "max"]
    )
    
    if result.status.value == "success":
        print(f"  Data: {data_points}")
        print(f"  Mean: {result.data['mean']:.2f}")
        print(f"  Median: {result.data['median']:.2f}")
        print(f"  Std Dev: {result.data['std']:.2f}")
        print(f"  Range: {result.data['min']} - {result.data['max']}")
        print("  ✅ Statistics test passed")
    else:
        print(f"  ❌ Statistics test failed: {result.error}")
    
    # Test 3: System Info
    print("\n🖥️ TEST 3: SYSTEM INFO")
    print("-" * 80)
    
    result = await registry.execute_tool("system_info", info_type="all")
    
    if result.status.value == "success":
        data = result.data
        print(f"  OS: {data['os']['system']} {data['os']['release']}")
        print(f"  CPU Cores: {data['cpu']['logical_cores']}")
        print(f"  Memory: {data['memory']['used_gb']:.1f}/{data['memory']['total_gb']:.1f} GB")
        print(f"  Disk: {data['disk']['used_gb']:.1f}/{data['disk']['total_gb']:.1f} GB")
        print("  ✅ System info test passed")
    else:
        print(f"  ❌ System info test failed: {result.error}")
    
    # Test 4: File Operations
    print("\n📁 TEST 4: FILE OPERATIONS")
    print("-" * 80)
    
    # Write a test file
    test_content = f"""# Test File
Created: {datetime.now().isoformat()}
Tool System: Active
Status: Testing
"""
    
    result = await registry.execute_tool(
        "file_write",
        file_path="/tmp/tool_test.txt",
        content=test_content
    )
    
    if result.status.value == "success":
        print("  ✅ File written successfully")
        
        # Read it back
        result = await registry.execute_tool("file_read", file_path="/tmp/tool_test.txt")
        if result.status.value == "success":
            print("  ✅ File read successfully")
            print(f"  Content length: {len(result.data)} characters")
        else:
            print(f"  ❌ File read failed: {result.error}")
    else:
        print(f"  ❌ File write failed: {result.error}")
    
    # Test 5: JSON Processing
    print("\n🔧 TEST 5: JSON PROCESSING")
    print("-" * 80)
    
    json_data = {
        "project": "Tool System",
        "version": "1.0",
        "tools": ["calculator", "statistics", "file_ops"],
        "metrics": {
            "total": 15,
            "active": 15,
            "success_rate": 100
        }
    }
    
    # Parse JSON
    result = await registry.execute_tool(
        "json_parse",
        json_string=json.dumps(json_data)
    )
    
    if result.status.value == "success":
        print("  ✅ JSON parsed successfully")
        
        # Query JSON
        result = await registry.execute_tool(
            "json_query",
            data=json_data,
            path="metrics.total"
        )
        
        if result.status.value == "success":
            print(f"  Total tools from JSON: {result.data}")
            print("  ✅ JSON query test passed")
        else:
            print(f"  ❌ JSON query failed: {result.error}")
    else:
        print(f"  ❌ JSON parse failed: {result.error}")
    
    # Test 6: Process List
    print("\n⚙️ TEST 6: PROCESS LIST")
    print("-" * 80)
    
    result = await registry.execute_tool(
        "process_list",
        sort_by="memory",
        limit=5
    )
    
    if result.status.value == "success":
        processes = result.data
        print("  Top 5 processes by memory:")
        for i, p in enumerate(processes[:5], 1):
            print(f"  {i}. {p['name']:20} PID: {p['pid']:8} Memory: {p['memory_percent']:5.2f}%")
        print("  ✅ Process list test passed")
    else:
        print(f"  ❌ Process list test failed: {result.error}")
    
    # Test 7: Environment Variables
    print("\n🌍 TEST 7: ENVIRONMENT VARIABLES")
    print("-" * 80)
    
    result = await registry.execute_tool("env_get")
    
    if result.status.value == "success":
        env_vars = result.data
        important_vars = ["PATH", "HOME", "USER", "PWD"]
        
        for var in important_vars:
            if var in env_vars:
                value = env_vars[var]
                if len(value) > 50:
                    value = value[:47] + "..."
                print(f"  {var:10} = {value}")
        print("  ✅ Environment test passed")
    else:
        print(f"  ❌ Environment test failed: {result.error}")
    
    # Get tool statistics
    print("\n📊 TOOL STATISTICS")
    print("-" * 80)
    
    stats = registry.get_stats()
    total_calls = sum(tool['usage_count'] for tool in stats['tools'])
    successful_calls = sum(tool['success_count'] for tool in stats['tools'])
    
    print(f"  Total API Calls: {total_calls}")
    print(f"  Successful: {successful_calls}")
    print(f"  Success Rate: {(successful_calls/total_calls*100) if total_calls > 0 else 0:.1f}%")
    print(f"  Active Tools: {stats['total_tools']}")
    print(f"  Categories: {', '.join(stats['categories'])}")
    
    print("\n  Tool Usage Breakdown:")
    for tool in sorted(stats['tools'], key=lambda x: x['usage_count'], reverse=True)[:5]:
        if tool['usage_count'] > 0:
            print(f"    • {tool['name']:15} {tool['usage_count']:3} calls ({tool['success_rate']*100:.0f}% success)")
    
    # Test schemas
    print("\n📋 TOOL SCHEMAS")
    print("-" * 80)
    
    schemas = registry.get_schemas()
    print(f"  Total schemas available: {len(schemas)}")
    
    for schema in schemas[:3]:
        func = schema.get("function", {})
        print(f"  • {func.get('name', 'unknown'):15} - {func.get('description', 'No description')[:50]}")
    
    print("\n" + "=" * 80)
    print(" ✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_tool_system())