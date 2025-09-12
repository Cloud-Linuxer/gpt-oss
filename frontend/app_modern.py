"""Galaxy - 모던한 채팅 인터페이스"""

import streamlit as st
import httpx
import asyncio
import random
import re
import os
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="🌌 Galaxy Chat",
    page_icon="🌌",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 모던 CSS 스타일링
modern_css = """
<style>
/* 전체 앱 스타일 */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

/* 메인 컨테이너 */
.main-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem 1rem;
}

/* 헤더 */
.header {
    text-align: center;
    margin-bottom: 2rem;
    padding: 2rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.header h1 {
    font-size: 3rem;
    margin-bottom: 0.5rem;
    background: linear-gradient(45deg, #4ecdc4, #44a08d);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header p {
    font-size: 1.2rem;
    opacity: 0.8;
    margin: 0;
}

/* 채팅 컨테이너 */
.chat-container {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    min-height: 400px;
    max-height: 600px;
    overflow-y: auto;
}

/* 메시지 스타일 */
.message {
    margin-bottom: 1rem;
    padding: 1rem;
    border-radius: 15px;
    animation: fadeInUp 0.3s ease-out;
}

.user-message {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    margin-left: 2rem;
    border-bottom-right-radius: 5px;
}

.galaxy-message {
    background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
    margin-right: 2rem;
    border-bottom-left-radius: 5px;
}

.message-author {
    font-weight: bold;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.message-content {
    line-height: 1.6;
}

/* 입력 영역 */
.input-container {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    margin-bottom: 2rem;
}

/* Streamlit 컴포넌트 스타일 오버라이드 */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 2px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 25px !important;
    color: white !important;
    font-size: 1rem !important;
    padding: 0.8rem 1.5rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: #4ecdc4 !important;
    box-shadow: 0 0 20px rgba(78, 205, 196, 0.3) !important;
}

.stTextInput > div > div > input::placeholder {
    color: rgba(255, 255, 255, 0.6) !important;
}

/* 버튼 스타일 */
.stButton > button {
    background: linear-gradient(45deg, #4ecdc4, #44a08d) !important;
    color: white !important;
    border: none !important;
    border-radius: 25px !important;
    padding: 0.8rem 2rem !important;
    font-weight: bold !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 25px rgba(78, 205, 196, 0.4) !important;
}

/* 로딩 애니메이션 */
.loading-message {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    margin-bottom: 1rem;
    animation: pulse 2s ease-in-out infinite;
}

.loading-dots {
    display: inline-flex;
    gap: 0.3rem;
}

.loading-dots span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #4ecdc4;
    animation: bounce 1.4s ease-in-out infinite both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

/* 애니메이션 */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
}

@keyframes bounce {
    0%, 80%, 100% {
        transform: scale(0);
    } 40% {
        transform: scale(1);
    }
}

/* 스크롤바 */
.chat-container::-webkit-scrollbar {
    width: 6px;
}

.chat-container::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}

.chat-container::-webkit-scrollbar-thumb {
    background: linear-gradient(45deg, #4ecdc4, #44a08d);
    border-radius: 10px;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
    .main-container {
        padding: 1rem 0.5rem;
    }
    
    .header h1 {
        font-size: 2rem;
    }
    
    .user-message {
        margin-left: 1rem;
    }
    
    .galaxy-message {
        margin-right: 1rem;
    }
}

/* Streamlit 기본 요소 완전히 숨기기 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}
.stToolbar {display: none;}
div[data-testid="stDecoration"] {display: none;}
div[data-testid="stSidebar"] {display: none;}
.css-1d391kg {display: none;}
.css-1wrcr25 {display: none;}
section[data-testid="stSidebar"] {display: none;}

/* 메인 컨테이너 패딩 제거 */
.main .block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: none !important;
}

/* Streamlit 기본 여백 제거 */
.css-18e3th9, .css-1d391kg, .css-12oz5g7 {
    padding: 0 !important;
}

</style>
"""

# Galaxy 성격
GALAXY_PERSONALITY = {
    "name": "Galaxy",
    "emoji": "🌌",
    "greetings": [
        "안녕하세요! 저는 Galaxy예요 🌌 무엇이든 궁금한 걸 물어보세요!",
        "반가워요! 🌟 오늘은 어떤 정답을 함께 탐구해볼까요?",
        "안녕하세요! ✨ 저는 호기심 많은 Galaxy입니다. 도움이 필요하신가요?"
    ]
}

