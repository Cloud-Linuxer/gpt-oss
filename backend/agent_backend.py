#!/usr/bin/env python3
"""LLM 기반 에이전트 백엔드 - Galaxy AI Assistant"""

import json
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Import all tools
from tools import (
    ToolRegistry,
    FileReadTool, FileWriteTool, FileListTool,
    SystemInfoTool, ProcessListTool, EnvironmentTool,
    CalculatorTool, StatisticsTool,
    JSONParseTool, JSONQueryTool, DataTransformTool,
    APIRequestTool, WebScrapeTool,
    DatabaseQueryTool, DatabaseExecuteTool,
    TimeTool
)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Galaxy AI Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# vLLM 설정
VLLM_URL = "http://localhost:8000/v1"
MODEL_NAME = "openai/gpt-oss-20b"

# 글로벌 도구 레지스트리
tool_registry = None

def initialize_tools():
    """도구 시스템 초기화"""
    registry = ToolRegistry()
    
    # 파일 도구들
    registry.register(FileReadTool(), category="file")
    registry.register(FileWriteTool(), category="file")
    registry.register(FileListTool(), category="file")
    
    # 시스템 도구들
    registry.register(SystemInfoTool(), category="system")
    registry.register(ProcessListTool(), category="system")
    registry.register(EnvironmentTool(), category="system")
    
    # 수학 도구들
    registry.register(CalculatorTool(), category="math")
    registry.register(StatisticsTool(), category="math")
    
    # 데이터 도구들
    registry.register(JSONParseTool(), category="data")
    registry.register(JSONQueryTool(), category="data")
    registry.register(DataTransformTool(), category="data")
    
    # 웹 도구들
    registry.register(APIRequestTool(), category="web")
    registry.register(WebScrapeTool(), category="web")
    
    # 데이터베이스 도구들
    registry.register(DatabaseQueryTool(), category="database")
    registry.register(DatabaseExecuteTool(), category="database")
    
    # 유틸리티 도구들
    registry.register(TimeTool(), category="utility")
    
    logger.info(f"Initialized {len(registry.list_tools())} tools")
    return registry

@app.on_event("startup")
async def startup():
    global tool_registry
    tool_registry = initialize_tools()

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    response: str
    tools_used: List[Dict[str, Any]] = []
    tokens_used: int = 0

async def call_vllm(messages: List[Dict[str, str]], max_tokens: int = 8192, use_tools: bool = True) -> Dict[str, Any]:
    """vLLM 모델 호출"""
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0
        }
        
        # Method 3: OpenAI function calling 형식으로 도구 정의
        if use_tools:
            tools_definition = [
                {
                    "type": "function",
                    "function": {
                        "name": "calculator",
                        "description": "수학 계산을 수행합니다",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "expression": {
                                    "type": "string",
                                    "description": "계산할 수학 표현식"
                                }
                            },
                            "required": ["expression"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "time_now",
                        "description": "현재 시간을 조회합니다",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "timezone": {
                                    "type": "string",
                                    "description": "시간대 (기본: Seoul)"
                                }
                            }
                        }
                    }
                }
            ]
            payload["tools"] = tools_definition
            # Method 7: 강제 도구 호출 테스트
            payload["tool_choice"] = {
                "type": "function", 
                "function": {"name": "calculator"}
            }
        
        logger.debug(f"vLLM 요청 페이로드: {payload}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{VLLM_URL}/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            logger.debug(f"vLLM 응답 상태코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"vLLM 응답 성공: {result}")
                return result
            else:
                error_text = response.text
                logger.error(f"vLLM 오류 응답: {error_text}")
                logger.error(f"vLLM 요청 헤더: {response.request.headers}")
                raise Exception(f"vLLM 오류: {response.status_code} - {error_text}")
                
    except Exception as e:
        logger.error(f"vLLM 호출 오류 상세: {str(e)}", exc_info=True)
        raise

async def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """도구 실행"""
    try:
        logger.debug(f"도구 실행 요청: {tool_name}, 파라미터: {parameters}")
        
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            error_msg = f"도구 '{tool_name}'을 찾을 수 없습니다"
            logger.error(error_msg)
            return {"error": error_msg}
        
        logger.debug(f"도구 '{tool_name}' 실행 시작")
        result = await tool.execute(**parameters)
        
        logger.debug(f"도구 '{tool_name}' 실행 완료: 상태={result.status.value}")
        
        return {
            "tool": tool_name,
            "status": result.status.value,
            "data": result.data,
            "error": result.error
        }
    except Exception as e:
        logger.error(f"도구 '{tool_name}' 실행 오류 상세: {str(e)}", exc_info=True)
        return {"error": str(e)}

def create_system_prompt() -> str:
    """Galaxy 시스템 프롬프트 생성 - GPT-OSS 도구 호출 형식"""
    return """You are Galaxy, a friendly AI assistant. 

When you need to use tools, use this exact format:
function_call: tool_name(parameter=value)

Available tools:
- calculator(expression): for mathematical calculations
- time_now(timezone): for time queries (default: Seoul)

Always use tools when needed and respond in a friendly manner."""

