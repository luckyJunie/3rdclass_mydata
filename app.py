import os
from datetime import datetime
from urllib.parse import quote
from typing import Optional, Tuple, Dict, List
from functools import lru_cache

import pandas as pd
import streamlit as st
import requests
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import openai


# =============================================================================
# CONFIG & CONSTANTS
# =============================================================================
APP_CONFIG = {
    "layout": "wide",
    "page_title": "SEOUL TOILET FINDER",
    "page_icon": "🚻",
}

SEOUL_BOUNDS = {
    "lat_min": 37.4,
    "lat_max": 37.8,
    "lon_min": 126.7,
    "lon_max": 127.3,
}

CACHE_TTL = 60 * 20  # 20 minutes


# =============================================================================
# STREAMLIT SETUP
# =============================================================================
st.set_page_config(**APP_CONFIG)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def get_secret(key: str) -> str:
    """Safely retrieve secrets from Streamlit config."""
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""


@lru_cache(maxsize=128)
def get_api_keys() -> Tuple[str, str]:
    """Cache API keys to avoid repeated secret lookups."""
    return get_secret("YOUTUBE_API_KEY"), get_secret("OPENAI_API_KEY")


# =============================================================================
# STYLING
# =============================================================================
def inject_css():
    """Inject optimized CSS with improved mobile responsiveness."""
    st.markdown(
        """
        <style>
            @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
            
            * { font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; }
            
            .stApp { 
                background-color: #FFFFFF;
                transition: background-color 0.3s ease;
            }

            /* Sidebar */
            section[data-testid="stSidebar"] {
                background-color: #F8F9FA;
                border-right: 1px solid #EAEAEA;
            }
            
            /* Typography */
            h2, h3, h4 { 
                color: #0039CB; 
                font-weight: 700; 
                letter-spacing: -0.5px;
                margin-top: 0.5rem;
            }

            /* Big Title - Responsive */
            .big-title {
                color: #2962FF;
                font-size: clamp(2.5rem, 8vw, 4.5rem);
                font-weight: 900;
                letter-spacing: -2px;
                line-height: 1.0;
                margin-bottom: 1rem;
                text-shadow: 2px 2px 0px #E3F2FD;
            }

            /* Form Elements */
            div[data-baseweb="checkbox"] div[aria-checked="true"] {
                background-color: #2962FF !important;
                border-color: #2962FF !important;
            }

            .stTextInput > div > div > input:focus {
                border-color: #2962FF !important;
                box-shadow: 0 0 0 1px #2962FF !important;
            }

            /* Metrics - Responsive */
            div[data-testid="stMetricValue"] {
                color: #2962FF !important;
                font-weight: 800;
                font-size: clamp(24px, 5vw, 42px) !important;
            }
            
            div[data-testid="stMetricLabel"] { 
                color: #666666; 
                font-size: clamp(12px, 2vw, 14px);
            }

            /* Buttons */
            div.stButton > button {
                background: linear-gradient(135deg, #2962FF 0%, #0039CB 100%);
                color: white;
                border-radius: 10px;
                border: none;
                padding: 0.6rem 1.4rem;
                font-weight: 700;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 2px 8px rgba(41, 98, 255, 0.2);
            }
            
            div.stButton > button:hover {
                background: linear-gradient(135deg, #0039CB 0%, #002ba1 100%);
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(41, 98, 255, 0.3);
            }
            
            div.stButton > button:active {
                transform: translateY(0);
            }

            /* Boxes */
            .info-box {
                background: linear-gradient(135deg, #E3F2FD 0%, #F5F9FF 100%);
                padding: 1.2rem;
                border-radius: 12px;
                border: 1px solid #90CAF9;
                margin-bottom: 1rem;
                color: #0D47A1;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            
            .location-box {
                background: linear-gradient(90deg, #E8F0FE 0%, #F0F4FF 100%);
                padding: 1rem 1.2rem;
                border-radius: 10px;
                border-left: 5px solid #2962FF;
                color: #1565C0;
                font-weight: 600;
                margin-bottom: 1rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            
            .card {
                background-color: #F8F9FA;
                padding: 1.2rem;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            
            .card:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                transform: translateY(-2px);
            }

            /* Tabs - Enhanced */
            div[data-testid="stTabs"] {
                margin-top: 0.5rem;
            }
            
            div[data-testid="stTabs"] button {
                font-size: clamp(16px, 3vw, 20px) !important;
                font-weight: 900 !important;
                color: #2962FF !important;
                padding: 0.8rem 1.2rem !important;
                transition: all 0.2s ease;
            }
            
            div[data-testid="stTabs"] button:hover {
                background-color: #F0F4FF;
            }
            
            div[data-testid="stTabs"] button[aria-selected="true"] {
                color: #002ba1 !important;
                border-bottom: 4px solid #2962FF !important;
                background-color: #F5F9FF;
            }
            
            div[data-testid="stTabs"] [data-baseweb="tab-list"] {
                border-bottom: 2px solid #E3F2FD !important;
            }

            /* Loading Spinner */
            .stSpinner > div {
                border-top-color: #2962FF !important;
            }

            /* Responsive adjustments */
            @media (max-width: 768px) {
                .big-title {
                    margin-bottom: 0.5rem;
                }
                
                div.stButton > button {
                    width: 100%;
                    padding: 0.7rem 1rem;
                }
                
                .card {
                    padding: 1rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# I18N (INTERNATIONALIZATION)
# =============================================================================
TRANSLATIONS = {
    "ko": {
        "desc": "서울시 공중화장실, 지하철, 편의점 위치 안내 서비스",
        "sidebar_header": "검색 옵션",
        "input_label": "현재 위치 (예: 강남역, 시청)",
        "radius_label": "검색 반경 (km)",
        "show_toilet": "공중화장실 🚻",
        "show_subway": "지하철역 🚇",
        "show_store": "안심 편의점 🏪",
        "error_file": "⚠️ 데이터 파일을 찾을 수 없습니다.",
        "success_loc": "📍 위치 확인: {}",
        "warn_no_result": "검색 결과가 없습니다.",
        "popup_current": "현재 위치",
        "error_no_loc": "위치를 찾을 수 없습니다. 다시 시도해주세요.",
        "btn_label": "Switch to English",
        "detail_title": "상세 정보",
        "col_addr": "주소",
        "col_time": "운영시간",
        "fb_title": "피드백 보내기",
        "fb_type": "유형",
        "fb_types": ["정보 수정", "오류 신고", "기타 의견"],
        "fb_msg": "내용을 입력해주세요",
        "fb_btn": "의견 보내기",
        "fb_success": "소중한 의견 감사합니다! 💙",
        "youtube_title": "📺 주변 브이로그",
        "youtube_need_key": "⚠️ YouTube API Key를 설정해주세요.",
        "ai_title": "🤖 AI 화장실 추천 (Beta)",
        "ai_desc": "원하는 조건을 말하면 AI가 최적의 화장실을 찾아드립니다.",
        "ai_placeholder": "예: 아이와 함께 갈 수 있는 깨끗한 화장실 추천해줘",
        "ai_btn": "AI 추천 받기 ✨",
        "ai_thinking": "AI가 분석 중입니다...",
        "ai_need_key": "⚠️ OpenAI API Key가 필요합니다.",
        "search_placeholder": "시설명으로 검색...",
        "select_label": "시설 선택",
        "admin_mode": "관리자 모드",
        "feedback_list": "📥 피드백 목록",
        "no_feedback": "아직 피드백이 없습니다.",
        "tab_map": "🗺️ 지도",
        "tab_list": "📋 리스트",
        "tab_ai": "🤖 AI 추천",
        "tab_vlog": "📺 브이로그",
        "tab_feedback": "💬 피드백",
        "metric_toilet": "화장실",
        "metric_subway": "지하철",
        "metric_nearest": "최단거리",
        "finding_vlogs": "브이로그 검색 중...",
        "facility": "편의시설",
        "question_label": "💭 질문",
        "search_web": "지도에서 보기",
        "route_try": "길찾기",
        "route_note": "* PC에서는 앱 링크가 제한될 수 있습니다.",
        "loading": "로딩 중...",
        "input_location": "사이드바에서 위치를 입력해주세요 👈",
    },
    "en": {
        "desc": "Find nearby public toilets, subway stations, and stores in Seoul",
        "sidebar_header": "Search Options",
        "input_label": "Current Location (e.g., Gangnam Station)",
        "radius_label": "Search Radius (km)",
        "show_toilet": "Public Toilets 🚻",
        "show_subway": "Subway Stations 🚇",
        "show_store": "Stores 🏪",
        "error_file": "⚠️ Data file not found.",
        "success_loc": "📍 Location: {}",
        "warn_no_result": "No results found.",
        "popup_current": "Current Location",
        "error_no_loc": "Location not found. Please try again.",
        "btn_label": "한국어로 변경",
        "detail_title": "Details",
        "col_addr": "Address",
        "col_time": "Hours",
        "fb_title": "Send Feedback",
        "fb_type": "Type",
        "fb_types": ["Info Correction", "Bug Report", "Other"],
        "fb_msg": "Your message",
        "fb_btn": "Submit",
        "fb_success": "Thank you for your feedback! 💙",
        "youtube_title": "📺 Nearby Vlogs",
        "youtube_need_key": "⚠️ Please set YouTube API Key.",
        "ai_title": "🤖 AI Toilet Recommendation (Beta)",
        "ai_desc": "Tell AI what you need, and get the best recommendation.",
        "ai_placeholder": "e.g., Clean toilet with baby changing station",
        "ai_btn": "Get AI Recommendation ✨",
        "ai_thinking": "AI is analyzing...",
        "ai_need_key": "⚠️ OpenAI API Key required.",
        "search_placeholder": "Search by name...",
        "select_label": "Select Facility",
        "admin_mode": "Admin Mode",
        "feedback_list": "📥 Feedback List",
        "no_feedback": "No feedback yet.",
        "tab_map": "🗺️ Map",
        "tab_list": "📋 List",
        "tab_ai": "🤖 AI",
        "tab_vlog": "📺 Vlog",
        "tab_feedback": "💬 Feedback",
        "metric_toilet": "Toilets",
        "metric_subway": "Subway",
        "metric_nearest": "Nearest",
        "finding_vlogs": "Finding vlogs...",
        "facility": "Facilities",
        "question_label": "💭 Question",
        "search_web": "View on Map",
        "route_try": "Get Directions",
        "route_note": "* App links may not work on desktop.",
        "loading": "Loading...",
        "input_location": "Please enter location in sidebar 👈",
    },
}


def init_session_state():
    """Initialize session state variables."""
    if "lang" not in st.session_state:
        st.session_state.lang = "ko"


def toggle_language():
    """Toggle between Korean and English."""
    st.session_state.lang = "en" if st.session_state.lang == "ko" else "ko"


def get_text() -> Dict[str, str]:
    """Get current language translations."""
    return TRANSLATIONS[st.session_state.lang]


# =============================================================================
# DATA LOADING
# =============================================================================
@st.cache_data(show_spinner=False, ttl=3600)
def load_toilet_data(file_path: str = "seoul_toilet.csv") -> pd.DataFrame:
    """
    Load and preprocess toilet data with optimized error handling.
    
    Returns:
        Preprocessed DataFrame with cleaned columns
    """
    # Try multiple encodings
    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            break
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    else:
        raise FileNotFoundError(f"Could not load {file_path}")

    # Column mapping
    column_map = {
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

    # Select and rename columns
    existing_cols = [c for c in column_map if c in df.columns]
    df = df[existing_cols].rename(columns=column_map)

    # Fill missing values
    for col in ["unisex", "diaper", "bell", "cctv", "addr", "hours"]:
        if col not in df.columns:
            df[col] = "-"
        else:
            df[col] = df[col].fillna("정보없음")

    # Clean pipe characters
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.replace("|", "", regex=False)

    # Filter by Seoul bounds
    if "lat" in df.columns and "lon" in df.columns:
        df = df[
            (df["lat"] > SEOUL_BOUNDS["lat_min"]) & 
            (df["lat"] < SEOUL_BOUNDS["lat_max"]) &
            (df["lon"] > SEOUL_BOUNDS["lon_min"]) & 
            (df["lon"] < SEOUL_BOUNDS["lon_max"])
        ]

    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_extra_facilities() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load subway and store data (sample data for demo)."""
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


# =============================================================================
# GEOCODING
# =============================================================================
@st.cache_data(show_spinner=False, ttl=3600)
def geocode_address(address: str) -> Optional[Tuple[float, float, str]]:
    """
    Geocode address with caching and error handling.
    
    Returns:
        Tuple of (latitude, longitude, full_address) or None if failed
    """
    try:
        geolocator = Nominatim(user_agent="seoul_toilet_finder_v6", timeout=10)
        search_query = (
            f"Seoul {address}"
            if "Seoul" not in address and "서울" not in address
            else address
        )
        
        location = geolocator.geocode(search_query)
        
        if location:
            return float(location.latitude), float(location.longitude), location.address
        return None
        
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
        return None


def calculate_distance(df: pd.DataFrame, user_lat: float, user_lon: float) -> pd.DataFrame:
    """
    Add distance column to DataFrame (vectorized for performance).
    
    Args:
        df: DataFrame with 'lat' and 'lon' columns
        user_lat: User latitude
        user_lon: User longitude
        
    Returns:
        DataFrame with added 'dist' column
    """
    df = df.copy()
    df["dist"] = df.apply(
        lambda row: geodesic((user_lat, user_lon), (row["lat"], row["lon"])).km,
        axis=1
    )
    return df


# =============================================================================
# ROUTING & MAPS
# =============================================================================
def create_naver_route_url(
    user_lat: float,
    user_lon: float,
    dest_lat: float,
    dest_lon: float,
    dest_name: str,
    mode: str = "walk"
) -> str:
    """Generate Naver Map route URL scheme."""
    sname = quote("현재 위치")
    dname = quote(str(dest_name))
    appname = quote("seoul-toilet-finder")
    
    return (
        f"nmap://route/{mode}"
        f"?slat={user_lat}&slng={user_lon}&sname={sname}"
        f"&dlat={dest_lat}&dlng={dest_lon}&dname={dname}"
        f"&appname={appname}"
    )


def get_facility_icons(row: pd.Series) -> str:
    """Generate facility icon string from row data."""
    icons = []
    
    if str(row.get("diaper", "-")) not in ("-", "정보없음", "nan"):
        icons.append("👶")
    
    if str(row.get("bell", "")) in ("Y", "설치"):
        icons.append("🚨")
    
    if str(row.get("cctv", "")) in ("Y", "설치"):
        icons.append("📷")
    
    if str(row.get("unisex", "")) == "Y":
        icons.append("👫")
    
    return " ".join(icons)


def create_map(
    user_lat: float,
    user_lon: float,
    txt: Dict[str, str],
    toilets: pd.DataFrame,
    subways: pd.DataFrame,
    stores: pd.DataFrame,
    show_toilet: bool,
    show_subway: bool,
    show_store: bool,
    selected_name: Optional[str] = None,
) -> folium.Map:
    """
    Create optimized Folium map with all markers.
    
    Args:
        user_lat, user_lon: User location
        txt: Translation dictionary
        toilets, subways, stores: DataFrames with facility data
        show_*: Boolean flags for each facility type
        selected_name: Name of selected facility to highlight
        
    Returns:
        Folium Map object
    """
    # Initialize map
    m = folium.Map(
        location=[user_lat, user_lon],
        zoom_start=15,
        tiles="CartoDB positron"
    )

    # User location marker
    folium.Marker(
        [user_lat, user_lon],
        popup=txt["popup_current"],
        tooltip=txt["popup_current"],
        icon=folium.Icon(color="red", icon="user", prefix="fa"),
    ).add_to(m)

    # Marker cluster for performance
    marker_cluster = MarkerCluster(
        options={
            'maxClusterRadius': 50,
            'spiderfyOnMaxZoom': True,
            'showCoverageOnHover': False
        }
    ).add_to(m)

    # Add toilet markers
    if show_toilet and toilets is not None and not toilets.empty:
        for _, row in toilets.iterrows():
            is_selected = (selected_name is not None and row["name"] == selected_name)
            
            route_url = create_naver_route_url(
                user_lat, user_lon,
                row["lat"], row["lon"],
                row["name"]
            )
            
            web_url = f"https://map.naver.com/v5/search/{quote(str(row['name']))}"
            
            popup_html = f"""
            <div style="font-family:Pretendard,sans-serif;font-size:14px;min-width:250px;">
              <div style="font-weight:900;margin-bottom:6px;color:#2962FF;">🚻 {row['name']}</div>
              <div style="color:#666;margin-bottom:10px;">📍 {float(row['dist']):.2f} km</div>
              
              <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <a href="{web_url}" onclick="
                    try {{
                      var ifr=document.createElement('iframe');
                      ifr.style.display='none';
                      ifr.src='{route_url}';
                      document.body.appendChild(ifr);
                      setTimeout(function(){{}},1200);
                    }} catch(e) {{}}
                  " style="text-decoration:none;">
                  <span style="background:#2962FF;color:white;padding:6px 12px;border-radius:8px;font-weight:700;font-size:13px;">
                    {txt['route_try']}
                  </span>
                </a>
                
                <a href="{web_url}" target="_blank" style="text-decoration:none;">
                  <span style="background:#E3F2FD;color:#0D47A1;padding:6px 12px;border-radius:8px;font-weight:700;border:1px solid #90CAF9;font-size:13px;">
                    {txt['search_web']}
                  </span>
                </a>
              </div>
              
              <div style="margin-top:8px;font-size:11px;color:#999;">
                {txt['route_note']}
              </div>
            </div>
            """
            
            popup = folium.Popup(
                folium.IFrame(html=popup_html, width=280, height=160),
                max_width=320
            )
            
            marker_params = {
                "location": [row["lat"], row["lon"]],
                "tooltip": row["name"],
                "popup": popup,
            }
            
            if is_selected:
                marker_params["icon"] = folium.Icon(color="green", icon="star", prefix="fa")
                folium.Marker(**marker_params).add_to(m)
            else:
                marker_params["icon"] = folium.Icon(color="green", icon="info-sign")
                folium.Marker(**marker_params).add_to(marker_cluster)

    # Add subway markers
    if show_subway and subways is not None and not subways.empty:
        for _, row in subways.iterrows():
            folium.Marker(
                [row["lat"], row["lon"]],
                popup=f"<b>🚇 {row['name']}</b>",
                tooltip=row["name"],
                icon=folium.Icon(color="orange", icon="subway", prefix="fa"),
            ).add_to(m)

    # Add store markers
    if show_store and stores is not None and not stores.empty:
        for _, row in stores.iterrows():
            folium.Marker(
                [row["lat"], row["lon"]],
                popup=f"<b>🏪 {row['name']}</b>",
                tooltip=row["name"],
                icon=folium.Icon(color="purple", icon="shopping-cart", prefix="fa"),
            ).add_to(m)

    return m


# =============================================================================
# EXTERNAL APIs
# =============================================================================
@st.cache_data(show_spinner=False, ttl=CACHE_TTL)
def search_youtube_videos(query: str, api_key: str, max_results: int = 3) -> List[str]:
    """Search YouTube videos with caching."""
    if not api_key:
        return []
    
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{query} 맛집 핫플 브이로그",
        "key": api_key,
        "maxResults": max_results,
        "type": "video",
        "relevanceLanguage": "ko",
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        items = data.get("items", [])
        
        return [
            f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            for item in items
        ]
        
    except Exception as e:
        st.warning(f"YouTube API error: {str(e)}")
        return []


def get_ai_recommendation(df: pd.DataFrame, user_query: str, api_key: str) -> str:
    """
    Get AI recommendation using OpenAI API.
    
    Args:
        df: DataFrame of nearby toilets
        user_query: User's question
        api_key: OpenAI API key
        
    Returns:
        AI response string
    """
    if not api_key:
        return "⚠️ OpenAI API Key가 필요합니다."
    
    if df is None or df.empty:
        return "주변에 검색된 화장실이 없습니다."

    # Prepare data context
    cols = ["name", "dist", "unisex", "diaper", "bell", "cctv"]
    df_slim = df[cols].head(15).copy()
    df_slim["dist"] = df_slim["dist"].round(2)
    data_csv = df_slim.to_csv(index=False)

    system_prompt = (
        "당신은 화장실 추천 전문가입니다. "
        "주어진 데이터를 바탕으로 정확하게 추천하세요. "
        "없는 정보는 추측하지 말고 '정보 없음'이라고 명시하세요."
    )
    
    user_prompt = f"""
[주변 화장실 데이터]
{data_csv}

[사용자 요청]
{user_query}

위 데이터를 분석하여 요구사항에 가장 적합한 화장실 1-2곳을 추천해주세요.
각 추천에 대해:
1. 추천 이유
2. 거리 (km)
3. 특이사항 또는 정보 부족 항목

간결하고 명확하게 작성해주세요.
"""

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"AI 오류: {str(e)}"


# =============================================================================
# FEEDBACK SYSTEM
# =============================================================================
def save_feedback(fb_type: str, message: str, filename: str = "user_feedback.csv"):
    """Save user feedback to CSV file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_row = pd.DataFrame(
        [[timestamp, fb_type, message]],
        columns=["Time", "Type", "Message"]
    )
    
    try:
        if os.path.exists(filename):
            new_row.to_csv(filename, mode="a", header=False, index=False, encoding="utf-8-sig")
        else:
            new_row.to_csv(filename, index=False, encoding="utf-8-sig")
    except Exception as e:
        st.error(f"피드백 저장 실패: {str(e)}")


# =============================================================================
# UI COMPONENTS
# =============================================================================
def render_sidebar(txt: Dict[str, str]) -> Tuple[str, float, bool, bool, bool]:
    """
    Render sidebar with all controls.
    
    Returns:
        Tuple of (address, radius, show_toilet, show_subway, show_store)
    """
    with st.sidebar:
        # Language toggle
        st.button(
            txt["btn_label"],
            on_click=toggle_language,
            use_container_width=True
        )
        
        st.divider()
        
        # Header
        st.subheader(txt["sidebar_header"])
        
        # Facility checkboxes
        show_toilet = st.checkbox(txt["show_toilet"], value=True)
        show_subway = st.checkbox(txt["show_subway"], value=True)
        show_store = st.checkbox(txt["show_store"], value=False)
        
        st.divider()
        
        # Location input
        default_location = "서울시청" if st.session_state.lang == "ko" else "Seoul City Hall"
        user_address = st.text_input(txt["input_label"], value=default_location)
        
        # Radius slider
        search_radius = st.slider(
            txt["radius_label"],
            min_value=0.5,
            max_value=5.0,
            value=1.0,
            step=0.1
        )
        
        st.divider()
        
        # Admin mode
        if st.checkbox(txt["admin_mode"]):
            st.caption(txt["feedback_list"])
            if os.path.exists("user_feedback.csv"):
                try:
                    feedback_df = pd.read_csv("user_feedback.csv")
                    st.dataframe(feedback_df, use_container_width=True)
                except Exception:
                    st.caption(txt["no_feedback"])
            else:
                st.caption(txt["no_feedback"])
    
    return user_address, search_radius, show_toilet, show_subway, show_store


def render_header(txt: Dict[str, str]):
    """Render main page header."""
    st.markdown(
        '<h1 class="big-title">SEOUL<br>TOILET FINDER</h1>',
        unsafe_allow_html=True
    )
    st.caption(txt["desc"])


def render_metrics(txt: Dict[str, str], toilets: pd.DataFrame, subways: pd.DataFrame):
    """Render metric cards."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label=txt["metric_toilet"], value=len(toilets))
    
    with col2:
        st.metric(label=txt["metric_subway"], value=len(subways))
    
    with col3:
        nearest = (
            f"{toilets.iloc[0]['dist']:.1f} km"
            if not toilets.empty
            else "-"
        )
        st.metric(label=txt["metric_nearest"], value=nearest)


def render_list_tab(txt: Dict[str, str], df: pd.DataFrame) -> Optional[pd.Series]:
    """
    Render list tab with search and selection.
    
    Returns:
        Selected row as Series or None
    """
    if df.empty:
        st.warning(txt["warn_no_result"])
        return None
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # Search box
        search_keyword = st.text_input(
            "🔍 " + txt["search_placeholder"],
            key="search_input"
        )
        
        # Filter by search
        filtered = (
            df[df["name"].str.contains(search_keyword, case=False, na=False)]
            if search_keyword
            else df
        )
        
        if filtered.empty:
            st.warning(txt["warn_no_result"])
            return None
        
        # Selection
        selected_name = st.selectbox(
            txt["select_label"],
            options=filtered["name"].tolist(),
            key="facility_select"
        )
        
        selected_row = filtered[filtered["name"] == selected_name].iloc[0]
    
    with col_right:
        if selected_row is not None:
            # Detail card
            st.markdown(
                f"""
                <div class="card">
                    <h4 style="color:#2962FF;margin-top:0;">{selected_row['name']}</h4>
                    <p style="margin-bottom:8px;">
                        <b>📍 {txt['col_addr']}</b><br>
                        {selected_row.get('addr', '-')}
                    </p>
                    <p style="margin-bottom:0;">
                        <b>⏰ {txt['col_time']}</b><br>
                        {selected_row.get('hours', '-')}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Facility icons
            icons = get_facility_icons(selected_row)
            if icons:
                st.info(f"**{txt['facility']}:** {icons}")
            
            # Expandable details
            with st.expander(txt["detail_title"]):
                st.write(f"- 기저귀교환대: {selected_row.get('diaper', '-')}")
                st.write(f"- 비상벨: {selected_row.get('bell', '-')}")
                st.write(f"- CCTV: {selected_row.get('cctv', '-')}")
                st.write(f"- 남녀공용: {selected_row.get('unisex', '-')}")
    
    # Results table
    st.markdown("#### 검색 결과")
    display_df = filtered[["name", "dist", "addr", "hours"]].copy()
    display_df["dist"] = display_df["dist"].round(2)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "name": "시설명",
            "dist": "거리(km)",
            "addr": "주소",
            "hours": "운영시간"
        }
    )
    
    return selected_row


def render_ai_tab(txt: Dict[str, str], df: pd.DataFrame, api_key: str):
    """Render AI recommendation tab."""
    if df.empty:
        st.warning(txt["warn_no_result"])
        return
    
    st.markdown(
        f"""
        <div class="info-box">
            <h3 style="margin-top:0;color:#0D47A1;">{txt['ai_title']}</h3>
            <p style="margin-bottom:0;">{txt['ai_desc']}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    with st.form("ai_form", clear_on_submit=False):
        user_question = st.text_input(
            txt["question_label"],
            placeholder=txt["ai_placeholder"]
        )
        
        submitted = st.form_submit_button(txt["ai_btn"], use_container_width=True)
        
        if submitted and user_question:
            if not api_key:
                st.warning(txt["ai_need_key"])
            else:
                with st.spinner(txt["ai_thinking"]):
                    answer = get_ai_recommendation(df, user_question, api_key)
                    st.info(answer)


def render_vlog_tab(txt: Dict[str, str], location: str, api_key: str):
    """Render YouTube vlog tab."""
    if not api_key:
        st.warning(txt["youtube_need_key"])
        return
    
    query = f"{location} 맛집 핫플"
    
    with st.spinner(txt["finding_vlogs"]):
        video_urls = search_youtube_videos(query, api_key, max_results=3)
    
    if video_urls:
        cols = st.columns(len(video_urls))
        for i, url in enumerate(video_urls):
            with cols[i]:
                st.video(url)
        
        st.caption(f"👀 '{query}' 검색 결과")
    else:
        st.caption("관련 영상을 찾을 수 없습니다.")


def render_feedback_tab(txt: Dict[str, str]):
    """Render feedback form tab."""
    st.subheader(txt["fb_title"])
    
    with st.form("feedback_form", clear_on_submit=True):
        fb_type = st.selectbox(txt["fb_type"], options=txt["fb_types"])
        fb_message = st.text_area(txt["fb_msg"], height=120)
        
        submitted = st.form_submit_button(txt["fb_btn"], use_container_width=True)
        
        if submitted and fb_message:
            save_feedback(fb_type, fb_message)
            st.success(txt["fb_success"])


# =============================================================================
# MAIN APP
# =============================================================================
def main():
    """Main application logic."""
    # Initialize
    inject_css()
    init_session_state()
    txt = get_text()
    
    # Get API keys
    youtube_key, openai_key = get_api_keys()
    
    # Render sidebar
    user_address, search_radius, show_toilet, show_subway, show_store = render_sidebar(txt)
    
    # Render header
    render_header(txt)
    
    # Load data
    try:
        with st.spinner(txt["loading"]):
            df_toilet = load_toilet_data()
    except FileNotFoundError:
        st.error(txt["error_file"])
        st.stop()
    
    df_subway, df_store = load_extra_facilities()
    
    # Check if location entered
    if not user_address or not user_address.strip():
        st.info(txt["input_location"])
        st.stop()
    
    # Geocode location
    with st.spinner(txt["loading"]):
        location_result = geocode_address(user_address)
    
    if not location_result:
        st.error(txt["error_no_loc"])
        st.stop()
    
    user_lat, user_lon, full_address = location_result
    
    # Show location confirmation
    st.markdown(
        f'<div class="location-box">{txt["success_loc"].format(full_address)}</div>',
        unsafe_allow_html=True
    )
    
    # Calculate distances
    df_toilet_dist = calculate_distance(df_toilet, user_lat, user_lon)
    df_subway_dist = calculate_distance(df_subway, user_lat, user_lon)
    df_store_dist = calculate_distance(df_store, user_lat, user_lon)
    
    # Filter by radius
    nearby_toilets = df_toilet_dist[df_toilet_dist["dist"] <= search_radius].sort_values("dist")
    nearby_subways = df_subway_dist[df_subway_dist["dist"] <= search_radius].sort_values("dist")
    nearby_stores = df_store_dist[df_store_dist["dist"] <= search_radius].sort_values("dist")
    
    # Metrics
    st.markdown("---")
    render_metrics(txt, nearby_toilets, nearby_subways)
    st.markdown("---")
    
    # Tabs
    tab_map, tab_list, tab_ai, tab_vlog, tab_feedback = st.tabs([
        txt["tab_map"],
        txt["tab_list"],
        txt["tab_ai"],
        txt["tab_vlog"],
        txt["tab_feedback"]
    ])
    
    # Track selected facility
    selected_row = None
    selected_name = None
    
    # List tab
    with tab_list:
        selected_row = render_list_tab(txt, nearby_toilets)
        if selected_row is not None:
            selected_name = selected_row["name"]
    
    # Map tab
    with tab_map:
        m = create_map(
            user_lat=user_lat,
            user_lon=user_lon,
            txt=txt,
            toilets=nearby_toilets,
            subways=nearby_subways,
            stores=nearby_stores,
            show_toilet=show_toilet,
            show_subway=show_subway,
            show_store=show_store,
            selected_name=selected_name
        )
        
        st_folium(m, width=1100, height=560, returned_objects=[])
    
    # AI tab
    with tab_ai:
        render_ai_tab(txt, nearby_toilets, openai_key)
    
    # Vlog tab
    with tab_vlog:
        render_vlog_tab(txt, user_address, youtube_key)
    
    # Feedback tab
    with tab_feedback:
        render_feedback_tab(txt)


if __name__ == "__main__":
    main()
