# GPT-OSS Backend API Documentation

## Overview
The GPT-OSS backend provides a comprehensive tool system integrated with vLLM for AI-powered tool execution.

## Architecture

### Components
- **vLLM Client**: Connects to vLLM server for LLM inference
- **Tool Registry**: Manages all available tools
- **API Routes**: FastAPI endpoints for tool execution and chat
- **Tool Categories**: File, System, Math, Data, Web, Database tools

## API Endpoints

### Root Endpoints

#### GET /
Returns API information and available endpoints.

#### GET /health
Health check endpoint.

Response:
```json
{
  "status": "healthy",
  "vllm_connected": true,
  "tools_available": 15,
  "version": "0.1.0"
}
```

### Tool Endpoints

#### GET /api/tools/tools
List all available tools with their schemas.

Response:
```json
{
  "tools": [
    {
      "name": "calculator",
      "category": "math",
      "description": "Perform mathematical calculations",
      "parameters": {
        "type": "object",
        "properties": {
          "expression": {
            "type": "string",
            "description": "Mathematical expression to evaluate"
          }
        }
      },
      "timeout": 5.0
    }
  ],
  "total_count": 15,
  "categories": ["file", "system", "math", "data", "web", "database"]
}
```

#### POST /api/tools/execute
Execute a specific tool.

Request:
```json
{
  "tool_name": "calculator",
  "parameters": {
    "expression": "(10 + 20) * 3"
  },
  "timeout": 30.0
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "expression": "(10 + 20) * 3",
    "result": 90
  },
  "error": null,
  "metadata": null
}
```

#### GET /api/tools/stats
Get tool usage statistics.

Response:
```json
{
  "total_tools": 15,
  "categories": ["file", "system", "math", "data", "web", "database"],
  "tools": [
    {
      "name": "calculator",
      "usage_count": 10,
      "success_count": 9,
      "error_count": 1,
      "last_used": "2025-09-12T13:00:00",
      "success_rate": 0.9
    }
  ]
}
```

#### POST /api/tools/stats/reset
Reset tool usage statistics.

#### GET /api/tools/tools/{tool_name}
Get information about a specific tool.

#### POST /api/tools/tools/{tool_name}/execute
Execute a specific tool by name.

### OpenAI-Compatible Endpoints

#### POST /v1/chat/completions
OpenAI-compatible chat completions endpoint with tool support.

Request:
```json
{
  "model": "openai/gpt-oss-20b",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Calculate 25 * 4"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "calculator",
        "description": "Perform mathematical calculations",
        "parameters": {
          "type": "object",
          "properties": {
            "expression": {
              "type": "string",
              "description": "Mathematical expression"
            }
          }
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

Response:
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "openai/gpt-oss-20b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The result of 25 * 4 is 100."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 20,
    "total_tokens": 70
  }
}
```

## Available Tools

### File Tools
- **file_read**: Read contents of a file
- **file_write**: Write content to a file
- **file_list**: List files in a directory

### System Tools
- **system_info**: Get system information (CPU, memory, disk)
- **process_list**: List running processes
- **env_get**: Get environment variables

### Math Tools
- **calculator**: Perform mathematical calculations
- **statistics**: Perform statistical calculations on data

### Data Tools
- **json_parse**: Parse JSON string
- **json_query**: Query JSON data using path notation
- **data_transform**: Transform data between formats (CSV, JSON, XML)

### Web Tools
- **api_request**: Make HTTP API requests
- **web_scrape**: Scrape web pages (placeholder)

### Database Tools
- **db_query**: Execute database queries (placeholder)
- **db_execute**: Execute database modifications (placeholder)

## Tool Schemas

Each tool follows the OpenAI function calling schema format:

```json
{
  "type": "function",
  "function": {
    "name": "tool_name",
    "description": "Tool description",
    "parameters": {
      "type": "object",
      "properties": {
        "param1": {
          "type": "string",
          "description": "Parameter description"
        }
      },
      "required": ["param1"]
    }
  }
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- 200: Success
- 400: Bad Request (invalid parameters)
- 404: Not Found (tool not found)
- 500: Internal Server Error

Error response format:
```json
{
  "error": "Error message description"
}
```

## Usage Examples

### Python Client Example

```python
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        # Execute a tool
        response = await client.post(
            "http://localhost:8001/api/tools/execute",
            json={
                "tool_name": "calculator",
                "parameters": {"expression": "sqrt(144)"}
            }
        )
        result = response.json()
        print(f"Result: {result['data']['result']}")
        
        # Chat with tools
        response = await client.post(
            "http://localhost:8001/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {"role": "user", "content": "What's the weather?"}
                ],
                "tools": [...],  # Tool schemas
                "tool_choice": "auto"
            }
        )
        print(response.json())

asyncio.run(main())
```

### cURL Examples

```bash
# List tools
curl http://localhost:8001/api/tools/tools

# Execute calculator
curl -X POST http://localhost:8001/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "calculator", "parameters": {"expression": "2 + 2"}}'

# Get system info
curl -X POST http://localhost:8001/api/tools/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "system_info", "parameters": {"info_type": "all"}}'
```

## Running the Backend

### Development Mode
```bash
cd /home/gpt-oss/backend
python3 app_main.py
```

### Production Mode
```bash
cd /home/gpt-oss/backend
uvicorn app_main:app --host 0.0.0.0 --port 8001 --workers 4
```

### With Docker
```bash
docker-compose up backend
```

## Configuration

Configuration is managed through environment variables:
- `VLLM_BASE_URL`: vLLM server URL (default: http://localhost:8000)
- `VLLM_MODEL`: Model name (default: openai/gpt-oss-20b)
- `PORT`: Backend port (default: 8001)
- `HOST`: Backend host (default: 0.0.0.0)
- `LOG_LEVEL`: Logging level (default: INFO)

## Testing

Run the test suite:
```bash
python3 test_tool_system.py
python3 test_vllm_tools.py
python3 demo_final.py
```

## Performance

- Tool execution timeout: 30 seconds (configurable)
- Concurrent tool execution supported
- Tool usage statistics tracking
- Automatic error recovery and retry logic

## Security Considerations

- Input validation on all tool parameters
- Sandboxed file operations (restricted paths)
- Safe mathematical expression evaluation
- API request filtering and rate limiting

## Future Enhancements

- [ ] Database tool implementation
- [ ] Web scraping tool implementation
- [ ] Tool chaining and workflows
- [ ] Advanced caching mechanisms
- [ ] Tool authentication and authorization
- [ ] WebSocket support for streaming
- [ ] Tool marketplace integration