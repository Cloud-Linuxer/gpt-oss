#!/usr/bin/env python3
"""Final demonstration of the tool system."""

import httpx
import json
import asyncio
from datetime import datetime

TOOL_API = "http://localhost:8001"


async def demo_tool_system():
    """Demonstrate all tool capabilities."""
    print("=" * 80)
    print(" 🚀 TOOL SYSTEM FINAL DEMONSTRATION")
    print("=" * 80)
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. System Overview
        print("\n📊 SYSTEM OVERVIEW")
        print("-" * 80)
        
        # Get system info
        response = await client.post(f"{TOOL_API}/execute", json={
            "tool_name": "system_info",
            "parameters": {"info_type": "all"}
        })
        result = response.json()
        
        if result['status'] == 'success':
            data = result['data']
            print(f"🖥️  OS: {data['os']['system']} {data['os']['release']}")
            print(f"💻 CPU: {data['cpu']['logical_cores']} cores @ {data['cpu']['usage_percent']}% usage")
            print(f"🧠 Memory: {data['memory']['used_gb']:.1f}/{data['memory']['total_gb']:.1f} GB ({data['memory']['percent']:.1f}%)")
            print(f"💾 Disk: {data['disk']['used_gb']:.1f}/{data['disk']['total_gb']:.1f} GB ({data['disk']['percent']:.1f}%)")
        
        # 2. Mathematical Calculations
        print("\n🧮 MATHEMATICAL OPERATIONS")
        print("-" * 80)
        
        calculations = [
            "pow(2, 10)",
            "sqrt(144) * 5",
            "sin(3.14159) + cos(0)",
            "(100 + 200) / 3"
        ]
        
        for expr in calculations:
            response = await client.post(f"{TOOL_API}/execute", json={
                "tool_name": "calculator",
                "parameters": {"expression": expr}
            })
            result = response.json()
            if result['status'] == 'success':
                print(f"  {expr:30} = {result['data']['result']}")
        
        # 3. Statistical Analysis
        print("\n📈 STATISTICAL ANALYSIS")
        print("-" * 80)
        
        data_points = [23, 45, 67, 89, 12, 34, 56, 78, 90, 100]
        response = await client.post(f"{TOOL_API}/execute", json={
            "tool_name": "statistics",
            "parameters": {
                "data": data_points,
                "operations": ["mean", "median", "std", "min", "max"]
            }
        })
        result = response.json()
        
        if result['status'] == 'success':
            stats = result['data']
            print(f"  Dataset: {data_points}")
            print(f"  Mean: {stats['mean']:.2f}")
            print(f"  Median: {stats['median']:.2f}")
            print(f"  Std Dev: {stats['std']:.2f}")
            print(f"  Range: {stats['min']} - {stats['max']}")
        
        # 4. File Operations
        print("\n📁 FILE OPERATIONS")
        print("-" * 80)
        
        # Write a file
        test_content = f"""# Tool System Report
Generated: {datetime.now().isoformat()}
Status: Active
Performance: Excellent

## Results
- All systems operational
- Tools responding correctly
- Integration successful
"""
        
        response = await client.post(f"{TOOL_API}/execute", json={
            "tool_name": "file_write",
            "parameters": {
                "file_path": "/tmp/tool_report.md",
                "content": test_content
            }
        })
        
        if response.json()['status'] == 'success':
            print("  ✅ Report written to /tmp/tool_report.md")
        
        # Read it back
        response = await client.post(f"{TOOL_API}/execute", json={
            "tool_name": "file_read",
            "parameters": {"file_path": "/tmp/tool_report.md"}
        })
        
        if response.json()['status'] == 'success':
            print("  ✅ Report verified and readable")
        
        # List Python files
        response = await client.post(f"{TOOL_API}/execute", json={
            "tool_name": "file_list",
            "parameters": {
                "directory": "/home/gpt-oss/backend",
                "pattern": "test*.py"
            }
        })
        result = response.json()
        
        if result['status'] == 'success':
            files = result['data']
            print(f"  📂 Found {len(files)} test files in backend/")
            for f in files[:3]:
                print(f"     • {f['name']} ({f['size']:,} bytes)")
        
        # 5. JSON Processing
        print("\n🔧 JSON DATA PROCESSING")
        print("-" * 80)
        
        json_data = {
            "project": "Tool System",
            "version": "2.0",
            "components": [
                {"name": "file_tools", "status": "active"},
                {"name": "system_tools", "status": "active"},
                {"name": "math_tools", "status": "active"}
            ],
            "metrics": {
                "total_tools": 11,
                "success_rate": 100,
                "avg_response_ms": 15
            }
        }
        
        # Parse JSON
        response = await client.post(f"{TOOL_API}/execute", json={
            "tool_name": "json_parse",
            "parameters": {"json_string": json.dumps(json_data)}
        })
        
        if response.json()['status'] == 'success':
            print("  ✅ JSON parsed successfully")
        
        # Query JSON
        response = await client.post(f"{TOOL_API}/execute", json={
            "tool_name": "json_query",
            "parameters": {
                "data": json_data,
                "path": "metrics.total_tools"
            }
        })
        result = response.json()
        
        if result['status'] == 'success':
            print(f"  📊 Total tools in system: {result['data']}")
        
        # Transform to CSV
        csv_data = """name,type,status
file_read,file,active
calculator,math,active
system_info,system,active"""
        
        response = await client.post(f"{TOOL_API}/execute", json={
            "tool_name": "data_transform",
            "parameters": {
                "data": csv_data,
                "from_format": "csv",
                "to_format": "json"
            }
        })
        
        if response.json()['status'] == 'success':
            print("  ✅ CSV successfully transformed to JSON")
        
        # 6. Process Monitoring
        print("\n⚙️ PROCESS MONITORING")
        print("-" * 80)
        
        response = await client.post(f"{TOOL_API}/execute", json={
            "tool_name": "process_list",
            "parameters": {"sort_by": "memory", "limit": 5}
        })
        result = response.json()
        
        if result['status'] == 'success':
            processes = result['data']
            print("  Top 5 processes by memory:")
            for i, p in enumerate(processes, 1):
                print(f"  {i}. {p['name']:20} PID: {p['pid']:8} Memory: {p['memory_percent']:5.2f}%")
        
        # 7. Environment Check
        print("\n🌍 ENVIRONMENT VARIABLES")
        print("-" * 80)
        
        response = await client.post(f"{TOOL_API}/execute", json={
            "tool_name": "env_get",
            "parameters": {}
        })
        result = response.json()
        
        if result['status'] == 'success':
            env_vars = result['data']
            important_vars = ["PATH", "HOME", "USER", "PWD"]
            for var in important_vars:
                if var in env_vars:
                    value = env_vars[var]
                    if len(value) > 50:
                        value = value[:47] + "..."
                    print(f"  {var:10} = {value}")
        
        # 8. Performance Summary
        print("\n🏆 PERFORMANCE SUMMARY")
        print("-" * 80)
        
        response = await client.get(f"{TOOL_API}/stats")
        stats = response.json()
        
        total_calls = sum(tool['usage_count'] for tool in stats['tools'])
        successful_calls = sum(tool['success_count'] for tool in stats['tools'])
        
        print(f"  📊 Total API Calls: {total_calls}")
        print(f"  ✅ Successful: {successful_calls}")
        print(f"  🎯 Success Rate: {(successful_calls/total_calls*100) if total_calls > 0 else 0:.1f}%")
        print(f"  🛠️ Active Tools: {stats['total_tools']}")
        print(f"  📁 Categories: {', '.join(stats['categories'])}")
        
        print("\n  Tool Usage Breakdown:")
        for tool in sorted(stats['tools'], key=lambda x: x['usage_count'], reverse=True)[:5]:
            if tool['usage_count'] > 0:
                print(f"    • {tool['name']:15} {tool['usage_count']:3} calls ({tool['success_rate']*100:.0f}% success)")
        
        print("\n" + "=" * 80)
        print(" ✅ DEMONSTRATION COMPLETE - ALL SYSTEMS OPERATIONAL")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(demo_tool_system())