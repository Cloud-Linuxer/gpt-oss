#!/usr/bin/env python3
"""Simple tool API test."""

import httpx
import asyncio
import json
from datetime import datetime

API_URL = "http://localhost:8001"

async def test_tools():
    """Test tools via API."""
    print("=" * 80)
    print(" 🧪 TOOL API TEST")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Calculator
        print("\n🧮 Calculator Test")
        print("-" * 40)
        
        expressions = ["2 + 2", "sqrt(144)", "pow(2, 10)"]
        for expr in expressions:
            response = await client.post(
                f"{API_URL}/execute",
                json={
                    "tool_name": "calculator",
                    "parameters": {"expression": expr}
                }
            )
            result = response.json()
            if result['status'] == 'success':
                print(f"  {expr:15} = {result['data']['result']}")
            else:
                print(f"  {expr:15} ❌ {result.get('error', 'Failed')}")
        
        # Test 2: System Info
        print("\n🖥️ System Info Test")
        print("-" * 40)
        
        response = await client.post(
            f"{API_URL}/execute",
            json={
                "tool_name": "system_info",
                "parameters": {"info_type": "all"}
            }
        )
        result = response.json()
        if result['status'] == 'success':
            info = result['data']
            print(f"  OS: {info['os']['system']} {info['os']['release']}")
            print(f"  CPU: {info['cpu']['logical_cores']} cores")
            print(f"  Memory: {info['memory']['used_gb']:.1f}/{info['memory']['total_gb']:.1f} GB")
            print(f"  Disk: {info['disk']['used_gb']:.1f}/{info['disk']['total_gb']:.1f} GB")
        
        # Test 3: File Operations
        print("\n📁 File Operations Test")
        print("-" * 40)
        
        # Write file
        content = f"Test at {datetime.now()}"
        response = await client.post(
            f"{API_URL}/execute",
            json={
                "tool_name": "file_write",
                "parameters": {
                    "file_path": "/tmp/test_api.txt",
                    "content": content
                }
            }
        )
        if response.json()['status'] == 'success':
            print("  ✅ File written")
        
        # Read file
        response = await client.post(
            f"{API_URL}/execute",
            json={
                "tool_name": "file_read",
                "parameters": {"file_path": "/tmp/test_api.txt"}
            }
        )
        if response.json()['status'] == 'success':
            print(f"  ✅ File read: {response.json()['data']}")
        
        # Test 4: Statistics
        print("\n📈 Statistics Test")
        print("-" * 40)
        
        data = [10, 20, 30, 40, 50]
        response = await client.post(
            f"{API_URL}/execute",
            json={
                "tool_name": "statistics",
                "parameters": {
                    "data": data,
                    "operations": ["mean", "median", "min", "max"]
                }
            }
        )
        result = response.json()
        if result['status'] == 'success':
            stats = result['data']
            print(f"  Data: {data}")
            print(f"  Mean: {stats['mean']}, Median: {stats['median']}")
            print(f"  Range: {stats['min']}-{stats['max']}")
        
        # Test 5: JSON Operations
        print("\n🔧 JSON Test")
        print("-" * 40)
        
        json_data = {
            "project": "GPT-OSS",
            "version": "2.0",
            "status": "active"
        }
        
        # Parse JSON
        response = await client.post(
            f"{API_URL}/execute",
            json={
                "tool_name": "json_parse",
                "parameters": {"json_string": json.dumps(json_data)}
            }
        )
        if response.json()['status'] == 'success':
            print("  ✅ JSON parsed")
        
        # Query JSON
        response = await client.post(
            f"{API_URL}/execute",
            json={
                "tool_name": "json_query",
                "parameters": {
                    "data": json_data,
                    "path": "project"
                }
            }
        )
        if response.json()['status'] == 'success':
            print(f"  Project: {response.json()['data']}")
        
        # Test 6: Process List
        print("\n⚙️ Process List Test")
        print("-" * 40)
        
        response = await client.post(
            f"{API_URL}/execute",
            json={
                "tool_name": "process_list",
                "parameters": {
                    "sort_by": "memory",
                    "limit": 3
                }
            }
        )
        result = response.json()
        if result['status'] == 'success':
            processes = result['data']
            print("  Top 3 processes by memory:")
            for i, p in enumerate(processes[:3], 1):
                print(f"  {i}. {p['name'][:20]:20} Memory: {p['memory_percent']:.1f}%")
        
        # Get stats
        print("\n📊 Tool Statistics")
        print("-" * 40)
        
        response = await client.get(f"{API_URL}/stats")
        stats = response.json()
        print(f"  Total tools: {stats['total_tools']}")
        print(f"  Categories: {', '.join(stats['categories'])}")
        
        total_calls = sum(t['usage_count'] for t in stats['tools'])
        print(f"  Total calls: {total_calls}")
        
        print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_tools())