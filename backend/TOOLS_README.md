# Backend Tool System Documentation

## Overview

The backend now features a comprehensive, extensible tool system that allows the LLM to interact with various resources and perform complex operations. The system is designed with safety, modularity, and extensibility in mind.

## Architecture

### Core Components

1. **Tool Base Class** (`tools/base.py`)
   - Abstract base class for all tools
   - Automatic timeout and error handling
   - Usage statistics tracking
   - Parameter validation

2. **Tool Registry** (`tools/base.py`)
   - Central management of all tools
   - Category-based organization
   - Dynamic tool registration/unregistration
   - Unified execution interface

3. **Tool Categories**
   - **File Operations**: Read, write, and list files with safety constraints
   - **System Information**: System info, process list, environment variables
   - **Mathematics**: Calculator and statistics tools
   - **Data Processing**: JSON parsing, querying, and data transformation
   - **Web Operations**: API requests and web scraping (placeholder)
   - **Database**: Database queries and executions (placeholder)

## Available Tools

### File Operations

#### file_read
- **Description**: Read contents of a file
- **Parameters**:
  - `file_path` (string, required): Path to the file to read
  - `encoding` (string, optional): File encoding (default: "utf-8")
- **Safety**: Only allows reading from whitelisted directories

#### file_write
- **Description**: Write content to a file
- **Parameters**:
  - `file_path` (string, required): Path to the file to write
  - `content` (string, required): Content to write
  - `mode` (string, optional): Write mode ("w", "a", "x")
  - `encoding` (string, optional): File encoding (default: "utf-8")
- **Safety**: Only allows writing to whitelisted directories, size limits enforced

#### file_list
- **Description**: List files in a directory
- **Parameters**:
  - `directory` (string, required): Directory path
  - `pattern` (string, optional): File pattern to match (e.g., "*.py")
  - `recursive` (boolean, optional): Search recursively

### System Information

#### system_info
- **Description**: Get system information (OS, CPU, memory, disk)
- **Parameters**:
  - `info_type` (string, optional): Type of info ("all", "os", "cpu", "memory", "disk", "network")

#### process_list
- **Description**: List running processes
- **Parameters**:
  - `sort_by` (string, optional): Sort by ("cpu", "memory", "name")
  - `limit` (number, optional): Maximum number of processes to return

#### env_get
- **Description**: Get environment variables
- **Parameters**:
  - `var_name` (string, optional): Specific variable name or all allowed variables

### Mathematics

#### calculator
- **Description**: Perform mathematical calculations
- **Parameters**:
  - `expression` (string, optional): Mathematical expression to evaluate
  - `operation` (string, optional): Specific operation ("add", "subtract", "multiply", "divide", "power", "sqrt", "log")
  - `values` (array, optional): Values to perform operation on

#### statistics
- **Description**: Perform statistical calculations on data
- **Parameters**:
  - `data` (array, required): Numerical data to analyze
  - `operations` (array, optional): Operations to perform ("mean", "median", "mode", "std", "variance", "min", "max", "sum", "count", "range", "percentiles")

### Data Processing

#### json_parse
- **Description**: Parse and validate JSON string
- **Parameters**:
  - `json_string` (string, required): JSON string to parse
  - `validate_schema` (object, optional): JSON schema for validation

#### json_query
- **Description**: Query JSON data using JQ expressions
- **Parameters**:
  - `data` (string/object/array, required): JSON data to query
  - `query` (string, required): JQ query expression

#### data_transform
- **Description**: Transform data between formats (JSON, CSV, DataFrame)
- **Parameters**:
  - `data` (any, required): Data to transform
  - `from_format` (string, required): Input format ("json", "csv", "dataframe")
  - `to_format` (string, required): Output format ("json", "csv", "dataframe", "html", "markdown", "summary")
  - `options` (object, optional): Format-specific options

### Web Operations

#### api_request
- **Description**: Make HTTP API requests
- **Parameters**:
  - `method` (string, required): HTTP method ("GET", "POST", "PUT", "PATCH", "DELETE")
  - `url` (string, required): API endpoint URL
  - `headers` (object, optional): Request headers
  - `params` (object, optional): Query parameters
  - `json_data` (any, optional): JSON body data
  - `data` (object, optional): Form data

## API Endpoints

