import os
from datetime import datetime
from urllib.parse import quote
from typing import Tuple

import pandas as pd
import streamlit as st
import requests

import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from geopy.geocoders import Nominatim
from geopy.distance import geodesic

import openai

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    layout="wide",
    page_title="SEOUL TOILET FINDER",
    page_icon="🚻",
)

APP_TITLE_HTML = '<h1 class="big-title">SEOUL<br>TOILET FINDER</h1>'

# -----------------------------
# Secrets (API keys) - 여기서 한 번에 불러와서 관리
# -----------------------------
@st.cache_data(ttl=3600)  # 1시간 캐싱
def get_api_keys() -> Tuple[str, str, str]:
    def get_secret(key: str) -> str:
        try:
            return st.secrets.get(key, "")
        except Exception:
            return ""

    youtube = get_secret("YOUTUBE_API_KEY")
    openai_key = get_secret("OPENAI_API_KEY")
    seoul = get_secret("SEOUL_API_KEY")  # 나중에 서울 Open API 쓸 때 사용

    if not youtube:
        st.sidebar.warning("⚠️ YouTube API Key가 설정되지 않았습니다. Secrets에 추가해주세요.")
    if not openai_key:
        st.sidebar.warning("⚠️ OpenAI API Key가 설정되지 않았습니다. Secrets에 추가해주세요.")
    # 서울 키는 아직 CSV 사용 중이니 경고 생략 (필요 시 추가)

    return youtube, openai_key, seoul

# secrets에서 키 불러오기 (앱 시작 시 한 번만)
YOUTUBE_API_KEY, OPENAI_API_KEY, SEOUL_API_KEY = get_api_keys()

# -----------------------------
# Styles (기존 그대로)
# -----------------------------
def inject_css():
    st.markdown(
        """
        <style>
            @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
            html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
            .stApp { background-color: #FFFFFF; }

            /* Sidebar */
            section[data-testid="stSidebar"] {
                background-color: #F8F9FA;
                border-right: 1px solid #EAEAEA;
            }
            h2, h3, h4 { color: #0039CB; font-weight: 700; letter-spacing: -0.5px; }

            /* Big Title */
            .big-title {
                color: #2962FF;
                font-size: 4.5rem !important;
                font-weight: 900;
                letter-spacing: -2px;
                line-height: 1.0;
                margin-bottom: 22px;
                text-shadow: 2px 2px 0px #E3F2FD;
            }

            /* ... (나머지 CSS 그대로 유지 - 길어서 생략했지만 원본 그대로 복사하세요) */
        </style>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# i18n (기존 그대로)
# -----------------------------
# LANG 딕셔너리, init_lang(), toggle_language()는 당신 원본 그대로 사용
# ... (생략 - 그대로 복사)

# -----------------------------
# Data Loading
# -----------------------------
@st.cache_data(show_spinner=False)
def load_toilet_data(file_path: str = "seoul_toilet.csv") -> pd.DataFrame:
    # 현재는 CSV 로드 (기존 방식 유지)
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except Exception:
            df = None
    if df is None:
        st.error(f"데이터 파일을 찾을 수 없습니다: {file_path}")
        st.stop()

    target_cols = {
        "건물명": "name",
        "도로명주소": "addr",
        "개방시간": "hours",
        "x 좌표": "lon",
        "y 좌표": "lat",
        "남녀공용화장실여부": "unisex",
        "기저귀교환대장소": "diaper",
        "비상벨설치여부": "bell",
        "CCTV설치여부": "cctv",
    }
    existing_cols = [c for c in target_cols if c in df.columns]
    df = df[existing_cols].rename(columns=target_cols)

    for col in ["unisex", "diaper", "bell", "cctv", "addr", "hours"]:
        if col not in df.columns:
            df[col] = "-"
        else:
            df[col] = df[col].fillna("정보없음")

    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.replace("|", "", regex=False)

    # 서울 범위 필터
    df = df[
        (df["lat"] > 37.4) & (df["lat"] < 37.8) &
        (df["lon"] > 126.7) & (df["lon"] < 127.3)
    ]

    return df

# (load_sample_extra_data, geocode_address, add_distance 등은 기존 그대로)

# -----------------------------
# 나머지 함수들 (naver_route_link, search_youtube_videos, save_feedback, ask_ai_recommendation, facility_icons, build_map 등)
# 모두 당신 원본 그대로 복사해서 사용하세요!
# ... (생략 - 변경 없음)

# -----------------------------
# Main (기존 그대로, 키 변수만 업데이트)
# -----------------------------
def main():
    inject_css()
    init_lang()
    txt = LANG[st.session_state.lang]

    # 키는 이미 전역으로 불러옴 → 여기서 다시 안 불러도 됨

    user_address, search_radius, show_toilet, show_subway, show_store = sidebar_ui(txt)
    top_header(txt)

    try:
        df_toilet = load_toilet_data()
    except Exception:
        st.warning(txt["error_file"])
        st.stop()

    df_subway, df_store = load_sample_extra_data()

    # (나머지 main() 로직은 당신 원본 그대로 - geocoding, distance, tabs 등)
    # ... (생략)

if __name__ == "__main__":
    main()
