"""Galaxy AI Agent Frontend - 에이전트 기반 채팅"""

import streamlit as st
import httpx
import asyncio
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="🌌 Galaxy AI Agent",
    page_icon="🌌",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 백엔드 URL
BACKEND_URL = "http://localhost:8001"

async def call_galaxy_agent(message: str, history: list = None) -> dict:
    """Galaxy AI 에이전트 호출"""
    try:
        if history is None:
            history = []
            
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{BACKEND_URL}/chat",
                json={
                    "message": message,
                    "history": history
                }
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "response": f"😅 Galaxy 연결에 문제가 있어요 (상태코드: {response.status_code})",
                    "tools_used": [],
                    "tokens_used": 0
                }
    except Exception as e:
        return {
            "response": f"🌌 우주의 신호가 약해요... 다시 시도해주세요! 오류: {str(e)}",
            "tools_used": [],
            "tokens_used": 0
        }

def format_chat_history(messages: list) -> list:
    """채팅 히스토리를 API 형식으로 변환"""
    history = []
    for msg in messages:
        if msg["role"] == "user":
            history.append({"role": "user", "content": msg["content"]})
        else:
            history.append({"role": "assistant", "content": msg["content"]})
    return history

# CSS 스타일링
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .main-header {
        text-align: center;
        padding: 1rem;
        margin-bottom: 2rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        backdrop-filter: blur(10px);
    }
    
    .main-header h1 {
        font-size: 3rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    .message {
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 15px;
        backdrop-filter: blur(10px);
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
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    .message-content {
        line-height: 1.5;
    }
    
    .tools-used {
        margin-top: 1rem;
        padding: 0.5rem;
        background: rgba(0,0,0,0.2);
        border-radius: 8px;
        font-size: 0.8rem;
    }
    
    .loading-message {
        text-align: center;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        margin: 1rem 0;
    }
    
    .loading-dots {
        display: inline-block;
        margin-left: 10px;
    }
    
    .loading-dots span {
        display: inline-block;
        width: 6px;
        height: 6px;
        background: white;
        border-radius: 50%;
        margin: 0 2px;
        animation: loading 1.4s infinite ease-in-out;
    }
    
    .loading-dots span:nth-child(1) { animation-delay: 0s; }
    .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
    .loading-dots span:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes loading {
        0%, 40%, 100% { opacity: 0.3; transform: scale(0.8); }
        20% { opacity: 1; transform: scale(1); }
    }
    
    /* Streamlit 기본 요소 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    .stToolbar {display: none;}
    div[data-testid="stDecoration"] {display: none;}
    div[data-testid="stSidebar"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: none !important;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 헤더
    st.markdown('''
    <div class="main-header">
        <h1>🌌 Galaxy</h1>
        <p>vLLM GPT-OSS 기반 AI 에이전트 - 정답을 탐구하는 호기심 많은 우주 친구</p>
    </div>
    ''', unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # 초기 인사말
        st.session_state.messages.append({
            "role": "assistant",
            "content": "안녕하세요! 🌌 저는 vLLM GPT-OSS 모델을 기반으로 한 Galaxy AI 에이전트예요! 정답을 탐구하는 호기심 많은 우주 친구로서 여러분의 질문에 답해드릴 준비가 되어 있어요! ✨\n\n시간 조회, 계산, 파일 작업, 웹 요청 등 16가지 도구를 사용해서 정확한 정보를 제공해드릴게요! 🚀",
            "timestamp": datetime.now()
        })
    
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
            tools_info = ""
            if "tools_used" in message and message["tools_used"]:
                tools_list = ", ".join([tool.get("tool", "알 수 없는 도구") for tool in message["tools_used"]])
                tools_info = f'''
                <div class="tools-used">
                    🛠️ <strong>사용된 도구:</strong> {tools_list}
                </div>
                '''
            
            st.markdown(f'''
            <div class="message galaxy-message">
                <div class="message-author">🌌 <strong>Galaxy AI Agent</strong></div>
                <div class="message-content">{message["content"]}</div>
                {tools_info}
            </div>
            ''', unsafe_allow_html=True)
    
    # 채팅 입력
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "메시지 입력",
                placeholder="Galaxy에게 무엇이든 물어보세요! (예: '지금 몇시야?', '100+200 계산해줘', '시스템 정보 알려줘') 🌟",
                label_visibility="collapsed",
                key="user_input"
            )
        
        with col2:
            send_clicked = st.form_submit_button("🚀 전송", use_container_width=True)
    
    # 메시지 처리
    if send_clicked and user_input.strip():
        # 사용자 메시지 추가
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # 로딩 표시
        loading_placeholder = st.empty()
        loading_placeholder.markdown('''
        <div class="loading-message">
            🌌 <strong>Galaxy AI가 vLLM GPT-OSS 모델과 도구들을 활용해 답변을 준비하고 있어요...</strong>
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 채팅 히스토리 준비
        history = format_chat_history(st.session_state.messages[:-1])  # 마지막 사용자 메시지 제외
        
        # Galaxy AI 에이전트 호출
        agent_response = asyncio.run(call_galaxy_agent(user_input, history))
        
        # 로딩 제거
        loading_placeholder.empty()
        
        # Galaxy 응답 추가
        st.session_state.messages.append({
            "role": "assistant",
            "content": agent_response.get("response", "🌌 우주의 신호가 약해요... 다시 시도해주세요!"),
            "timestamp": datetime.now(),
            "tools_used": agent_response.get("tools_used", []),
            "tokens_used": agent_response.get("tokens_used", 0)
        })
        
        st.rerun()

if __name__ == "__main__":
    main()