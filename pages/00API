import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="Streamlit API 마스터 클래스",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (코드 가독성 향상)
st.markdown("""
<style>
    .stCode { font-family: 'D2Coding', 'Courier New', monospace; }
    .highlight-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# 메인 타이틀 영역
st.title("☁️ Streamlit Cloud & API Master")
st.subheader("배포부터 데이터 분석, AI 활용까지 한 번에 끝내기")
st.markdown("---")

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["🏠 홈", "🔑 1강: API 키 발급", "☁️ 2강: 클라우드 배포", "🚀 3강: 실전 앱 분석"])

# --- 탭 1: 홈 (강의 소개) ---
with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### 🎯 강의 목표")
        st.info("이 웹앱은 **외부 API 연동**부터 **Streamlit Cloud 배포**까지,\n실제 작동하는 AI 서비스를 만드는 과정을 담았습니다.")
        st.markdown("""
        #### 📚 학습 내용
        - **API 개념**: '웨이터' 비유로 쉽게 이해하기
        - **보안**: `secrets.toml`로 API 키 안전하게 관리
        - **데이터**: YouTube 댓글 수집 & 시각화
        - **AI**: GPT-4o 기반 감성 분석 & 영화 추천
        """)
    
    with col2:
        st.markdown("### 🏗️ 아키텍처 미리보기")
        # 간단한 다이어그램 느낌의 텍스트
        st.code("""
[User] 
  ⬇️ (요청)
[Streamlit App] <--> [secrets.toml] (키 관리)
  ⬇️        ⬇️
[YouTube] [OpenAI]
  ⬇️        ⬇️
(댓글)    (분석결과)
  ⬇️        ⬇️
[   Dashboard   ]
        """, language="text")

# --- 탭 2: API 키 발급 ---
with tab2:
    st.header("🔑 API 키 발급 및 개념 정복")
    
    # 개념 설명 카드
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("### 💡 API = 웨이터?")
            st.markdown("""
            손님(**내 앱**)이 주방(**서버**)에 직접 들어갈 수 없죠?  
            대신 **웨이터(API)**에게 주문하면 요리(**데이터**)를 가져다줍니다.  
            이때 웨이터가 확인하는 출입증이 바로 **API 키**입니다.
            """)
        with c2:
            st.warning("⚠️ **주의**: API 키는 집 열쇠와 같습니다. 절대 남에게 보여주거나 GitHub에 올리지 마세요!")

    st.divider()
    st.subheader("🛠️ 서비스별 발급 가이드")
    
    # 3단 컬럼 구성
    cols = st.columns(3)
    
    # YouTube
    with cols[0]:
        with st.container(border=True):
            st.markdown("#### 📺 YouTube API")
            st.caption("댓글 수집, 영상 정보 조회")
            st.markdown("1. [Google Cloud Console](https://console.cloud.google.com/) 접속")
            st.markdown("2. `YouTube Data API v3` 검색")
            st.markdown("3. **사용자 인증 정보** > **API 키** 생성")
            st.code("AIzaSy...", language="text")
    
    # OpenAI
    with cols[1]:
        with st.container(border=True):
            st.markdown("#### 🤖 OpenAI API")
            st.caption("GPT 모델, 텍스트 분석")
            st.markdown("1. [OpenAI Platform](https://platform.openai.com/) 접속")
            st.markdown("2. **Billing** 카드 등록 (필수)")
            st.markdown("3. **API Keys** > **Create new key**")
            st.code("sk-proj...", language="text")
    
    # TMDB
    with cols[2]:
        with st.container(border=True):
            st.markdown("#### 🎬 TMDB API")
            st.caption("영화 포스터, 줄거리 데이터")
            st.markdown("1. [TMDB](https://www.themoviedb.org/) 로그인")
            st.markdown("2. 설정 > **API** 메뉴 이동")
            st.markdown("3. Developer용 키 생성 요청")
            st.code("a1b2c3...", language="text")

# --- 탭 3: 클라우드 배포 ---
with tab3:
    st.header("☁️ Streamlit Cloud 배포 가이드")
    
    col_deploy_1, col_deploy_2 = st.columns([1, 1])
    
    with col_deploy_1:
        st.markdown("### Step 1. GitHub 업로드")
        st.markdown("내 컴퓨터의 코드를 GitHub 저장소에 올립니다.")
        with st.container(border=True):
            st.markdown("**반드시 포함해야 할 파일**")
            st.checkbox("main.py (메인 실행 파일)", value=True, disabled=True)
            st.checkbox("requirements.txt (라이브러리 목록)", value=True, disabled=True)
            st.error("❌ secrets.toml은 절대 올리지 마세요!")
            
    with col_deploy_2:
        st.markdown("### Step 2. Secrets 설정")
        st.markdown("Streamlit Cloud 서버의 '보안 금고'에 키를 저장합니다.")
        with st.container(border=True):
            st.code("""
# Streamlit Cloud > App Settings > Secrets
YOUTUBE_API_KEY = "..."
OPENAI_API_KEY = "..."
TMDB_API_KEY = "..."
            """, language="toml")
            st.caption("이곳에 저장하면 코드에서 `st.secrets`로 불러올 수 있습니다.")

# --- 탭 4: 실전 앱 분석 (임팩트 강화 버전) ---
with tab4:
    st.header("🚀 Code Dive: 핵심 로직 뜯어보기")
    st.markdown("현업 수준의 기능을 구현하는 **결정적 코드 2가지**를 소개합니다.")
    st.divider()

    # 1. YouTube 섹션 (좌우 배치)
    st.subheader("1️⃣ 정규표현식(Regex)으로 영상 ID 추출하기")
    st.markdown("사용자가 어떤 형태의 유튜브 링크를 넣어도 찰떡같이 **ID만 뽑아내는 마법**입니다.")

    col_code1, col_desc1 = st.columns([1.5, 1])
    
    with col_code1:
        st.markdown("**💻 Code**")
        st.code("""
import re

def extract_video_id(url):
    # 정규표현식 패턴 2가지 (일반 링크, 단축 링크)
    patterns = [
        r'v=([a-zA-Z0-9_-]{11})',       # youtube.com/watch?v=...
        r'youtu\.be/([a-zA-Z0-9_-]{11})' # youtu.be/...
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1) # ID 반환
    return None
        """, language="python")
        
    with col_desc1:
        st.markdown("**💡 Logic Check**")
        with st.container(border=True):
            st.markdown("""
            - **`v=...`**: 일반적인 유튜브 주소 패턴을 찾습니다.
            - **`youtu.be/...`**: '공유하기'로 복사한 단축 URL을 찾습니다.
            - **`([a-zA-Z0-9_-]{11})`**: 유튜브 ID는 항상 **11자리**의 문자+숫자 조합입니다.
            """)
        st.success("👉 이 코드를 쓰면 링크 형식을 고민할 필요가 없습니다.")

    st.divider()

    # 2. TMDB 섹션 (Before & After 비교 느낌)
    st.subheader("2️⃣ RAG Lite: '근거 있는' AI 답변 만들기")
    st.markdown("AI가 없는 말을 지어내지 못하도록 **강력한 제약 조건(Prompt)**을 겁니다.")

    col_code2, col_desc2 = st.columns([1.5, 1])
    
    with col_code2:
        st.markdown("**💻 Code (System Prompt)**")
        st.code("""
system_message = \"\"\"
You are a helpful assistant.

[중요 규칙]
1. 답변 본문에서 반드시 [R#] 형태로 근거를 인용하세요.
2. 리뷰 데이터에 없는 내용은 절대 지어내지 마세요.
3. '확인되지 않습니다'라고 솔직하게 말하세요.
\"\"\"

# 실제 리뷰 데이터를 번호와 함께 주입
user_message = f\"\"\"
[리뷰 데이터]
[R1] {review_1}
[R2] {review_2}
...
\"\"\"
        """, language="python")

    with col_desc2:
        st.markdown("**💡 Why this works**")
        with st.container(border=True):
            st.markdown("#### 🚫 할루시네이션(거짓 답변) 방지")
            st.markdown("""
            AI에게 단순히 "리뷰 요약해줘"라고 하면 없는 내용을 지어낼 수 있습니다.
            
            하지만 **"반드시 [R1]처럼 출처를 밝혀"**라고 지시하면, AI는 주어진 데이터 안에서만 답을 찾으려고 노력합니다.
            """)
        st.info("👉 이것이 바로 RAG(검색 증강 생성)의 기초 원리입니다.")

# 사이드바
with st.sidebar:
    st.success("🎉 **강의 예제 앱 실행**")
    st.markdown("왼쪽 메뉴에서 페이지를 선택하세요.")
    st.page_link("pages/00_youtube_api활용.py", label="YouTube 댓글 분석", icon="📺")
    st.page_link("pages/01_openai_api연결.py", label="AI 심층 분석", icon="🤖")
    st.page_link("pages/03_TMDB_AI분석(ChatGPT).py", label="영화 추천 & Q&A", icon="🎬")
