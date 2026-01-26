import os
import time
import html
from datetime import datetime
from urllib.parse import quote

import numpy as np
import pandas as pd
import streamlit as st
import requests

import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

from geopy.geocoders import Nominatim
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
# Secrets (API keys)
# -----------------------------
def get_secret(key: str) -> str:
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""


@st.cache_data(ttl=3600, show_spinner=False)
def get_api_keys():
    youtube = get_secret("YOUTUBE_API_KEY")
    openai_key = get_secret("OPENAI_API_KEY")
    seoul = get_secret("SEOUL_API_KEY")  # optional future
    return youtube, openai_key, seoul


YOUTUBE_API_KEY, OPENAI_API_KEY, SEOUL_API_KEY = get_api_keys()


# -----------------------------
# Styles
# -----------------------------
def inject_css():
    st.markdown(
        """
        <style>
            @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
            html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
            .stApp { background-color: #FFFFFF; }

            section[data-testid="stSidebar"] {
                background-color: #F8F9FA;
                border-right: 1px solid #EAEAEA;
            }
            h2, h3, h4 { color: #0039CB; font-weight: 700; letter-spacing: -0.5px; }

            .big-title {
                color: #2962FF;
                font-size: 4.5rem !important;
                font-weight: 900;
                letter-spacing: -2px;
                line-height: 1.0;
                margin-bottom: 22px;
                text-shadow: 2px 2px 0px #E3F2FD;
            }

            div[data-baseweb="checkbox"] div[aria-checked="true"] {
                background-color: #2962FF !important;
                border-color: #2962FF !important;
            }

            div[data-testid="stMetricValue"] {
                color: #2962FF !important;
                font-weight: 800;
                font-size: 42px !important;
            }
            div[data-testid="stMetricLabel"] { color: #666666; font-size: 14px; }

            div.stButton > button {
                background-color: #2962FF;
                color: white;
                border-radius: 10px;
                border: none;
                padding: 0.5rem 1.2rem;
                font-weight: 700;
                transition: all 0.2s ease;
            }
            div.stButton > button:hover {
                background-color: #002ba1;
                transform: translateY(-2px);
            }

            .stTextInput > div > div > input:focus {
                border-color: #2962FF !important;
                box-shadow: 0 0 0 1px #2962FF !important;
            }

            .info-box {
                background-color: #E3F2FD;
                padding: 18px;
                border-radius: 12px;
                border: 1px solid #90CAF9;
                margin-bottom: 16px;
                color: #0D47A1;
            }
            .location-box {
                background-color: #E8F0FE;
                padding: 14px 16px;
                border-radius: 10px;
                border-left: 5px solid #2962FF;
                color: #1565C0;
                font-weight: 600;
                margin-bottom: 16px;
            }
            .card {
                background-color:#F8F9FA;
                padding:18px;
                border-radius:12px;
                border:1px solid #E0E0E0;
            }

            /* Tabs styling (bigger + blue + 강조) */
            div[data-testid="stTabs"] {
                margin-top: 8px;
            }
            div[data-testid="stTabs"] button {
                font-size: 20px !important;
                font-weight: 900 !important;
                color: #2962FF !important;
                padding: 10px 16px !important;
            }
            div[data-testid="stTabs"] button[aria-selected="true"] {
                color: #002ba1 !important;
                border-bottom: 4px solid #2962FF !important;
            }
            div[data-testid="stTabs"] [data-baseweb="tab-list"] {
                border-bottom: 1px solid #E3F2FD !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------
# i18n
# -----------------------------
LANG = {
    "ko": {
        "desc": "서울시 공중화장실, 지하철, 편의점 위치 안내 서비스",
        "sidebar_header": "SEARCH OPTION",
        "input_label": "현재 위치 (예: 강남역, 시청)",
        "radius_label": "검색 반경 (km)",
        "show_toilet": "공중화장실 (Toilet)",
        "show_subway": "지하철역 (Subway)",
        "show_store": "안심 편의점 (Store)",
        "error_file": "⚠️ 데이터 파일을 찾을 수 없습니다. (seoul_toilet.csv)",
        "success_loc": "📍 위치 확인됨: {}",
        "warn_no_result": "검색 결과가 없습니다.",
        "popup_current": "현 위치",
        "error_no_loc": "위치를 찾을 수 없습니다.",
        "btn_label": "Switch to English",
        "detail_title": "DETAILS",
        "col_addr": "주소",
        "col_time": "운영시간",
        "fb_title": "FEEDBACK",
        "fb_type": "유형 선택",
        "fb_types": ["정보 수정", "오류 신고", "기타 의견"],
        "fb_msg": "내용을 입력해주세요",
        "fb_btn": "의견 보내기",
        "fb_success": "소중한 의견이 전달되었습니다. 감사합니다! 💙",
        "youtube_title": "📺 Nearby Vibe (Vlog)",
        "youtube_need_key": "⚠️ 설정(Secrets)에 YouTube API Key를 등록해주세요.",
        "ai_title": "🤖 AI 화장실 소믈리에 (Beta)",
        "ai_desc": "원하는 조건을 말하면 AI가 최고의 화장실을 추천해줍니다.",
        "ai_placeholder": "예: 아이랑 갈 수 있는 깨끗하고 안전한 화장실 추천해줘",
        "ai_btn": "AI에게 추천받기 ✨",
        "ai_thinking": "AI가 데이터를 분석 중입니다...",
        "ai_need_key": "⚠️ 설정(Secrets)에 OpenAI API Key가 필요합니다.",
        "search_placeholder": "시설 이름으로 검색...",
        "select_label": "시설 선택 (상세보기)",
        "admin_mode": "Admin Mode",
        "feedback_list": "📥 Feedback List",
        "no_feedback": "No feedback yet.",
        "tab_map": "지도",
        "tab_list": "리스트",
        "tab_ai": "AI 추천",
        "tab_vlog": "브이로그",
        "tab_feedback": "피드백",
        "metric_toilet": "TOILET",
        "metric_subway": "SUBWAY",
        "metric_nearest": "NEAREST",
        "finding_vlogs": "Finding Vlogs...",
        "facility": "시설",
        "question_label": "💬 질문",
        "search_web": "웹에서 보기",
        "route_try": "앱으로 길찾기",
        "route_note": "* PC에서는 앱 링크가 제한될 수 있어요. (웹으로 자동 이동)",
        "enter_location_hint": "사이드바에서 위치를 입력해 주세요.",
        "vlog_empty": "관련 영상을 찾을 수 없습니다.",
        "admin_feedback_missing": "아직 피드백이 없습니다.",
    },
    "en": {
        "desc": "Find nearby public toilets, subway stations, and safe stores.",
        "sidebar_header": "SEARCH OPTION",
        "input_label": "Enter Location (e.g., Gangnam Station)",
        "radius_label": "Search Radius (km)",
        "show_toilet": "Public Toilet",
        "show_subway": "Subway Station",
        "show_store": "Convenience Store",
        "error_file": "⚠️ Data file missing. (seoul_toilet.csv)",
        "success_loc": "📍 Location: {}",
        "warn_no_result": "No results found.",
        "popup_current": "Current Location",
        "error_no_loc": "Location not found.",
        "btn_label": "한국어로 변경",
        "detail_title": "DETAILS",
        "col_addr": "Address",
        "col_time": "Hours",
        "fb_title": "FEEDBACK",
        "fb_type": "Type",
        "fb_types": ["Correction", "Bug Report", "Other"],
        "fb_msg": "Message",
        "fb_btn": "Submit",
        "fb_success": "Thank you! Feedback sent. 💙",
        "youtube_title": "📺 Nearby Vibe (Vlog)",
        "youtube_need_key": "⚠️ Please set YouTube API Key in Secrets.",
        "ai_title": "🤖 AI Toilet Sommelier (Beta)",
        "ai_desc": "Ask AI for the best restroom recommendation.",
        "ai_placeholder": "e.g., Where is the cleanest toilet with a diaper station?",
        "ai_btn": "Ask AI ✨",
        "ai_thinking": "AI is analyzing data...",
        "ai_need_key": "⚠️ OpenAI API Key is missing in Secrets.",
        "search_placeholder": "Search by name...",
        "select_label": "Select Place",
        "admin_mode": "Admin Mode",
        "feedback_list": "📥 Feedback List",
        "no_feedback": "No feedback yet.",
        "tab_map": "Map",
        "tab_list": "List",
        "tab_ai": "AI",
        "tab_vlog": "Vlog",
        "tab_feedback": "Feedback",
        "metric_toilet": "TOILET",
        "metric_subway": "SUBWAY",
        "metric_nearest": "NEAREST",
        "finding_vlogs": "Finding Vlogs...",
        "facility": "Facility",
        "question_label": "💬 Question",
        "search_web": "Open on web",
        "route_try": "Route in app",
        "route_note": "* Desktop may block app links. (Auto fallback to web)",
        "enter_location_hint": "Enter a location in the sidebar.",
        "vlog_empty": "No related videos found.",
        "admin_feedback_missing": "No feedback yet.",
    },
}


def init_session_state():
    if "lang" not in st.session_state:
        st.session_state.lang = "ko"


def toggle_language():
    st.session_state.lang = "en" if st.session_state.lang == "ko" else "ko"


# -----------------------------
# Data Loading
# -----------------------------
@st.cache_data(show_spinner=False)
def load_toilet_data(file_path: str = "seoul_toilet.csv") -> pd.DataFrame:
    df = None
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except Exception:
            df = None
    if df is None:
        raise FileNotFoundError(file_path)

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

    # Clean pipes (|)
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.replace("|", "", regex=False)

    # Basic bounds for Seoul-ish
    if "lat" in df.columns and "lon" in df.columns:
        df = df[(df["lat"] > 37.4) & (df["lat"] < 37.8) & (df["lon"] > 126.7) & (df["lon"] < 127.3)]

    # Ensure numeric
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])

    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_sample_extra_data():
    subway_data = [
        {"name": "시청역 1호선", "lat": 37.5635, "lon": 126.9754},
        {"name": "시청역 2호선", "lat": 37.5620, "lon": 126.9750},
        {"name": "을지로입구역", "lat": 37.5660, "lon": 126.9826},
        {"name": "광화문역", "lat": 37.5716, "lon": 126.9768},
        {"name": "종각역", "lat": 37.5702, "lon": 126.9831},
        {"name": "명동역", "lat": 37.5609, "lon": 126.9863},
        {"name": "강남역", "lat": 37.4979, "lon": 127.0276},
        {"name": "홍대입구역", "lat": 37.5575, "lon": 126.9245},
    ]
    store_data = [
        {"name": "CU 시청광장점", "lat": 37.5640, "lon": 126.9770},
        {"name": "GS25 을지로점", "lat": 37.5655, "lon": 126.9810},
        {"name": "세븐일레븐 무교점", "lat": 37.5675, "lon": 126.9790},
        {"name": "CU 강남대로점", "lat": 37.4985, "lon": 127.0280},
        {"name": "GS25 홍대파크", "lat": 37.5580, "lon": 126.9250},
    ]
    return pd.DataFrame(subway_data), pd.DataFrame(store_data)


# -----------------------------
# Geo (Geocoding + Distance)
# -----------------------------
@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)  # 24h cache
def geocode_address(raw_address: str):
    """
    Nominatim can be flaky; we retry with backoff to reduce failure rate.
    """
    geolocator = Nominatim(user_agent="seoul_toilet_finder_v6", timeout=10)
    search_query = f"Seoul {raw_address}" if "Seoul" not in raw_address and "서울" not in raw_address else raw_address

    for attempt in range(3):
        try:
            loc = geolocator.geocode(search_query)
            if loc:
                return float(loc.latitude), float(loc.longitude), loc.address
        except Exception:
            pass
        time.sleep(0.6 * (attempt + 1))  # backoff

    return None


def _haversine_km(lat1, lon1, lat2_arr, lon2_arr) -> np.ndarray:
    """
    Vectorized Haversine distance (km)
    """
    R = 6371.0088
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2_arr)
    lon2 = np.radians(lon2_arr)

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * (np.sin(dlon / 2.0) ** 2)
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def _bounding_box(user_lat: float, user_lon: float, radius_km: float):
    """
    Rough bounding box (degrees) for prefiltering.
    """
    lat_delta = radius_km / 111.32
    lon_delta = radius_km / (111.32 * max(np.cos(np.radians(user_lat)), 1e-6))
    return (
        user_lat - lat_delta,
        user_lat + lat_delta,
        user_lon - lon_delta,
        user_lon + lon_delta,
    )


def add_distance_fast(df: pd.DataFrame, user_lat: float, user_lon: float) -> pd.DataFrame:
    """
    Adds 'dist' column with vectorized Haversine distance.
    """
    out = df.copy()
    out["dist"] = _haversine_km(user_lat, user_lon, out["lat"].to_numpy(), out["lon"].to_numpy())
    return out


# -----------------------------
# Naver Map Route Link
# -----------------------------
def naver_route_link(user_lat, user_lon, dest_lat, dest_lon, dest_name, mode="walk"):
    sname = quote("현재 위치")
    dname = quote(str(dest_name))
    appname = quote("https://seoul-toilet-finder.streamlit.app")
    return (
        f"nmap://route/{mode}"
        f"?slat={user_lat}&slng={user_lon}&sname={sname}"
        f"&dlat={dest_lat}&dlng={dest_lon}&dname={dname}"
        f"&appname={appname}"
    )


# -----------------------------
# YouTube
# -----------------------------
@st.cache_data(show_spinner=False, ttl=60 * 20)
def search_youtube_videos(query: str, api_key: str, max_results: int = 3):
    if not api_key:
        return []
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{query} 맛집 핫플 브이로그",
        "key": api_key,
        "maxResults": max_results,
        "type": "video",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("items", [])
        return [f"https://www.youtube.com/watch?v={it['id']['videoId']}" for it in items]
    except Exception:
        return []


# -----------------------------
# Feedback
# -----------------------------
def save_feedback(fb_type: str, message: str, file_name: str = "user_feedback.csv"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_data = pd.DataFrame([[timestamp, fb_type, message]], columns=["Time", "Type", "Message"])
    if not os.path.exists(file_name):
        new_data.to_csv(file_name, index=False, encoding="utf-8-sig")
    else:
        new_data.to_csv(file_name, mode="a", header=False, index=False, encoding="utf-8-sig")


# -----------------------------
# AI
# -----------------------------
def ask_ai_recommendation(df_nearby: pd.DataFrame, user_query: str, api_key: str) -> str:
    if not api_key:
        return "⚠️ API Key가 설정되지 않았습니다. (Secrets를 확인해주세요)"
    if df_nearby is None or df_nearby.empty:
        return "주변에 검색된 화장실 데이터가 없어 추천할 수 없어요."

    cols = ["name", "dist", "unisex", "diaper", "bell", "cctv"]
    df_slim = df_nearby[cols].head(15).copy()
    df_slim["dist"] = df_slim["dist"].round(2)
    data_context = df_slim.to_csv(index=False)

    system = (
        "당신은 '화장실 소믈리에'입니다. "
        "주어진 데이터만 근거로 추천하세요. 없는 정보는 지어내지 말고 '정보 없음'이라고 말하세요."
    )
    user = f"""
[주변 화장실 데이터 CSV]
{data_context}

[사용자 질문]
{user_query}

요구조건(거리/안전/기저귀교환대 등)에 가장 잘 맞는 화장실 1~2곳을 추천하고,
각 추천에 대해 (1) 추천 이유 (2) 거리(km) (3) 주의사항/정보없음 항목을 간단히 정리해주세요.
"""

    try:
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"AI 연결 오류: {e}"


# -----------------------------
# Map helpers
# -----------------------------
def facility_icons(row: pd.Series) -> str:
    icons = ""
    if str(row.get("diaper", "-")) not in ("-", "정보없음", "nan"):
        icons += "👶 "
    bell = str(row.get("bell", ""))
    cctv = str(row.get("cctv", ""))
    unisex = str(row.get("unisex", ""))

    if bell == "Y" or "설치" in bell:
        icons += "🚨 "
    if cctv == "Y" or "설치" in cctv:
        icons += "📷 "
    if unisex == "Y":
        icons += "👫"
    return icons.strip()


def build_map(
    user_lat: float,
    user_lon: float,
    txt: dict,
    nearby_toilet: pd.DataFrame,
    nearby_subway: pd.DataFrame,
    nearby_store: pd.DataFrame,
    show_toilet: bool,
    show_subway: bool,
    show_store: bool,
    selected_name: str | None,
):
    m = folium.Map(location=[user_lat, user_lon], zoom_start=15, tiles="CartoDB positron")

    folium.Marker(
        [user_lat, user_lon],
        popup=txt["popup_current"],
        icon=folium.Icon(color="red", icon="user"),
    ).add_to(m)

    marker_cluster = MarkerCluster().add_to(m)

    if show_toilet and nearby_toilet is not None and not nearby_toilet.empty:
        for _, r in nearby_toilet.iterrows():
            is_selected = (selected_name is not None and r["name"] == selected_name)

            route_url = naver_route_link(
                user_lat=user_lat,
                user_lon=user_lon,
                dest_lat=r["lat"],
                dest_lon=r["lon"],
                dest_name=r["name"],
                mode="walk",
            )

            # Web fallback always works (PC/Mobile)
            web_url = f"https://map.naver.com/v5/search/{quote(str(r['name']))}"

            # Safe text for HTML
            safe_name = html.escape(str(r["name"]))
            safe_dist = f"{float(r['dist']):.2f}"

            # ✅ 핵심 UX 개선:
            # - 클릭 시 default 이동을 막고
            # - nmap:// 먼저 시도 (iframe)
            # - 0.9초 후 웹으로 fallback 이동 (PC에서도 '먹통' 없음)
            popup_html = f"""
            <div style="font-family:Pretendard, sans-serif; font-size:14px;">
              <div style="font-weight:900; margin-bottom:6px;">🚻 {safe_name}</div>
              <div style="color:#666; margin-bottom:10px;">약 {safe_dist} km</div>

              <div style="display:flex; gap:8px; flex-wrap:wrap;">
                <a href="#" onclick="
                    try {{
                      event.preventDefault();
                      var ifr = document.createElement('iframe');
                      ifr.style.display = 'none';
                      ifr.src = '{route_url}';
                      document.body.appendChild(ifr);
                      setTimeout(function(){{ window.location.href = '{web_url}'; }}, 900);
                      return false;
                    }} catch(e) {{
                      window.location.href = '{web_url}';
                      return false;
                    }}
                  " style="text-decoration:none;">
                  <span style="background:#2962FF; color:white; padding:6px 10px; border-radius:8px; font-weight:800;">
                    {txt['route_try']}
                  </span>
                </a>

                <a href="{web_url}" target="_blank" style="text-decoration:none;">
                  <span style="background:#E3F2FD; color:#0D47A1; padding:6px 10px; border-radius:8px; font-weight:800; border:1px solid #90CAF9;">
                    {txt['search_web']}
                  </span>
                </a>
              </div>

              <div style="margin-top:8px; font-size:12px; color:#7a7a7a;">
                {txt['route_note']}
              </div>
            </div>
            """

            popup = folium.Popup(folium.IFrame(html=popup_html, width=320, height=175), max_width=360)

            if is_selected:
                folium.Marker(
                    [r["lat"], r["lon"]],
                    tooltip=str(r["name"]),
                    popup=popup,
                    icon=folium.Icon(color="green", icon="star"),
                ).add_to(m)
            else:
                folium.Marker(
                    [r["lat"], r["lon"]],
                    tooltip=str(r["name"]),
                    popup=popup,
                    icon=folium.Icon(color="green", icon="info-sign"),
                ).add_to(marker_cluster)

    if show_subway and nearby_subway is not None and not nearby_subway.empty:
        for _, r in nearby_subway.iterrows():
            folium.Marker(
                [r["lat"], r["lon"]],
                popup=f"<b>🚇 {html.escape(str(r['name']))}</b>",
                tooltip=str(r["name"]),
                icon=folium.Icon(color="orange", icon="arrow-down", prefix="fa"),
            ).add_to(m)

    if show_store and nearby_store is not None and not nearby_store.empty:
        for _, r in nearby_store.iterrows():
            folium.Marker(
                [r["lat"], r["lon"]],
                popup=f"<b>🏪 {html.escape(str(r['name']))}</b>",
                tooltip=str(r["name"]),
                icon=folium.Icon(color="purple", icon="shopping-cart", prefix="fa"),
            ).add_to(m)

    return m


# -----------------------------
# UI
# -----------------------------
def sidebar_ui(txt: dict):
    with st.sidebar:
        st.button(txt["btn_label"], on_click=toggle_language)
        st.divider()
        st.subheader(txt["sidebar_header"])

        show_toilet = st.checkbox(txt["show_toilet"], value=True)
        show_subway = st.checkbox(txt["show_subway"], value=True)
        show_store = st.checkbox(txt["show_store"], value=False)

        st.divider()
        default_val = "서울시청" if st.session_state.lang == "ko" else "Seoul City Hall"
        user_address = st.text_input(txt["input_label"], default_val)
        search_radius = st.slider(txt["radius_label"], 0.5, 5.0, 1.0)

        st.divider()
        if st.checkbox(txt["admin_mode"]):
            if os.path.exists("user_feedback.csv"):
                st.write(txt["feedback_list"] + ":")
                st.dataframe(pd.read_csv("user_feedback.csv"))
            else:
                st.caption(txt.get("admin_feedback_missing", txt["no_feedback"]))

    return user_address, search_radius, show_toilet, show_subway, show_store


def top_header(txt: dict):
    st.markdown(APP_TITLE_HTML, unsafe_allow_html=True)
    st.caption(txt["desc"])


# -----------------------------
# Main
# -----------------------------
def main():
    init_session_state()
    inject_css()
    txt = LANG[st.session_state.lang]

    user_address, search_radius, show_toilet, show_subway, show_store = sidebar_ui(txt)
    top_header(txt)

    try:
        df_toilet = load_toilet_data()
    except Exception:
        st.warning(txt["error_file"])
        st.stop()

    df_subway, df_store = load_sample_extra_data()

    if not user_address:
        st.info(txt["enter_location_hint"])
        st.stop()

    loc = geocode_address(user_address)
    if not loc:
        st.error(txt["error_no_loc"])
        st.stop()

    user_lat, user_lon, full_addr = loc
    st.markdown(
        f'<div class="location-box">{txt["success_loc"].format(html.escape(str(full_addr)))}</div>',
        unsafe_allow_html=True,
    )

    # ✅ Prefilter by bounding box (performance)
    lat_min, lat_max, lon_min, lon_max = _bounding_box(user_lat, user_lon, search_radius + 0.3)
    df_toilet_pref = df_toilet[
        (df_toilet["lat"] >= lat_min) & (df_toilet["lat"] <= lat_max) &
        (df_toilet["lon"] >= lon_min) & (df_toilet["lon"] <= lon_max)
    ].copy()

    # ✅ Fast vectorized distances
    df_toilet_d = add_distance_fast(df_toilet_pref, user_lat, user_lon)
    nearby_toilet = df_toilet_d[df_toilet_d["dist"] <= search_radius].sort_values("dist")

    df_subway_d = add_distance_fast(df_subway, user_lat, user_lon)
    nearby_subway = df_subway_d[df_subway_d["dist"] <= search_radius].sort_values("dist")

    df_store_d = add_distance_fast(df_store, user_lat, user_lon)
    nearby_store = df_store_d[df_store_d["dist"] <= search_radius].sort_values("dist")

    # Metrics
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(label=txt["metric_toilet"], value=len(nearby_toilet))
    with m2:
        st.metric(label=txt["metric_subway"], value=len(nearby_subway))
    with m3:
        nearest = f"{nearby_toilet.iloc[0]['dist']:.1f} km" if not nearby_toilet.empty else "-"
        st.metric(label=txt["metric_nearest"], value=nearest)
    st.markdown("---")

    tab_map, tab_list, tab_ai, tab_vlog, tab_feedback = st.tabs(
        [txt["tab_map"], txt["tab_list"], txt["tab_ai"], txt["tab_vlog"], txt["tab_feedback"]]
    )

    selected_name = None
    selected_row = None

    # List Tab
    with tab_list:
        if nearby_toilet.empty:
            st.warning(txt["warn_no_result"])
        else:
            left, right = st.columns([1, 1])
            with left:
                search_keyword = st.text_input("🔍 " + txt["search_placeholder"])
                if search_keyword:
                    filtered = nearby_toilet[nearby_toilet["name"].astype(str).str.contains(search_keyword, na=False)]
                else:
                    filtered = nearby_toilet

                if filtered.empty:
                    st.warning(txt["warn_no_result"])
                else:
                    selected_name = st.selectbox(txt["select_label"], filtered["name"].tolist())
                    selected_row = filtered[filtered["name"] == selected_name].iloc[0]

            with right:
                if selected_row is not None:
                    st.markdown(
                        f"""
                        <div class="card">
                            <h4 style="color:#2962FF; margin-top:0;">{html.escape(str(selected_row['name']))}</h4>
                            <p style="margin-bottom:8px;"><b>📍 {txt['col_addr']}</b><br>{html.escape(str(selected_row.get('addr','-')))}</p>
                            <p style="margin-bottom:0px;"><b>⏰ {txt['col_time']}</b><br>{html.escape(str(selected_row.get('hours','-')))}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    icons = facility_icons(selected_row)
                    if icons:
                        st.info(f"**{txt['facility']}:** {icons}")

                    with st.expander(txt["detail_title"]):
                        st.write(f"- 기저귀교환대: {selected_row.get('diaper','-')}")
                        st.write(f"- 안전시설: 비상벨({selected_row.get('bell','-')}), CCTV({selected_row.get('cctv','-')})")
                        st.write(f"- 남녀공용: {selected_row.get('unisex','-')}")

            st.markdown("#### Nearby Results")
            st.dataframe(
                filtered[["name", "dist", "addr", "hours"]].assign(dist=lambda d: d["dist"].round(2)),
                use_container_width=True,
                hide_index=True,
            )

    # Map Tab
    with tab_map:
        m = build_map(
            user_lat=user_lat,
            user_lon=user_lon,
            txt=txt,
            nearby_toilet=nearby_toilet,
            nearby_subway=nearby_subway,
            nearby_store=nearby_store,
            show_toilet=show_toilet,
            show_subway=show_subway,
            show_store=show_store,
            selected_name=selected_name,
        )
        st_folium(m, height=560, use_container_width=True)

    # AI Tab
    with tab_ai:
        if nearby_toilet.empty:
            st.warning(txt["warn_no_result"])
        else:
            st.markdown(
                f"""
                <div class="info-box">
                    <h3 style="margin-top:0; color:#0D47A1;">{txt['ai_title']}</h3>
                    <p style="margin-bottom:0;">{txt['ai_desc']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.form("ai_form"):
                user_question = st.text_input(txt["question_label"], placeholder=txt["ai_placeholder"])
                submitted = st.form_submit_button(txt["ai_btn"])
                if submitted and user_question:
                    if not OPENAI_API_KEY:
                        st.warning(txt["ai_need_key"])
                    else:
                        with st.spinner(txt["ai_thinking"]):
                            ans = ask_ai_recommendation(nearby_toilet, user_question, OPENAI_API_KEY)
                            st.info(ans)

    # Vlog Tab
    with tab_vlog:
        if not YOUTUBE_API_KEY:
            st.warning(txt["youtube_need_key"])
        else:
            query = f"{user_address} 맛집 핫플"
            with st.spinner(txt["finding_vlogs"]):
                urls = search_youtube_videos(query, YOUTUBE_API_KEY, max_results=3)
            if urls:
                cols = st.columns(len(urls))
                for i, url in enumerate(urls):
                    with cols[i]:
                        st.video(url)
                st.caption(f"👀 '{query}' 검색 결과")
            else:
                st.caption(txt["vlog_empty"])

    # Feedback Tab
    with tab_feedback:
        st.subheader(txt["fb_title"])
        with st.form("feedback_form"):
            fb_type = st.selectbox(txt["fb_type"], txt["fb_types"])
            fb_msg = st.text_area(txt["fb_msg"])
            sent = st.form_submit_button(txt["fb_btn"])
            if sent:
                save_feedback(fb_type, fb_msg)
                st.success(txt["fb_success"])


if __name__ == "__main__":
    main()
