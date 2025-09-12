"""
Galaxy Frontend - Integrated with Tool Calling Proxy
Modern chat interface connected to OpenAI-compatible proxy
"""

import streamlit as st
import httpx
import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any

# 페이지 설정
st.set_page_config(
    page_title="🌌 Galaxy Chat with Tools",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
PROXY_URL = os.getenv("PROXY_URL", "http://localhost:8001/v1/chat/completions")
PROXY_BASE = os.getenv("PROXY_BASE", "http://localhost:8001")

# 모던 CSS 스타일링
modern_css = """
<style>
/* 전체 앱 스타일 */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

/* 사이드바 스타일 */
.css-1d391kg {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255, 255, 255, 0.2);
}

/* 메인 컨테이너 */
.main .block-container {
    padding-top: 2rem;
    max-width: 1000px;
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

/* 채팅 메시지 */
.chat-message {
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 15px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.user-message {
    background: rgba(76, 175, 80, 0.3);
    margin-left: 20%;
}

.assistant-message {
    background: rgba(33, 150, 243, 0.3);
    margin-right: 20%;
}

.tool-call {
    background: rgba(255, 193, 7, 0.3);
    border-left: 4px solid #ffc107;
}

/* 입력 폼 스타일 */
.stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 25px;
    color: white;
    padding: 15px 20px;
}

.stTextInput > div > div > input:focus {
    border-color: #4ecdc4;
    box-shadow: 0 0 20px rgba(78, 205, 196, 0.3);
}

/* 버튼 스타일 */
.stButton > button {
    background: linear-gradient(45deg, #4ecdc4, #44a08d);
    border: none;
    border-radius: 25px;
    color: white;
    font-weight: bold;
    padding: 12px 30px;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(78, 205, 196, 0.3);
}

/* 성공/에러 메시지 */
.success {
    background: rgba(76, 175, 80, 0.2);
    border-left: 4px solid #4caf50;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}

.error {
    background: rgba(244, 67, 54, 0.2);
    border-left: 4px solid #f44336;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
</style>
"""

st.markdown(modern_css, unsafe_allow_html=True)

# 헤더
st.markdown("""
<div class="header">
    <h1>🌌 Galaxy Chat with Tools</h1>
    <p>OpenAI-compatible Tool Calling Interface</p>
</div>
""", unsafe_allow_html=True)

# 사이드바 - 도구 정보
st.sidebar.title("🛠️ Available Tools")

@st.cache_data
def get_available_tools():
    """도구 목록을 가져와서 캐시"""
    try:
        response = httpx.get(f"{PROXY_BASE}/tools", timeout=10.0)
        if response.status_code == 200:
            return response.json()
        else:
            return {"tools": [], "total_tools": 0, "categories": []}
    except Exception as e:
        st.sidebar.error(f"Failed to load tools: {e}")
        return {"tools": [], "total_tools": 0, "categories": []}

tools_info = get_available_tools()

if tools_info["total_tools"] > 0:
    st.sidebar.success(f"✅ {tools_info['total_tools']} tools available")
    
    # 카테고리별로 도구 표시
    for category in tools_info["categories"]:
        category_tools = [t for t in tools_info["tools"] if t["category"] == category]
        if category_tools:
            st.sidebar.subheader(f"📁 {category.title()}")
            for tool in category_tools:
                with st.sidebar.expander(f"🔧 {tool['name']}"):
                    st.write(tool['description'])
                    if tool.get('parameters', {}).get('properties'):
                        st.write("**Parameters:**")
                        for param, details in tool['parameters']['properties'].items():
                            required = "✅" if param in tool['parameters'].get('required', []) else "⭕"
                            st.write(f"• {param} {required}: {details.get('description', '')}")
else:
    st.sidebar.warning("⚠️ No tools available")

# 프록시 상태 확인
st.sidebar.subheader("📊 Proxy Status")

@st.cache_data(ttl=10)  # 10초마다 새로고침
def get_proxy_health():
    """프록시 상태 확인"""
    try:
        response = httpx.get(f"{PROXY_BASE}/health", timeout=5.0)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

health = get_proxy_health()

if health.get("status") == "healthy":
    st.sidebar.success("🟢 Proxy Online")
    if "stats" in health:
        stats = health["stats"]
        st.sidebar.metric("Total Requests", stats.get("total_requests", 0))
        st.sidebar.metric("Tool Calls", stats.get("tool_calls_success", 0))
        st.sidebar.metric("Tools Available", health.get("tools_available", 0))
else:
    st.sidebar.error("🔴 Proxy Offline")
    st.sidebar.write(f"Error: {health.get('error', 'Unknown error')}")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = 0

# 채팅 기록 표시
def display_message(message: Dict[str, Any]):
    """메시지 표시"""
    
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 You:</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    
    elif message["role"] == "assistant":
        if message.get("tool_calls"):
            # Tool calls 표시
            st.markdown(f"""
            <div class="chat-message tool-call">
                <strong>🔧 Tool Calls:</strong>
            </div>
            """, unsafe_allow_html=True)
            
            for tool_call in message["tool_calls"]:
                function = tool_call["function"]
                args = json.loads(function["arguments"]) if function["arguments"] else {}
                
                st.markdown(f"""
                <div class="chat-message tool-call">
                    <strong>🛠️ {function["name"]}:</strong><br>
                    <code>{json.dumps(args, ensure_ascii=False, indent=2)}</code>
                </div>
                """, unsafe_allow_html=True)
        
        elif message.get("content"):
            # 일반 응답 표시
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong>🤖 Galaxy:</strong><br>
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)