async def process_llm_response(llm_response: str, llm_result: Dict[str, Any]) -> Dict[str, Any]:
    """LLM 응답 처리 및 도구 호출 - Method 3: OpenAI tool_calls 처리"""
    tools_used = []
    
    # Method 3: OpenAI tool_calls 확인
    if "choices" in llm_result and len(llm_result["choices"]) > 0:
        choice = llm_result["choices"][0]
        message = choice.get("message", {})
        tool_calls = message.get("tool_calls", [])
        
        logger.debug(f"OpenAI tool_calls 발견: {len(tool_calls)}개")
        
        if tool_calls:
            for tool_call in tool_calls:
                try:
                    function_info = tool_call.get("function", {})
                    tool_name = function_info.get("name")
                    arguments_str = function_info.get("arguments", "{}")
                    
                    # JSON 파라미터 파싱
                    import json
                    params = json.loads(arguments_str) if arguments_str else {}
                    
                    logger.debug(f"OpenAI 도구 호출: {tool_name}, 파라미터: {params}")
                    
                    # 도구 실행
                    tool_result = await execute_tool(tool_name, params)
                    tools_used.append(tool_result)
                    
                except Exception as e:
                    logger.error(f"OpenAI 도구 호출 처리 오류: {e}")
    
    # 기존 패턴 매칭도 유지 (fallback)
    if not tools_used:
        import re
        
        # 패턴 1: function_call: tool_name(param=value)
        pattern1 = r'function_call:\s*(\w+)\s*\((.*?)\)'
        matches1 = re.findall(pattern1, llm_response, re.DOTALL)
        
        # 패턴 2: tool_name(param=value) - 더 자연스러운 형태
        pattern2 = r'(?:^|\n)\s*(\w+)\s*\(([^)]+)\)'
        matches2 = re.findall(pattern2, llm_response, re.MULTILINE)
        
        all_matches = matches1 + matches2
        
        logger.debug(f"Fallback 패턴 매칭 결과: Pattern1={len(matches1)}, Pattern2={len(matches2)}")
        logger.debug(f"LLM 응답 내용: {llm_response}")
        
        if all_matches:
            for tool_name, params_str in all_matches:
                try:
                    # 도구 이름이 실제로 존재하는지 확인
                    available_tools = ['calculator', 'time_now', 'system_info', 'file_read', 'file_write', 'file_list']
                    if tool_name not in available_tools:
                        logger.debug(f"도구 '{tool_name}'가 사용 가능한 도구 목록에 없음: {available_tools}")
                        continue
                    
                    # 파라미터 파싱
                    params = {}
                    if params_str.strip():
                        for param in params_str.split(','):
                            if '=' in param:
                                key, value = param.split('=', 1)
                                key = key.strip().strip('"\'')
                                value = value.strip().strip('"\'')
                                params[key] = value
                            else:
                                # 단일 파라미터인 경우
                                clean_param = params_str.strip().strip('"\'')
                                if tool_name == 'calculator':
                                    params['expression'] = clean_param
                                elif tool_name == 'time_now':
                                    params['timezone'] = clean_param if clean_param else 'Seoul'
                    
                    logger.debug(f"Fallback 도구 호출 시도: {tool_name}, 파라미터: {params}")
                    
                    # 도구 실행
                    tool_result = await execute_tool(tool_name, params)
                    tools_used.append(tool_result)
                    
                except Exception as e:
                    logger.error(f"Fallback 도구 호출 파싱 오류: {e}")
    
    return {
        "response": llm_response,
        "tools_used": tools_used
    }

@app.get("/")
async def root():
    return {
        "service": "Galaxy AI Agent",
        "status": "running",
        "tools_available": len(tool_registry.list_tools()) if tool_registry else 0,
        "model": MODEL_NAME
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "vllm_connected": True}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Galaxy AI와 채팅"""
    try:
        logger.debug(f"채팅 요청 수신: 메시지='{request.message}', 히스토리 길이={len(request.history)}")
        
        # Method 8: 시스템 프롬프트 없이 도구만 제공
        messages = []
        
        # 이전 대화 히스토리 추가
        for msg in request.history[-10:]:  # 최근 10개만
            messages.append(msg)
        
        # 현재 사용자 메시지 추가
        messages.append({"role": "user", "content": request.message})
        
        logger.debug(f"vLLM 호출 준비: 총 메시지 수={len(messages)}")
        
        # vLLM 호출
        llm_result = await call_vllm(messages)
        
        if "choices" not in llm_result or len(llm_result["choices"]) == 0:
            logger.error(f"LLM 응답 형식 오류: {llm_result}")
            raise HTTPException(status_code=500, detail="LLM 응답 오류")
        
        ai_response = llm_result["choices"][0]["message"]["content"]
        tokens_used = llm_result.get("usage", {}).get("total_tokens", 0)
        
        logger.debug(f"LLM 응답 수신: 길이={len(ai_response)}, 토큰={tokens_used}")
        
        # 도구 호출 처리
        processed = await process_llm_response(ai_response, llm_result)
        
        logger.debug(f"도구 처리 완료: 사용된 도구 수={len(processed['tools_used'])}")
        
        return ChatResponse(
            response=processed["response"],
            tools_used=processed["tools_used"],
            tokens_used=tokens_used
        )
        
    except Exception as e:
        logger.error(f"채팅 처리 오류 상세: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"채팅 오류: {str(e)}")

@app.get("/tools")
async def list_tools():
    """사용 가능한 도구 목록"""
    tools = []
    for tool_name, tool in tool_registry._tools.items():
        schema = tool.get_schema()
        tools.append({
            "name": tool_name,
            "description": schema["function"]["description"],
            "category": getattr(tool, 'category', 'unknown')
        })
    return {"tools": tools, "total": len(tools)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)