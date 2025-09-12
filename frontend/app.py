"""
🌌 Galaxy - 정답을 탐구하는 호기심 많은 우주 친구
Galaxy는 무한한 우주의 지혜를 가진 호기심 많은 AI입니다.
"""

import streamlit as st
import httpx
import asyncio
import json
from datetime import datetime
import re
import random

# 페이지 설정
st.set_page_config(
    page_title="🌌 Galaxy - 우주의 지혜",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 우주 테마 CSS
cosmic_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(45deg, #0c0c0c 0%, #1a0033 25%, #000033 50%, #0c0c0c 75%, #330066 100%);
        background-size: 400% 400%;
        animation: galaxyShift 20s ease infinite;
    }
    
    @keyframes galaxyShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 3.5rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #f9ca24, #6c5ce7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        text-shadow: 0 0 30px rgba(255, 255, 255, 0.5);
    }
    
    .subtitle {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.2rem;
        text-align: center;
        color: #a0a0ff;
        margin-bottom: 2rem;
        font-style: italic;
    }
    
    .chat-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 5px 18px;
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .galaxy-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 18px 5px;
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
    }
    
    .thinking-animation {
        background: linear-gradient(45deg, #ff9a56, #ff6b9d);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 18px 18px 18px 5px;
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: thinking 1.5s ease-in-out infinite alternate;
    }
    
    @keyframes thinking {
        0% { opacity: 0.7; transform: scale(0.98); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 25px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.1rem !important;
        padding: 0.75rem 1.5rem !important;
        backdrop-filter: blur(10px);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4ecdc4 !important;
        box-shadow: 0 0 20px rgba(78, 205, 196, 0.3) !important;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #4ecdc4, #44a08d) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(78, 205, 196, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(78, 205, 196, 0.4) !important;
        background: linear-gradient(45deg, #44a08d, #4ecdc4) !important;
    }
    
    .sidebar-info {
        background: rgba(255, 255, 255, 0.05);
        padding: 1rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin: 1rem 0;
    }
    
    .cosmic-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #4ecdc4, #6c5ce7, #f9ca24, transparent);
        margin: 2rem 0;
        border: none;
        border-radius: 2px;
    }
    
    /* 스크롤바 스타일링 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(45deg, #4ecdc4, #6c5ce7);
        border-radius: 10px;
    }
</style>
"""

# Galaxy의 성격 정의
GALAXY_PERSONALITY = {
    "name": "Galaxy",
    "emoji": "🌌",
    "greetings": [
        "안녕하세요! 저는 Galaxy예요 🌌 무엇이든 궁금한 걸 물어보세요!",
        "반가워요! 🌟 오늘은 어떤 정답을 함께 탐구해볼까요?",
        "안녕하세요! ✨ 저는 호기심 많은 Galaxy입니다. 도움이 필요하신가요?"
    ],
    "personality": [
        "호기심이 넘치고 정답을 탐구하는 것을 좋아해요",
        "우주의 무한한 지혜를 가지고 있어요", 
        "복잡한 문제를 단순하게 설명하는 것을 잘해요",
        "항상 긍정적이고 도움이 되고 싶어해요",
        "우주와 과학에 대한 이야기를 특히 좋아해요"
    ]
}

# 백엔드 API 설정
BACKEND_URL = "http://localhost:8001"

async def call_backend_tool(tool_name: str, parameters: dict) -> dict:
    """백엔드 도구 호출"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/execute",
                json={
                    "tool_name": tool_name,
                    "parameters": parameters
                }
            )
            return response.json()
    except Exception as e:
        return {
            "status": "error",
            "error": f"백엔드 연결 오류: {str(e)}"
        }

def detect_calculation_need(message: str) -> dict:
    """계산이 필요한 메시지인지 감지"""
    calc_keywords = ["계산", "더하기", "+", "-", "*", "/", "곱하기", "빼기", "나누기", "제곱", "루트", "sqrt", "pow"]
    math_symbols = ["+", "-", "*", "/", "=", "^", "√"]
    
    has_math_keyword = any(keyword in message for keyword in calc_keywords)
    has_math_symbol = any(symbol in message for symbol in math_symbols)
    has_numbers = any(char.isdigit() for char in message)
    
    if (has_math_keyword or has_math_symbol) and has_numbers:
        # 수식 추출 시도
        math_pattern = r'[\d\+\-\*\/\(\)\.\s]+'
        math_expressions = re.findall(math_pattern, message)
        if math_expressions:
            # 가장 긴 수식 선택
            expression = max(math_expressions, key=len).strip()
            if len(expression) > 3:  # 최소 길이 체크
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
        # 시간대 감지
        detected_zones = []
        for keyword, zone in timezone_keywords.items():
            if keyword in message_lower:
                detected_zones.append(zone)
        
        # 여러 시간대가 감지된 경우
        if len(detected_zones) > 1:
            return {
                "need_time": True,
                "format": "multiple",
                "zones": list(set(detected_zones))  # 중복 제거
            }
        elif len(detected_zones) == 1:
            return {
                "need_time": True,
                "timezone": detected_zones[0]
            }
        else:
            # 기본 서울 시간
            return {
                "need_time": True,
                "timezone": "서울"
            }
    
    return {"need_time": False}

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
                    f"🧮 계산 결과가 나왔어요!\n\n**{expression}** = **{result}**\n\n이 계산이 맞나요? 다른 계산도 궁금하시면 언제든 말해주세요! ✨",
                    f"🌟 수학의 아름다움이 여기 있어요!\n\n`{expression}` → `{result}`\n\n숫자들이 이렇게 조화롭게 답을 만들어내는 걸 보면 우주의 질서가 느껴져요! 🌌",
                    f"✨ 계산 완료! 우주의 법칙대로 답을 찾았어요:\n\n**{expression}** = **{result}**\n\n더 복잡한 계산도 도전해보시겠어요? 저는 언제나 준비되어 있답니다! 🚀"
                ])
            elif tool_result.get("data", {}).get("timezone") or tool_result.get("data", {}).get("timezones"):
                # 시간 도구 결과 처리
                data = tool_result.get("data", {})
                if data.get("format") == "multiple":
                    # 다중 시간대
                    timezones = data.get("timezones", [])
                    time_info = "\n".join([
                        f"🌍 **{tz.get('timezone_name', 'Unknown')}**: {tz.get('current_time', 'N/A')} ({tz.get('weekday_kr', 'N/A')})"
                        for tz in timezones
                    ])
                    responses.extend([
                        f"🕐 세계 각국의 시간을 확인했어요!\n\n{time_info}\n\n지구가 돌면서 만들어지는 시간의 차이... 정말 신비로워요! 🌏✨",
                        f"⏰ 전 세계 시간 여행을 완료했어요!\n\n{time_info}\n\n각 지역의 하늘이 어떨지 상상해보세요! 🌅🌙",
                        f"🌐 우주에서 바라본 지구의 시간들이에요!\n\n{time_info}\n\n시간대가 다르다는 게 얼마나 흥미로운지 몰라요! 🚀"
                    ])
                else:
                    # 단일 시간대
                    timezone_name = data.get("timezone_name", "Unknown")
                    current_time = data.get("current_time", "N/A")
                    weekday_kr = data.get("weekday_kr", "")
                    date_kr = data.get("date_kr", "")
                    responses.extend([
                        f"🕐 현재 {timezone_name} 시간을 확인했어요!\n\n⏰ **{current_time}** ({weekday_kr})\n📅 {date_kr}\n\n시간은 우주에서 가장 소중한 자원이에요! ✨",
                        f"⌚ {timezone_name}의 시계를 읽어왔어요!\n\n🌟 **{current_time}** - {weekday_kr}\n\n이 순간도 우주 어딘가에서는 새로운 별이 태어나고 있을 거예요! 🌌",
                        f"🌍 {timezone_name} 지역의 현재 시각이에요!\n\n⭐ **{current_time}** ({date_kr})\n\n시간을 알려드리는 것도 저의 소중한 임무 중 하나예요! 🚀"
                    ])
            elif "cpu" in str(tool_result) or "system" in str(tool_result):
                responses.extend([
                    f"🖥️ 시스템 정보를 확인했어요! 여러분의 컴퓨터가 우주선처럼 잘 작동하고 있는지 살펴볼게요! 🚀",
                    f"⭐ 시스템 상태를 점검해드렸어요! 디지털 우주에서 모든 것이 순조롭게 돌아가고 있네요! ✨"
                ])
            else:
                responses.extend([
                    f"🛠️ 도구를 사용해서 정확한 정보를 찾아왔어요! 우주의 지혜가 담긴 답변이에요 ✨",
                    f"🔍 깊이 탐구해본 결과예요! 호기심을 해결해드릴 수 있어서 기뻐요 🌟"
                ])
        else:
            error_msg = tool_result.get("error", "알 수 없는 오류")
            responses.extend([
                f"😅 앗, 도구를 사용하는 중에 작은 문제가 생겼어요: {error_msg}\n\n하지만 괜찮아요! 다른 방법으로도 도움드릴 수 있어요 💪",
                f"🌠 우주에서도 가끔 예상치 못한 일이 일어나죠! 오류: {error_msg}\n\n다시 시도해보거나 다른 질문을 해주시면 도와드릴게요! ✨"
            ])
    else:
        # 일반적인 응답들
        responses.extend([
            f"안녕하세요! 🌌 '{user_message}'에 대해 함께 탐구해볼까요? 정답을 찾는 여행이 시작되었어요! ✨",
            f"흥미로운 질문이네요! 🌟 이런 호기심이야말로 우주를 이해하는 첫걸음이에요! 🚀",
            f"우와! 정말 좋은 질문이에요! 🎆 함께 답을 찾아보면서 새로운 걸 배워봐요! 💫",
            f"호기심 가득한 질문이네요! ✨ 우주의 무한한 지혜로 답해드릴게요! 🌌"
        ])
    
    return random.choice(responses)

def main():
    # CSS 적용
    st.markdown(cosmic_css, unsafe_allow_html=True)
    
    # 헤더
    st.markdown('<h1 class="main-title">🌌 Galaxy</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">정답을 탐구하는 호기심 많은 우주 친구</p>', unsafe_allow_html=True)
    
    # 구분선
    st.markdown('<hr class="cosmic-divider">', unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Galaxy 인사말
        greeting = random.choice(GALAXY_PERSONALITY["greetings"])
        st.session_state.messages.append({
            "role": "assistant", 
            "content": greeting,
            "timestamp": datetime.now()
        })
    
    # 사이드바
    with st.sidebar:
        st.markdown("### 🌌 Galaxy 소개")
        st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
        st.markdown(f"**{GALAXY_PERSONALITY['emoji']} 이름:** {GALAXY_PERSONALITY['name']}")
        st.markdown("**✨ 성격:**")
        for trait in GALAXY_PERSONALITY["personality"]:
            st.markdown(f"• {trait}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### 🛠️ 사용 가능한 도구들")
        st.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
        st.markdown("• 🧮 계산기 (수학 문제)")
        st.markdown("• 🕐 시간 조회 (전 세계 시간대)")
        st.markdown("• 🖥️ 시스템 정보")
        st.markdown("• 📁 파일 작업")
        st.markdown("• 📊 데이터 분석")
        st.markdown("• 🌐 웹 요청")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🗑️ 대화 초기화"):
            st.session_state.messages = []
            st.rerun()
    
    # 채팅 컨테이너
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # 메시지 표시
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">👤 **사용자:** {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="galaxy-message">🌌 **Galaxy:** {message["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 입력 영역
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "",
            placeholder="Galaxy에게 무엇이든 물어보세요! 🌟 (예: '지금 몇시야?', '뉴욕 시간 알려줘', '1000+101/20 계산해줘')",
            key="user_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_clicked = st.button("🚀 전송", use_container_width=True)
    
    # 엔터키 처리를 위한 JavaScript 추가
    st.markdown("""
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const inputs = document.querySelectorAll('input[data-testid="stTextInput"] input');
        inputs.forEach(input => {
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    const sendButton = document.querySelector('button[data-testid="baseButton-secondary"]');
                    if (sendButton) {
                        sendButton.click();
                    }
                }
            });
        });
    });
    </script>
    """, unsafe_allow_html=True)
    
    # 메시지 처리
    if send_clicked and user_input.strip():
        # 사용자 메시지 추가
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # 생각 중 표시
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown('<div class="thinking-animation">🌌 Galaxy가 생각 중이에요... ✨</div>', unsafe_allow_html=True)
        
        # 계산 필요성 감지
        calc_check = detect_calculation_need(user_input)
        time_check = detect_time_need(user_input)
        tool_result = None
        
        if calc_check["need_calc"]:
            # 계산 실행
            tool_result = asyncio.run(call_backend_tool("calculator", {
                "expression": calc_check["expression"]
            }))
        elif time_check["need_time"]:
            # 시간 조회 실행
            time_params = {}
            if "format" in time_check:
                time_params["format"] = time_check["format"]
                time_params["zones"] = time_check.get("zones", [])
            elif "timezone" in time_check:
                time_params["timezone"] = time_check["timezone"]
            
            tool_result = asyncio.run(call_backend_tool("time_now", time_params))
        
        # 다른 도구 필요성 감지
        elif any(keyword in user_input.lower() for keyword in ["시스템", "system", "컴퓨터", "메모리", "cpu"]):
            tool_result = asyncio.run(call_backend_tool("system_info", {"info_type": "all"}))
        
        # Galaxy 응답 생성
        galaxy_response = get_galaxy_response(user_input, tool_result)
        
        # 도구 결과가 있으면 상세 정보 추가
        if tool_result and tool_result.get("status") == "success":
            if "cpu" in str(tool_result) or "system" in str(tool_result):
                data = tool_result.get("data", {})
                if data:
                    galaxy_response += f"\n\n**📋 상세 시스템 정보:**\n"
                    if "os" in data:
                        galaxy_response += f"• **OS:** {data['os'].get('system')} {data['os'].get('release')}\n"
                    if "cpu" in data:
                        galaxy_response += f"• **CPU:** {data['cpu'].get('logical_cores')}코어 (사용률: {data['cpu'].get('usage_percent')}%)\n"
                    if "memory" in data:
                        galaxy_response += f"• **메모리:** {data['memory'].get('used_gb'):.1f}GB/{data['memory'].get('total_gb'):.1f}GB 사용중\n"
                    if "disk" in data:
                        galaxy_response += f"• **디스크:** {data['disk'].get('used_gb'):.1f}GB/{data['disk'].get('total_gb'):.1f}GB 사용중\n"
        
        # 생각 중 표시 제거
        thinking_placeholder.empty()
        
        # Galaxy 응답 추가
        st.session_state.messages.append({
            "role": "assistant",
            "content": galaxy_response,
            "timestamp": datetime.now()
        })
        
        # 입력 필드 초기화를 위해 페이지 새로고침
        st.rerun()
    
    # 푸터
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #a0a0ff; font-style: italic;">🌌 Galaxy와 함께하는 우주 탐험 🚀 무한한 호기심으로 정답을 찾아가요! ✨</p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