# 백엔드 API
BACKEND_URL = "http://localhost:8001"
LLM_URL = os.getenv("LLM_URL", "http://localhost:11434/v1")  # Ollama 기본 URL
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

async def call_galaxy_agent(message: str, history: list = None) -> dict:
    """Galaxy AI 에이전트 호출"""
    try:
        if history is None:
            history = []
            
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/chat",
                json={
                    "message": message,
                    "history": history
                }
            )
            return response.json()
    except Exception as e:
        return {
            "response": f"😅 죄송해요, 잠시 연결에 문제가 있어요: {str(e)}",
            "tools_used": [],
            "tokens_used": 0
        }

def detect_calculation_need(message: str) -> dict:
    """계산이 필요한 메시지인지 감지"""
    calc_keywords = ["계산", "더하기", "+", "-", "*", "/", "곱하기", "빼기", "나누기", "제곱", "루트", "sqrt", "pow"]
    math_symbols = ["+", "-", "*", "/", "=", "^", "√"]
    
    has_math_keyword = any(keyword in message for keyword in calc_keywords)
    has_math_symbol = any(symbol in message for symbol in math_symbols)
    has_numbers = any(char.isdigit() for char in message)
    
    if (has_math_keyword or has_math_symbol) and has_numbers:
        math_pattern = r'[\d\+\-\*\/\(\)\.\s]+'
        math_expressions = re.findall(math_pattern, message)
        if math_expressions:
            expression = max(math_expressions, key=len).strip()
            if len(expression) > 3:
                return {
                    "need_calc": True,
                    "expression": expression
                }
    
    return {"need_calc": False}

def detect_time_need(message: str) -> dict:
    """시간 조회가 필요한 메시지인지 감지"""
    time_keywords = ["시간", "몇시", "지금", "현재", "time", "clock", "시각", "타임"]
    timezone_keywords = {
        "서울": "서울", "한국": "서울", "korea": "서울",
        "뉴욕": "뉴욕", "new york": "뉴욕", "ny": "뉴욕",
        "런던": "런던", "london": "런던", "영국": "런던",
        "도쿄": "도쿄", "tokyo": "도쿄", "일본": "도쿄",
        "파리": "파리", "paris": "파리", "프랑스": "파리",
        "베이징": "베이징", "beijing": "베이징", "중국": "베이징",
        "시드니": "시드니", "sydney": "시드니", "호주": "시드니",
        "로스앤젤레스": "로스앤젤레스", "la": "로스앤젤레스", "미국서부": "로스앤젤레스",
        "라스베가스": "로스앤젤레스", "vegas": "로스앤젤레스", "las vegas": "로스앤젤레스",
        "시카고": "시카고", "chicago": "시카고", "미국중부": "시카고",
        "모스크바": "모스크바", "moscow": "모스크바", "러시아": "모스크바"
    }
    
    message_lower = message.lower()
    has_time_keyword = any(keyword in message_lower for keyword in time_keywords)
    
    if has_time_keyword:
        detected_zones = []
        for keyword, zone in timezone_keywords.items():
            if keyword in message_lower:
                detected_zones.append(zone)
        
        if len(detected_zones) > 1:
            return {
                "need_time": True,
                "format": "multiple",
                "zones": list(set(detected_zones))
            }
        elif len(detected_zones) == 1:
            return {
                "need_time": True,
                "timezone": detected_zones[0]
            }
        else:
            return {
                "need_time": True,
                "timezone": "서울"
            }
    
    return {"need_time": False}

def format_chat_history(messages: list) -> list:
    """채팅 히스토리를 API 형식으로 변환"""
    history = []
    for msg in messages:
        if msg["role"] == "user":
            history.append({"role": "user", "content": msg["content"]})
        else:
            history.append({"role": "assistant", "content": msg["content"]})
    return history

