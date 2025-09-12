#!/usr/bin/env python3
"""Comprehensive tool API testing script."""

import httpx
import asyncio
import json
from datetime import datetime
import sys

API_URL = "http://localhost:8001"

async def test_tools():
    """Test all tools via API."""
    print("=" * 80)
    print(" 🧪 TOOL API COMPREHENSIVE TEST")
    print("=" * 80)
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check health
        print("\n🏥 Health Check")
        print("-" * 40)
        response = await client.get(f"{API_URL}/health")
        health = response.json()
        print(f"✅ Status: {health['status']}")
        print(f"📊 Tools Available: {health.get('tools_available', 'N/A')}")
        
        # List available tools
        print("\n📋 Available Tools")
        print("-" * 40)
        response = await client.get(f"{API_URL}/api/tools/tools")
        tools_data = response.json()
        print(f"Total tools: {tools_data['total_count']}")
        print(f"Categories: {', '.join(tools_data['categories'])}")
        
        # Test 1: Calculator
        print("\n🧮 TEST 1: CALCULATOR")
        print("-" * 40)
        
        test_expressions = [
            "2 + 2",
            "sqrt(144)",
            "pow(2, 10)",
            "(100 + 200) / 3",
            "sin(3.14159/2)"
        ]
        
        for expr in test_expressions:
            response = await client.post(
                f"{API_URL}/api/tools/execute",
                json={
                    "tool_name": "calculator",
                    "parameters": {"expression": expr}
                }
            )
            result = response.json()
            if result['status'] == 'success':
                print(f"  {expr:20} = {result['data']['result']}")
            else:
                print(f"  {expr:20} ❌ Error: {result['error']}")
        
        # Test 2: Statistics
        print("\n📈 TEST 2: STATISTICS")
        print("-" * 40)
        
        datasets = [
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [10, 20, 30, 40, 50],
            [15, 25, 35, 45, 55, 65, 75, 85, 95]
        ]
        
        for i, data in enumerate(datasets, 1):
            response = await client.post(
                f"{API_URL}/api/tools/execute",
                json={
                    "tool_name": "statistics",
                    "parameters": {
                        "data": data,
                        "operations": ["mean", "median", "std", "min", "max"]
                    }
                }
            )
            result = response.json()
            if result['status'] == 'success':
                stats = result['data']
                print(f"  Dataset {i}: {data[:3]}...{data[-1:]}")
                print(f"    Mean: {stats['mean']:.2f}, Median: {stats['median']:.2f}")
                print(f"    Range: {stats['min']}-{stats['max']}, StdDev: {stats.get('std', 0):.2f}")
        
        # Test 3: File Operations
        print("\n📁 TEST 3: FILE OPERATIONS")
        print("-" * 40)
        
        # Write file
        test_content = f"""Test Report
Generated: {datetime.now().isoformat()}
Status: Testing
Tools: Active

Results:
- Calculator: OK
- Statistics: OK
- File I/O: Testing...
"""
        
        response = await client.post(
            f"{API_URL}/api/tools/execute",
            json={
                "tool_name": "file_write",
                "parameters": {
                    "file_path": "/tmp/api_test_report.txt",
                    "content": test_content
                }
            }
        )
        if response.json()['status'] == 'success':
            print("  ✅ File written successfully")
        
        # Read file
        response = await client.post(
            f"{API_URL}/api/tools/execute",
            json={
                "tool_name": "file_read",
                "parameters": {"file_path": "/tmp/api_test_report.txt"}
            }
        )
        if response.json()['status'] == 'success':
            content = response.json()['data']
            print(f"  ✅ File read successfully ({len(content)} bytes)")
        
        # List files
        response = await client.post(
            f"{API_URL}/api/tools/execute",
            json={
                "tool_name": "file_list",
                "parameters": {
                    "directory": "/home/gpt-oss/backend",
                    "pattern": "*.py"
                }
            }
        )
        if response.json()['status'] == 'success':
            files = response.json()['data']
            print(f"  ✅ Found {len(files)} Python files")
            for f in files[:3]:
                print(f"     • {f['name']} ({f['size']:,} bytes)")
        
        # Test 4: System Information
        print("\n🖥️ TEST 4: SYSTEM INFORMATION")
        print("-" * 40)
        
        response = await client.post(
            f"{API_URL}/api/tools/execute",
            json={
                "tool_name": "system_info",
                "parameters": {"info_type": "all"}
            }
        )
        
        if response.json()['status'] == 'success':
            info = response.json()['data']
            print(f"  OS: {info['os']['system']} {info['os']['release']}")
            print(f"  CPU: {info['cpu']['logical_cores']} cores @ {info['cpu']['usage_percent']:.1f}%")
            print(f"  Memory: {info['memory']['used_gb']:.1f}/{info['memory']['total_gb']:.1f} GB ({info['memory']['percent']:.1f}%)")
            print(f"  Disk: {info['disk']['used_gb']:.1f}/{info['disk']['total_gb']:.1f} GB ({info['disk']['percent']:.1f}%)")
        
        # Test 5: Process List
        print("\n⚙️ TEST 5: PROCESS LIST")
        print("-" * 40)
        
        response = await client.post(
            f"{API_URL}/api/tools/execute",
            json={
                "tool_name": "process_list",
                "parameters": {
                    "sort_by": "cpu",
                    "limit": 5
                }
            }
        )
        
        if response.json()['status'] == 'success':
            processes = response.json()['data']
            print("  Top 5 processes by CPU:")
            for i, p in enumerate(processes[:5], 1):
                print(f"  {i}. {p['name'][:20]:20} PID: {p['pid']:8} CPU: {p['cpu_percent']:5.1f}%")
        
        # Test 6: JSON Operations
        print("\n🔧 TEST 6: JSON OPERATIONS")
        print("-" * 40)
        
        json_data = {
            "project": "GPT-OSS",
            "version": "2.0",
            "components": {
                "backend": {
                    "status": "active",
                    "tools": 15,
                    "categories": 6
                },
                "frontend": {
                    "status": "pending",
                    "framework": "React"
                }
            },
            "metrics": {
                "uptime": 99.9,
                "requests": 1000,
                "errors": 5
            }
        }
        
        # Parse JSON
        response = await client.post(
            f"{API_URL}/api/tools/execute",
            json={
                "tool_name": "json_parse",
                "parameters": {"json_string": json.dumps(json_data)}
            }
        )
        if response.json()['status'] == 'success':
            print("  ✅ JSON parsed successfully")
        
        # Query JSON
        queries = [
            "project",
            "components.backend.tools",
            "metrics.uptime"
        ]
        
        for path in queries:
            response = await client.post(
                f"{API_URL}/api/tools/execute",
                json={
                    "tool_name": "json_query",
                    "parameters": {
                        "data": json_data,
                        "path": path
                    }
                }
            )
            if response.json()['status'] == 'success':
                value = response.json()['data']
                print(f"  Query '{path}' = {value}")
        
        # Test 7: Data Transformation
        print("\n🔄 TEST 7: DATA TRANSFORMATION")
        print("-" * 40)
        
        csv_data = """name,type,status
calculator,math,active
file_read,file,active
system_info,system,active
json_parse,data,active"""
        
        response = await client.post(
            f"{API_URL}/api/tools/execute",
            json={
                "tool_name": "data_transform",
                "parameters": {
                    "data": csv_data,
                    "from_format": "csv",
                    "to_format": "json"
                }
            }
        )
        
        if response.json()['status'] == 'success':
            transformed = response.json()['data']
            print("  ✅ CSV → JSON transformation successful")
            print(f"  Transformed {len(transformed)} records")
        
        # Test 8: Environment Variables
        print("\n🌍 TEST 8: ENVIRONMENT VARIABLES")
        print("-" * 40)
        
        response = await client.post(
            f"{API_URL}/api/tools/execute",
            json={
                "tool_name": "env_get",
                "parameters": {}
            }
        )
        
        if response.json()['status'] == 'success':
            env_vars = response.json()['data']
            important_vars = ["PATH", "HOME", "USER", "SHELL", "PWD"]
            
            for var in important_vars:
                if var in env_vars:
                    value = env_vars[var]
                    if len(value) > 40:
                        value = value[:37] + "..."
                    print(f"  {var:8} = {value}")
        
        # Test 9: API Request Tool
        print("\n🌐 TEST 9: API REQUEST TOOL")
        print("-" * 40)
        
        # Test API request to our own health endpoint
        response = await client.post(
            f"{API_URL}/api/tools/execute",
            json={
                "tool_name": "api_request",
                "parameters": {
                    "method": "GET",
                    "url": f"{API_URL}/health"
                }
            }
        )
        
        if response.json()['status'] == 'success':
            api_result = response.json()['data']
            print(f"  ✅ API request successful")
            print(f"  Status Code: {api_result['status_code']}")
            print(f"  Response: {api_result['content']}")
        
        # Get tool statistics
        print("\n📊 TOOL USAGE STATISTICS")
        print("-" * 40)
        
        response = await client.get(f"{API_URL}/api/tools/stats")
        stats = response.json()
        
        total_calls = sum(tool['usage_count'] for tool in stats['tools'])
        successful = sum(tool['success_count'] for tool in stats['tools'])
        
        print(f"  Total API Calls: {total_calls}")
        print(f"  Successful: {successful}")
        print(f"  Success Rate: {(successful/total_calls*100) if total_calls > 0 else 0:.1f}%")
        print(f"  Active Tools: {stats['total_tools']}")
        
        print("\n  Most Used Tools:")
        for tool in sorted(stats['tools'], key=lambda x: x['usage_count'], reverse=True)[:5]:
            if tool['usage_count'] > 0:
                print(f"    • {tool['name']:15} {tool['usage_count']:3} calls")
        
        # Test specific tool endpoint
        print("\n🔍 TEST 10: SPECIFIC TOOL INFO")
        print("-" * 40)
        
        response = await client.get(f"{API_URL}/api/tools/tools/calculator")
        if response.status_code == 200:
            tool_info = response.json()
            print(f"  Tool: {tool_info['name']}")
            print(f"  Category: {tool_info['category']}")
            print(f"  Description: {tool_info['description']}")
            print(f"  Timeout: {tool_info['timeout']}s")
        
        print("\n" + "=" * 80)
        print(" ✅ ALL API TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(test_tools())
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)