### `/api/chat`
Enhanced chat endpoint with tool support
- **Method**: POST
- **Body**: 
  ```json
  {
    "message": "string",
    "use_tools": true
  }
  ```
- **Response**:
  ```json
  {
    "response": "string",
    "tools_used": ["tool1", "tool2"]
  }
  ```

### `/api/tools`
Get information about available tools
- **Method**: GET
- **Response**:
  ```json
  {
    "tools": [...],
    "count": 15,
    "categories": ["file", "system", "math", "data", "web", "database"]
  }
  ```

### `/api/tools/execute`
Direct tool execution
- **Method**: POST
- **Body**:
  ```json
  {
    "tool_name": "string",
    "parameters": {}
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "data": {},
    "error": null
  }
  ```

### `/api/tools/stats`
Get tool usage statistics
- **Method**: GET
- **Response**:
  ```json
  {
    "total_tools": 15,
    "categories": [...],
    "tools": [
      {
        "name": "tool_name",
        "usage_count": 10,
        "success_count": 9,
        "error_count": 1,
        "success_rate": 0.9,
        "last_used": "2024-01-01T00:00:00"
      }
    ]
  }
  ```

### `/api/tools/reset-stats`
Reset tool usage statistics
- **Method**: POST
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Tool statistics reset"
  }
  ```

## Safety Features

1. **Path Restrictions**: File operations are restricted to whitelisted directories
2. **Size Limits**: File read/write operations have size limits (default: 10MB)
3. **Timeout Protection**: All tools have configurable timeouts (default: 30s)
4. **Environment Variable Filtering**: Only whitelisted environment variables can be accessed
5. **Expression Evaluation Safety**: Calculator uses restricted eval with whitelisted functions
6. **Error Handling**: Comprehensive error handling with graceful degradation

## Extending the Tool System

### Creating a New Tool

1. Create a new file in the `tools/` directory
2. Import the base classes:
```python
from .base import Tool, ToolResult, ToolStatus
```

3. Implement your tool class:
```python
class MyCustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_custom_tool",
            description="Description of what the tool does",
            timeout=30.0
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        try:
            # Your tool logic here
            result = do_something(**kwargs)
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=result
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=str(e)
            )
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
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

4. Register the tool in `app.py`:
```python
registry.register(MyCustomTool(), category="custom")
```

## Usage Examples

### Using Tools in Chat

```python
# Request with tools enabled
response = await client.post("/api/chat", json={
    "message": "What files are in the backend directory?",
    "use_tools": True
})

# The LLM will automatically use the file_list tool
# Response will include which tools were used
```

### Direct Tool Execution

```python
# Execute a tool directly
response = await client.post("/api/tools/execute", json={
    "tool_name": "calculator",
    "parameters": {
        "expression": "2 * (3 + 4)"
    }
})

# Response
{
    "status": "success",
    "data": {
        "expression": "2 * (3 + 4)",
        "result": 14
    },
    "error": null
}
```

## Migration from Legacy System

The new system is backwards compatible with the existing MCP tools. The legacy tools (`http_request` and `time_now`) are still available and work alongside the new tools.

To migrate to the new system:
1. Use `app_v2.py` instead of `app.py`
2. Update any direct tool calls to use the new registry
3. Gradually replace legacy tools with new equivalents

## Testing

Run the test suite:
```bash
cd backend
python -m pytest tests/test_tools.py -v
```

## Performance Considerations

- Tools are executed asynchronously for better performance
- Timeouts prevent long-running operations from blocking
- Statistics tracking helps identify performance bottlenecks
- The registry supports lazy loading of tools

## Troubleshooting

### Common Issues

1. **Tool not found**: Check if the tool is properly registered in the registry
2. **Permission denied**: Verify the path is in the allowed directories list
3. **Timeout errors**: Increase the timeout for long-running operations
4. **Parameter validation errors**: Check the tool schema for required parameters

### Debug Mode

Enable debug logging to see detailed tool execution:
```python
import logging
logging.getLogger("tools").setLevel(logging.DEBUG)
```

## Future Enhancements

- [ ] Database tool implementation with connection pooling
- [ ] Web scraping tool with BeautifulSoup
- [ ] Advanced file operations (zip, unzip, etc.)
- [ ] Image processing tools
- [ ] Email sending tool
- [ ] Caching layer for frequently used tools
- [ ] Tool composition and chaining
- [ ] Rate limiting for external API calls