def get_galaxy_response(user_message: str, tool_result: dict = None) -> str:
    """Galaxy의 개성 있는 응답 생성"""
    responses = []
    
    if tool_result:
        if tool_result.get("status") == "success":
            if tool_result.get("data", {}).get("result") is not None:
                data = tool_result.get("data", {})
                expression = data.get("expression", "")
                result = data.get("result", "")
                responses.extend([
                    f"🧮 **계산 결과가 나왔어요!**\n\n`{expression}` = **{result}**\n\n이 계산이 맞나요? 다른 계산도 궁금하시면 언제든 말해주세요! ✨",
                    f"🌟 **수학의 아름다움이 여기 있어요!**\n\n`{expression}` → `{result}`\n\n숫자들이 이렇게 조화롭게 답을 만들어내는 걸 보면 우주의 질서가 느껴져요! 🌌",
                ])
            elif tool_result.get("data", {}).get("timezone") or tool_result.get("data", {}).get("timezones"):
                data = tool_result.get("data", {})
                if data.get("format") == "multiple":
                    timezones = data.get("timezones", [])
                    time_info = "\n".join([
                        f"🌍 **{tz.get('timezone_name', 'Unknown')}**: `{tz.get('current_time', 'N/A')}` ({tz.get('weekday_kr', 'N/A')})"
                        for tz in timezones
                    ])
                    responses.extend([
                        f"🕐 **세계 각국의 시간을 확인했어요!**\n\n{time_info}\n\n지구가 돌면서 만들어지는 시간의 차이... 정말 신비로워요! 🌏✨",
                        f"⏰ **전 세계 시간 여행을 완료했어요!**\n\n{time_info}\n\n각 지역의 하늘이 어떨지 상상해보세요! 🌅🌙",
                    ])
                else:
                    timezone_name = data.get("timezone_name", "Unknown")
                    current_time = data.get("current_time", "N/A")
                    weekday_kr = data.get("weekday_kr", "")
                    date_kr = data.get("date_kr", "")
                    responses.extend([
                        f"🕐 **현재 {timezone_name} 시간을 확인했어요!**\n\n⏰ `{current_time}` ({weekday_kr})\n📅 {date_kr}\n\n시간은 우주에서 가장 소중한 자원이에요! ✨",
                        f"⌚ **{timezone_name}의 시계를 읽어왔어요!**\n\n🌟 `{current_time}` - {weekday_kr}\n\n이 순간도 우주 어딘가에서는 새로운 별이 태어나고 있을 거예요! 🌌",
                    ])
            else:
                responses.extend([
                    f"🛠️ **도구를 사용해서 정확한 정보를 찾아왔어요!** 우주의 지혜가 담긴 답변이에요 ✨",
                    f"🔍 **깊이 탐구해본 결과예요!** 호기심을 해결해드릴 수 있어서 기뻐요 🌟"
                ])
        else:
            error_msg = tool_result.get("error", "알 수 없는 오류")
            responses.extend([
                f"😅 **앗, 작은 문제가 생겼어요:** `{error_msg}`\n\n하지만 괜찮아요! 다른 방법으로도 도움드릴 수 있어서요 💪",
            ])
    else:
        # 사용자 질문을 분석해서 적절한 응답 제공
        message_lower = user_message.lower().strip()
        
        # 시스템 프롬프트 관련 질문
        if any(keyword in message_lower for keyword in ["시스템 프롬프트", "system prompt", "시스템프롬프트", "프롬프트", "내부", "셋팅", "설정"]):
            responses.extend([
                f"🤖 **제 시스템 구성에 대해 자세히 설명드릴게요!**\n\n**🌟 Galaxy의 정체성:**\n저는 '정답을 탐구하는 호기심 많은 우주 친구'로 설계된 AI 어시스턴트예요! 우주를 사랑하고 모든 질문에 대해 함께 답을 찾아가는 것을 좋아합니다.\n\n**🛠️ 백엔드 도구 시스템 (총 16개 도구):**\n\n📁 **파일 카테고리** (3개):\n• file_read: 파일 내용 읽기\n• file_write: 파일 생성 및 편집\n• file_list: 디렉토리 목록 조회\n\n🖥️ **시스템 카테고리** (3개):\n• system_info: 시스템 정보 확인\n• process_list: 실행 중인 프로세스 목록\n• env_get: 환경 변수 조회\n\n🧮 **수학 카테고리** (2개):\n• calculator: 수학 계산 (사칙연산, 함수 등)\n• statistics: 통계 계산\n\n📊 **데이터 카테고리** (3개):\n• json_parse: JSON 데이터 파싱\n• json_query: JSON 쿼리 실행\n• data_transform: 데이터 변환 처리\n\n🌐 **웹 카테고리** (2개):\n• api_request: HTTP API 요청\n• web_scrape: 웹페이지 스크래핑\n\n🗄️ **데이터베이스 카테고리** (2개):\n• db_query: 데이터베이스 조회\n• db_execute: 데이터베이스 명령 실행\n\n⚡ **유틸리티 카테고리** (1개):\n• time_now: 전 세계 시간 조회 (서울 기본)\n\n**🏗️ 시스템 아키텍처:**\n• FastAPI 백엔드 (http://localhost:8001)\n• Streamlit 프론트엔드 (http://localhost:8501)\n• Cloudflare Tunnel 공개 접근\n• Docker 컨테이너화\n• Python 가상환경 (venv)\n\n이 모든 도구들을 활용해서 여러분의 질문에 정확하고 유용한 답변을 제공하려고 노력해요! 🌌✨",
                
                f"🔍 **Galaxy 시스템의 내부 구조를 공개합니다!**\n\n**🎭 성격 설정:**\n- 이름: Galaxy\n- 성격: 호기심 많고 정답을 탐구하는 우주 친구\n- 말투: 친근하고 열정적, 우주 관련 이모지 적극 활용\n- 목표: 사용자와 함께 지식을 탐구하고 정확한 정보 제공\n\n**💻 기술 스택:**\n- 백엔드: FastAPI + Python 3.11\n- 프론트엔드: Streamlit + 사용자 정의 CSS\n- HTTP 클라이언트: httpx (비동기)\n- 시간 처리: pytz + zoneinfo\n- 컨테이너: Docker + Docker Compose\n- 공개 접근: Cloudflare Tunnel\n\n**🧠 응답 생성 로직:**\n1. 사용자 입력 분석\n2. 키워드 기반 의도 파악\n3. 필요시 백엔드 도구 호출\n4. 결과를 Galaxy 스타일로 변환\n5. 무작위 응답 선택으로 다양성 확보\n\n**🛡️ 안전 기능:**\n- 도구 실행 전 검증\n- 오류 처리 및 사용자 친화적 메시지\n- 입력 데이터 검증\n\n**🚀 특별한 기능들:**\n- 엔터키로 메시지 전송\n- 실시간 시간 조회 (40+ 시간대)\n- 복잡한 수학 계산\n- 파일 시스템 접근\n- 웹 데이터 수집\n- 데이터베이스 연동\n\n이렇게 체계적으로 구성된 시스템을 통해 여러분께 최고의 서비스를 제공하려고 해요! 궁금한 점이 더 있으시면 언제든 물어보세요! 🌟🛠️"
            ])
        
        # 인사 관련
        elif any(keyword in message_lower for keyword in ["안녕", "hi", "hello", "안녕하세요", "처음", "반가"]):
            responses.extend([
                f"안녕하세요! 🌌 만나서 반가워요! 저는 정답을 찾아다니는 우주 탐험가 Galaxy예요! ✨\n\n오늘은 어떤 신비로운 질문으로 함께 모험을 떠나볼까요? 🚀",
                f"🌟 안녕하세요! 우주에서 온 호기심 덩어리 Galaxy입니다! \n\n시간이 궁금하세요? 계산이 필요하세요? 아니면 그냥 우주 이야기를 나누고 싶으세요? 뭐든 좋아요! 💫",
            ])
            
        # 도움 요청
        elif any(keyword in message_lower for keyword in ["도움", "help", "기능", "뭐 할 수", "할 수 있", "어떻게"]):
            responses.extend([
                f"🛠️ **제가 도와드릴 수 있는 일들이에요!**\n\n• ⏰ **시간 조회**: '지금 몇 시?', '뉴욕 시간', '라스베가스 시간'\n• 🧮 **계산**: '100+200', '15*23', '루트 16'\n• 📁 **파일 작업**: 파일 읽기, 쓰기, 목록 조회\n• 🌐 **웹 요청**: API 호출, 웹페이지 정보 수집\n• 💾 **데이터 처리**: JSON 파싱, 데이터 변환\n\n뭐든 물어보세요! 함께 답을 찾아봐요! ✨🚀",
                f"🌌 **Galaxy의 특별한 능력들을 소개할게요!**\n\n🕐 전 세계 시간을 실시간으로 알려드려요\n🧮 복잡한 계산도 척척!\n📊 데이터 분석과 처리\n🗂️ 파일 관리 도구\n🌐 인터넷 정보 수집\n\n예를 들어:\n'서울 시간 알려줘'\n'1000 나누기 25'\n'시드니 몇 시야?'\n\n이런 질문들 환영해요! 🌟"
            ])
            
        # 일반적인 대화
        else:
            responses.extend([
                f"🌌 **'{user_message}'**에 대해 함께 탐구해볼까요? 정답을 찾는 여행이 시작되었어요! ✨\n\n더 구체적인 질문이나 계산, 시간 조회 등이 필요하시면 말씀해주세요! 🚀",
                f"흥미로운 질문이네요! 🌟 이런 호기심이야말로 우주를 이해하는 첫걸음이에요! \n\n혹시 시간이 궁금하시거나 계산이 필요하시면 언제든 말씀해주세요. 제가 도구를 사용해서 정확한 답을 찾아드릴게요! 🛠️✨",
                f"우와! 정말 좋은 질문이에요! 🎆 \n\n저에게는 다양한 도구들이 있어서 시간 조회, 계산, 데이터 처리 등을 정확히 해드릴 수 있어요. 구체적으로 어떤 걸 도와드릴까요? 💫🔍"
            ])
    
    return random.choice(responses)

