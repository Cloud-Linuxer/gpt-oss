# Tool Calling JSON Flow Example
## Frontend → Backend → vLLM → Tool Execution

This document demonstrates the complete JSON request/response flow for the question "현재시간몇시야?" (What time is it now?)

---

## 1. Frontend → Backend Request

**Endpoint**: `POST http://localhost:8080/api/chat`

### Request
```json
{
  "message": "현재시간몇시야?",
  "use_tools": true
}
```

---

## 2. Backend → vLLM Request

**Endpoint**: `POST http://vllm:8000/v1/chat/completions`

### Request
```json
{
  "model": "openai/gpt-oss-20b",
  "messages": [
    {
      "role": "system",
      "content": "한국어로 간결하게 답해. 필요한 경우 도구를 사용할 수 있습니다."
    },
    {
      "role": "user",
      "content": "현재시간몇시야?"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_current_time",
        "description": "Get the current system time",
        "parameters": {
          "type": "object",
          "properties": {
            "timezone": {
              "type": "string",
              "description": "Timezone (e.g., 'Asia/Seoul', 'UTC')",
              "default": "Asia/Seoul"
            },
            "format": {
              "type": "string",
              "description": "Time format ('24h' or '12h')",
              "default": "24h"
            }
          },
          "required": []
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "system_info",
        "description": "Get system information including OS, CPU, memory, and current time",
        "parameters": {
          "type": "object",
          "properties": {
            "include_processes": {
              "type": "boolean",
              "description": "Include running processes",
              "default": false
            }
          },
          "required": []
        }
      }
    }
  ],
  "tool_choice": "auto",
  "max_tokens": 1000,
  "temperature": 0.3,
  "frequency_penalty": 0.2
}
```

---

## 3. vLLM → Backend Response (Tool Call)

### Response
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1735892400,
  "model": "openai/gpt-oss-20b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_xyz789",
            "type": "function",
            "function": {
              "name": "get_current_time",
              "arguments": "{\"timezone\": \"Asia/Seoul\", \"format\": \"24h\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 145,
    "completion_tokens": 28,
    "total_tokens": 173
  }
}
```

---

## 4. Backend Tool Execution

### Internal Tool Registry Call
```python
# Backend executes:
tool_registry.execute_tool(
    "get_current_time",
    timezone="Asia/Seoul",
    format="24h"
)
```

### Tool Result
```json
{
  "status": "success",
  "data": {
    "current_time": "2025-01-03 14:35:22",
    "timezone": "Asia/Seoul",
    "timestamp": 1735892122,
    "day_of_week": "Friday"
  },
  "error": null,
  "metadata": {
    "execution_time_ms": 5,
    "tool_version": "1.0.0"
  }
}
```

---

## 5. Backend → vLLM (Tool Result + Follow-up)

### Request with Tool Result
```json
{
  "model": "openai/gpt-oss-20b",
  "messages": [
    {
      "role": "system",
      "content": "한국어로 간결하게 답해. 필요한 경우 도구를 사용할 수 있습니다."
    },
    {
      "role": "user",
      "content": "현재시간몇시야?"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_xyz789",
          "type": "function",
          "function": {
            "name": "get_current_time",
            "arguments": "{\"timezone\": \"Asia/Seoul\", \"format\": \"24h\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_xyz789",
      "name": "get_current_time",
      "content": "{\"current_time\": \"2025-01-03 14:35:22\", \"timezone\": \"Asia/Seoul\", \"timestamp\": 1735892122, \"day_of_week\": \"Friday\"}"
    }
  ],
  "tools": [...],  // Same tools as before
  "tool_choice": "auto",
  "max_tokens": 1000,
  "temperature": 0.3
}
```

---

## 6. vLLM → Backend Final Response

### Response
```json
{
  "id": "chatcmpl-def456",
  "object": "chat.completion",
  "created": 1735892401,
  "model": "openai/gpt-oss-20b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "현재 한국 시간은 오후 2시 35분 22초입니다. (2025년 1월 3일 금요일)"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 198,
    "completion_tokens": 32,
    "total_tokens": 230
  }
}
```

---

## 7. Backend → Frontend Final Response

### Response
```json
{
  "response": "현재 한국 시간은 오후 2시 35분 22초입니다. (2025년 1월 3일 금요일)",
  "tools_used": ["get_current_time"]
}
```

---

## Summary

### Request Flow
1. **User Input**: "현재시간몇시야?"
2. **Frontend**: Sends to backend API
3. **Backend**: Prepares tool schemas and sends to vLLM
4. **vLLM**: Decides to use `get_current_time` tool
5. **Backend**: Executes tool and gets current time
6. **Backend**: Sends tool result back to vLLM
7. **vLLM**: Generates natural language response
8. **Backend**: Returns final response to frontend
9. **Frontend**: Displays to user

### Key Points
- **Tool Decision**: vLLM autonomously decides which tool to use based on the question
- **Parameter Inference**: vLLM infers appropriate parameters (timezone: Asia/Seoul)
- **Natural Language**: Final response is in natural Korean language
- **Metadata Tracking**: Tools used are tracked for debugging/logging

### Total Latency Breakdown
- Frontend → Backend: ~5ms
- Backend → vLLM (initial): ~200ms
- Tool Execution: ~5ms
- Backend → vLLM (follow-up): ~150ms
- Backend → Frontend: ~5ms
- **Total**: ~365ms

### Token Usage
- First vLLM call: 173 tokens
- Second vLLM call: 230 tokens
- **Total**: 403 tokens