# 기존 메시지들 표시
for message in st.session_state.messages:
    display_message(message)

# 채팅 입력
def send_message():
    """메시지 전송 및 처리"""
    
    user_input = st.session_state.get("user_input", "").strip()
    if not user_input:
        return
    
    # 사용자 메시지 추가
    user_message = {"role": "user", "content": user_input}
    st.session_state.messages.append(user_message)
    
    # 프록시에 요청 보내기
    with st.spinner("Galaxy is thinking... 🌌"):
        try:
            # OpenAI 호환 요청 생성
            request_data = {
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {"role": "system", "content": "You are Galaxy, a helpful AI assistant with access to various tools. Use tools when they can help provide accurate information."},
                    user_message
                ],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "time_now",
                            "description": "Get current time in specified timezone",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "timezone": {"type": "string", "description": "Timezone like Asia/Seoul, UTC, etc."}
                                },
                                "required": []
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "calculator",
                            "description": "Perform mathematical calculations",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "expression": {"type": "string", "description": "Mathematical expression"}
                                },
                                "required": ["expression"]
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "system_info",
                            "description": "Get system information",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "info_type": {"type": "string", "enum": ["all", "cpu", "memory", "disk"]}
                                },
                                "required": []
                            }
                        }
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "file_list",
                            "description": "List files in a directory",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "directory": {"type": "string", "description": "Directory path"},
                                    "pattern": {"type": "string", "description": "File pattern"},
                                    "recursive": {"type": "boolean", "description": "Search recursively"}
                                },
                                "required": ["directory"]
                            }
                        }
                    }
                ],
                "tool_choice": "auto",
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            # 프록시로 요청
            response = httpx.post(
                PROXY_URL,
                json=request_data,
                timeout=30.0,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    assistant_message = result["choices"][0]["message"]
                    st.session_state.messages.append(assistant_message)
                    
                    # 성공 메시지
                    st.markdown("""
                    <div class="success">
                        ✅ Response received successfully!
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    st.markdown("""
                    <div class="error">
                        ❌ Invalid response format
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="error">
                    ❌ HTTP Error {response.status_code}: {response.text}
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown(f"""
            <div class="error">
                ❌ Error: {str(e)}
            </div>
            """, unsafe_allow_html=True)
    
    # 입력 필드 초기화 (안전한 방식으로)
    try:
        if "user_input" in st.session_state:
            del st.session_state["user_input"]
    except:
        pass
    st.rerun()

# 입력 폼
col1, col2 = st.columns([4, 1])

with col1:
    st.text_input(
        "Message Galaxy...",
        key="user_input",
        placeholder="Try: 'Calculate 25 × 8' or 'Check system memory'",
        on_change=send_message,
        label_visibility="collapsed"
    )

with col2:
    if st.button("Send 🚀", use_container_width=True):
        send_message()

# 하단 정보
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("💬 Messages", len(st.session_state.messages))

with col2:
    st.metric("🔧 Tools", tools_info["total_tools"])

with col3:
    if st.button("🔄 Clear Chat"):
        st.session_state.messages = []
        st.session_state.conversation_id += 1
        st.rerun()

# 사용 예시
with st.expander("💡 Usage Examples"):
    st.markdown("""
    **Calculator Tools:**
    - "Calculate 144 ÷ 12"
    - "What's 25 × 8 + 50?"
    
    **System Information:**
    - "Check CPU usage"
    - "Show memory status"
    - "System information"
    
    **File Operations:**
    - "List files in /tmp"
    - "Show contents of current directory"
    
    **General Chat:**
    - "Hello Galaxy!"
    - "Tell me about yourself"
    """)

# 디버그 정보 (개발용)
if st.checkbox("🔍 Debug Info", value=False):
    st.subheader("Debug Information")
    st.write("**Proxy URL:**", PROXY_URL)
    st.write("**Proxy Base:**", PROXY_BASE)
    st.write("**Session Messages:**", len(st.session_state.messages))
    st.write("**Tools Info:**", tools_info)
    
    if st.session_state.messages:
        st.json(st.session_state.messages[-1] if st.session_state.messages else {})