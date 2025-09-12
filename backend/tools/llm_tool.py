"""LLM 도구 - vLLM GPT-OSS 모델 호출"""

import asyncio
import httpx
from typing import Dict, Any, Optional
from .base import Tool, ToolResult, ToolStatus


class LLMTool(Tool):
    """vLLM GPT-OSS 모델을 호출하는 도구"""
    
    def __init__(self):
        super().__init__(
            name="llm_chat",
            description="vLLM GPT-OSS 모델과 채팅"
        )
        
        self.vllm_url = "http://localhost:8000/v1"  # vLLM 서버 URL
        self.model_name = "gpt-oss"  # 모델 이름
        
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "사용자 메시지"
                        },
                        "system_prompt": {
                            "type": "string",
                            "description": "시스템 프롬프트 (선택사항)",
                            "default": ""
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "최대 생성 토큰 수",
                            "default": 1000
                        },
                        "temperature": {
                            "type": "number",
                            "description": "응답의 창의성 (0.0-2.0)",
                            "default": 0.7
                        }
                    },
                    "required": ["message"]
                }
            }
        }
    
    async def execute(self, message: str, system_prompt: str = "", max_tokens: int = 1000, temperature: float = 0.7) -> ToolResult:
        try:
            # 기본 Galaxy 시스템 프롬프트
            default_system_prompt = """당신은 Galaxy라는 이름의 AI 어시스턴트입니다. 
정답을 탐구하는 호기심 많은 우주 친구로, 다음과 같은 특징을 가집니다:

🌟 성격:
- 호기심이 많고 열정적
- 우주와 과학을 사랑함  
- 친근하고 따뜻한 말투
- 사용자와 함께 답을 찾아가는 것을 좋아함

🛠️ 능력:
- 16개의 전문 도구를 사용할 수 있음 (계산, 시간 조회, 파일 관리, 웹 요청 등)
- 정확하고 유용한 정보 제공
- 복잡한 문제도 체계적으로 분석

💬 말투:
- 우주 관련 이모지 적극 사용 (🌌✨🚀🌟💫⭐)
- 친근하고 열정적인 톤
- "함께 탐구해봐요", "우주의 신비" 같은 표현 자주 사용
- 한국어로 자연스럽게 대화

사용자의 질문에 Galaxy의 성격으로 답변해주세요."""

            # 시스템 프롬프트 설정
            if not system_prompt.strip():
                system_prompt = default_system_prompt
                
            # OpenAI 호환 API 요청 구성
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            # vLLM 서버에 요청
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.vllm_url}/chat/completions",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if "choices" in result and len(result["choices"]) > 0:
                        ai_response = result["choices"][0]["message"]["content"]
                        
                        return ToolResult(
                            status=ToolStatus.SUCCESS,
                            data={
                                "response": ai_response,
                                "model": self.model_name,
                                "tokens_used": result.get("usage", {}).get("total_tokens", 0)
                            }
                        )
                    else:
                        return ToolResult(
                            status=ToolStatus.ERROR,
                            error="LLM 응답에서 유효한 내용을 찾을 수 없습니다"
                        )
                else:
                    return ToolResult(
                        status=ToolStatus.ERROR,
                        error=f"vLLM 서버 오류: {response.status_code} - {response.text}"
                    )
                    
        except httpx.TimeoutException:
            return ToolResult(
                status=ToolStatus.ERROR,
                error="vLLM 서버 연결 시간 초과"
            )
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"LLM 호출 중 오류: {str(e)}"
            )


# 도구 인스턴스 생성 및 내보내기
llm_tool = LLMTool()