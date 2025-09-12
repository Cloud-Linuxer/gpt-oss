#!/usr/bin/env python3
"""Test client for tool system API."""

import httpx
import json
import asyncio
from typing import Dict, Any

BASE_URL = "http://localhost:8001"


async def test_tool_system():
    """Test all tool functionalities."""
    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("TOOL SYSTEM API TEST")
        print("=" * 80)
        
        # 1. Check server status
        print("\n📡 Server Status")
        print("-" * 40)
        response = await client.get(f"{BASE_URL}/")
        print(f"Response: {response.json()}")
        
        # 2. List available tools
        print("\n📋 Available Tools")
        print("-" * 40)
        response = await client.get(f"{BASE_URL}/tools")
        tools = response.json()
        print(f"Total tools: {tools['count']}")
        for tool in tools['tools'][:5]:  # Show first 5
            print(f"  • {tool['name']}: {tool['description']}")
        
        # 3. Test Calculator Tool
        print("\n🧮 Test: Calculator Tool")
        print("-" * 40)
        test_cases = [
            {"expression": "2 * (3 + 4)"},
            {"expression": "sqrt(16) + pow(2, 3)"},
            {"expression": "sin(3.14159/2)"}
        ]
        
        for test in test_cases:
            response = await client.post(
                f"{BASE_URL}/execute",
                json={"tool_name": "calculator", "parameters": test}
            )
            result = response.json()
            if result['status'] == 'success':
                print(f"  {test['expression']} = {result['data']['result']}")
            else:
                print(f"  {test['expression']} = ERROR: {result['error']}")
        
        # 4. Test System Info Tool
        print("\n💻 Test: System Info Tool")
        print("-" * 40)
        response = await client.post(
            f"{BASE_URL}/execute",
            json={"tool_name": "system_info", "parameters": {"info_type": "cpu"}}
        )
        result = response.json()
        if result['status'] == 'success':
            cpu_info = result['data']['cpu']
            print(f"  CPU Cores: {cpu_info['logical_cores']}")
            print(f"  CPU Usage: {cpu_info['usage_percent']}%")
        
        # 5. Test File List Tool
        print("\n📁 Test: File List Tool")
        print("-" * 40)
        response = await client.post(
            f"{BASE_URL}/execute",
            json={
                "tool_name": "file_list",
                "parameters": {
                    "directory": "/home/gpt-oss/backend",
                    "pattern": "*.py"
                }
            }
        )
        result = response.json()
        if result['status'] == 'success':
            files = result['data']
            print(f"  Found {len(files)} Python files:")
            for f in files[:3]:  # Show first 3
                print(f"    - {f['name']} ({f['size']} bytes)")
        
        # 6. Test File Write Tool
        print("\n📝 Test: File Write Tool")
        print("-" * 40)
        test_content = """# Test File
This file was created by the tool system test.
Timestamp: 2024-01-01 00:00:00
Status: SUCCESS
"""
        response = await client.post(
            f"{BASE_URL}/execute",
            json={
                "tool_name": "file_write",
                "parameters": {
                    "file_path": "/tmp/tool_test.txt",
                    "content": test_content
                }
            }
        )
        result = response.json()
        print(f"  Status: {result['status']}")
        if result['status'] == 'success':
            print(f"  Result: {result['data']}")
        
        # 7. Test File Read Tool
        print("\n📖 Test: File Read Tool")
        print("-" * 40)
        response = await client.post(
            f"{BASE_URL}/execute",
            json={
                "tool_name": "file_read",
                "parameters": {"file_path": "/tmp/tool_test.txt"}
            }
        )
        result = response.json()
        if result['status'] == 'success':
            content = result['data']
            print(f"  File content (first 100 chars):")
            print(f"    {content[:100]}...")
        
        # 8. Test Statistics Tool
        print("\n📊 Test: Statistics Tool")
        print("-" * 40)
        test_data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        response = await client.post(
            f"{BASE_URL}/execute",
            json={
                "tool_name": "statistics",
                "parameters": {
                    "data": test_data,
                    "operations": ["mean", "median", "std", "min", "max"]
                }
            }
        )
        result = response.json()
        if result['status'] == 'success':
            stats = result['data']
            print(f"  Data: {test_data}")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        # 9. Test JSON Parse Tool
        print("\n🔧 Test: JSON Parse Tool")
        print("-" * 40)
        json_string = '{"name": "Tool Test", "version": "1.0", "status": "active"}'
        response = await client.post(
            f"{BASE_URL}/execute",
            json={
                "tool_name": "json_parse",
                "parameters": {"json_string": json_string}
            }
        )
        result = response.json()
        if result['status'] == 'success':
            print(f"  Parsed JSON: {json.dumps(result['data'], indent=2)}")
        
        # 10. Test Process List Tool
        print("\n⚙️ Test: Process List Tool")
        print("-" * 40)
        response = await client.post(
            f"{BASE_URL}/execute",
            json={
                "tool_name": "process_list",
                "parameters": {"sort_by": "memory", "limit": 3}
            }
        )
        result = response.json()
        if result['status'] == 'success':
            processes = result['data']
            print(f"  Top {len(processes)} processes by memory:")
            for p in processes:
                print(f"    - {p['name']} (PID: {p['pid']}, Mem: {p['memory_percent']}%)")
        
        # 11. Get Usage Statistics
        print("\n📈 Tool Usage Statistics")
        print("-" * 40)
        response = await client.get(f"{BASE_URL}/stats")
        stats = response.json()
        print(f"  Total tools: {stats['total_tools']}")
        print(f"  Categories: {', '.join(stats['categories'])}")
        print(f"  Tool usage:")
        for tool in stats['tools']:
            if tool['usage_count'] > 0:
                print(f"    - {tool['name']}: {tool['usage_count']} calls, "
                      f"{tool['success_rate']*100:.0f}% success")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_tool_system())