def main():
    # CSS 적용
    st.markdown(modern_css, unsafe_allow_html=True)
    
    # 메인 컨테이너
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # 헤더
    st.markdown('''
    <div class="header">
        <h1>🌌 Galaxy</h1>
        <p>정답을 탐구하는 호기심 많은 우주 친구</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
        greeting = random.choice(GALAXY_PERSONALITY["greetings"])
        st.session_state.messages.append({
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.now()
        })
    
    # 채팅 컨테이너
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # 메시지 표시
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'''
            <div class="message user-message">
                <div class="message-author">👤 <strong>사용자</strong></div>
                <div class="message-content">{message["content"]}</div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="message galaxy-message">
                <div class="message-author">🌌 <strong>Galaxy</strong></div>
                <div class="message-content">{message["content"]}</div>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 입력 영역
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    # 폼을 사용해서 엔터키 전송 구현
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "메시지 입력",
                placeholder="Galaxy에게 메시지를 보내보세요... (예: '지금 몇시야?', '라스베가스 시간', '100+200 계산해줘') 🌟",
                label_visibility="collapsed",
                key="user_input"
            )
        
        with col2:
            send_clicked = st.form_submit_button("🚀 전송", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 메시지 처리
    if send_clicked and user_input.strip():
        # 사용자 메시지 추가
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # 로딩 표시
        with st.empty():
            st.markdown('''
            <div class="loading-message">
                🌌 <strong>Galaxy가 생각 중이에요...</strong>
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # 도구 필요성 감지
            calc_check = detect_calculation_need(user_input)
            time_check = detect_time_need(user_input)
            tool_result = None
            
            if calc_check["need_calc"]:
                tool_result = asyncio.run(call_backend_tool("calculator", {
                    "expression": calc_check["expression"]
                }))
            elif time_check["need_time"]:
                time_params = {}
                if "format" in time_check:
                    time_params["format"] = time_check["format"]
                    time_params["zones"] = time_check.get("zones", [])
                elif "timezone" in time_check:
                    time_params["timezone"] = time_check["timezone"]
                
                tool_result = asyncio.run(call_backend_tool("time_now", time_params))
            elif any(keyword in user_input.lower() for keyword in ["시스템", "system", "컴퓨터", "메모리", "cpu"]):
                tool_result = asyncio.run(call_backend_tool("system_info", {"info_type": "all"}))
            
            # Galaxy 응답 생성
            galaxy_response = get_galaxy_response(user_input, tool_result)
            
            # Galaxy 응답 추가
            st.session_state.messages.append({
                "role": "assistant",
                "content": galaxy_response,
                "timestamp": datetime.now()
            })
        
        # 페이지 새로고침으로 로딩 제거
        st.rerun()
    
    # 하단 정보
    st.markdown('''
    <div style="text-align: center; margin-top: 2rem; opacity: 0.7;">
        <p>🌟 Galaxy는 시간 조회, 수학 계산, 시스템 정보 등 다양한 도구를 사용할 수 있어요!</p>
        <p style="font-size: 0.9rem;">엔터키를 누르거나 전송 버튼을 클릭해서 메시지를 보내보세요 ✨</p>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()