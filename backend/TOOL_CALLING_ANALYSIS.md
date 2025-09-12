# Tool Calling Analysis Results

## 🔍 Current Status Summary

**Date**: 2025-09-12  
**Model**: openai/gpt-oss-20b  
**vLLM Version**: v0.10.1.1  
**Backend Status**: ✅ Running (Docker, 16 tools available)  

## 🧪 Test Results

### Test 1: Basic Tool Choice (Auto)
```json
{
  "model": "openai/gpt-oss-20b",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant. Use tools when available."},
    {"role": "user", "content": "Calculate 25 * 4"}
  ],
  "tools": [/* calculator tool */],
  "tool_choice": "auto"
}
```
**Result**: ❌ `"tool_calls": []` - Empty array
**Model Response**: Direct calculation with reasoning_content but no tool calls

### Test 2: Forced Function Call
```json
{
  "tool_choice": {
    "type": "function",
    "function": {"name": "calculator"}
  }
}
```
**Result**: ❌ HTTP 500 Internal Server Error

### Test 3: Complex Weather Task
```json
{
  "messages": [
    {"role": "user", "content": "서울·부산·뉴욕의 현재 기온과 체감온도를 섭씨로 조회해 평균/최댓값을 함께 요약해줘. 각 도시는 반드시 get_weather 함수로 조회해."}
  ],
  "tool_choice": "auto"
}
```
**Result**: ❌ HTTP 500 Internal Server Error

## 📋 Key Findings

### ✅ Working Components
- **Request Format**: OpenAI-compatible JSON format correct
- **Backend API**: 16 tools available via Docker container
- **Model Loading**: gpt-oss-20b loads successfully
- **Basic Chat**: Non-tool requests work fine

### ❌ Failing Components  
- **Tool Choice Auto**: Always returns empty tool_calls array
- **Forced Tool Choice**: HTTP 500 errors with specific function targeting
- **Tool Parser**: Hermes parser causes loading failures

### 🔬 vLLM Logs Analysis
```
WARNING: For gpt-oss, we ignore --enable-auto-tool-choice and always enable tool use.
```
**Interpretation**: vLLM acknowledges tool capability but model itself lacks proper tool calling training

## 🎯 Root Cause Analysis

**Primary Issue**: `gpt-oss-20b` model has insufficient tool calling training
- Model can understand tools exist (shows in reasoning_content)
- Cannot generate proper OpenAI tool_calls format
- vLLM parser conflicts when forcing specific functions

**Evidence**:
1. `reasoning_content` shows model thinks about tools
2. `tool_calls` always empty regardless of strategy
3. Forced function calls trigger server errors
4. Parser restart attempts fail to load

## 🔄 Attempted Solutions

### Strategy 1: Gentle Guidance
- **Approach**: Soft prompting to prefer tools
- **Result**: ❌ Failed - no tool calls generated

### Strategy 2: Complexity Induction  
- **Approach**: Complex multi-step tasks requiring tools
- **Result**: ❌ Failed - HTTP 500 errors

### Strategy 3: Explicit Requirements
- **Approach**: User message explicitly requiring tool use
- **Result**: ❌ Failed - request parsing errors

### Strategy 4: Fallback Retry
- **Approach**: Retry with hints if no tools detected
- **Result**: ❌ Failed - first request already errors

### Strategy 5: Forced Tool Choice
- **Approach**: Specific function targeting
- **Result**: ❌ Failed - HTTP 500 server errors

## 📊 Test Statistics
- **Total Strategies Tested**: 5
- **Success Rate**: 0/5 (0%)
- **Common Failure**: `tool_calls: []` or HTTP 500

## 🛠️ Recommended Next Steps

### Option 1: Native Approach (Retry)
Try different parser options:
```bash
# Test different parsers
vllm serve openai/gpt-oss-20b --tool-call-parser openai
vllm serve openai/gpt-oss-20b --tool-call-parser none  
vllm serve openai/gpt-oss-20b --enable-auto-tool-choice
```

### Option 2: Emulation Approach (Fallback)
Implement wrapper that:
1. Detects tool intent from model text output
2. Parses tool name/parameters manually  
3. Wraps in OpenAI tool_calls format
4. Maintains API compatibility

### Option 3: Model Replacement
Switch to tool-calling trained model:
- Hermes-2.5-Mistral-7B
- CodeLlama-Instruct
- Mixtral-8x7B-Instruct

## 🔧 Emulation Implementation Plan

If native fails, implement:
```python
def emulate_tool_calls(model_response, available_tools):
    # Parse model text for tool intentions
    # Extract tool_name and parameters
    # Format as OpenAI tool_calls structure
    # Return compatible response
```

## 📝 Current Configuration

**vLLM Command**:
```bash
python3 -m vllm.entrypoints.openai.api_server \
  --model openai/gpt-oss-20b \
  --dtype auto \
  --gpu-memory-utilization 0.8
```

**Backend Tools Available**:
- calculator, system_info, file_read, file_write, file_list
- process_list, env_get, statistics, json_parse, json_query
- data_transform, api_request, web_scrape, database_query, database_execute, time_tool

**Container Status**: 
- vLLM: ✅ Running (port 8000)  
- Backend: ✅ Running (port 8001)
- Health checks: ✅ Passing

---
*Analysis generated on 2025-09-12*