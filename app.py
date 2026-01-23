import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import os
from datetime import datetime
import requests

st.set_page_config(layout="wide", page_title="서울시 공중화장실 찾기")

# 🔒 [보안] API Key 가져오기 (Secrets)
try:
    YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
except:
    YOUTUBE_API_KEY = ""

# 🎨 [CSS 스타일]
st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #FFFFFF; }
    section[data-testid="stSidebar"] { background-color: #F8F9FA; border-right: 1px solid #EAEAEA; }
    h1 { color: #111111; font-weight: 800; letter-spacing: -1.5px; }
    h2, h3 { color: #333333; font-weight: 700; letter-spacing: -1px; }
    div[data-testid="stMetricValue"] { color: #2962FF; font-weight: 800; font-size: 36px !important; }
    div.stButton > button { background-color: #2962FF; color: white; border-radius: 8px; border: none; }
    div.stButton > button:hover { background-color: #0039CB; color: white; }
    .stTextInput > div > div > input, .stSelectbox > div > div > div, .stTextArea > div > div > textarea { background-color: #F8F9FA; border-radius: 8px; border: 1px solid #E0E0E0; }
</style>
""", unsafe_allow_html=True)

lang_dict = {
    'ko': {
        'title': "SEOUL TOILET FINDER",
        'desc': "서울시 공중화장실, 지하철, 편의점 위치 안내 서비스",
        'sidebar_header': "SEARCH OPTION",
        'input_label': "현재 위치 (예: 강남역, 시청)",
        'radius_label': "검색 반경 (km)",
        'show_toilet': "공중화장실 (Toilet)",
        'show_subway': "지하철역 (Subway)",
        'show_store': "안심 편의점 (Store)",
        'upload_label': "데이터 파일 업로드 (.csv)",
        'error_file': "⚠️ 데이터 파일을 찾을 수 없습니다.",
        'success_loc': "📍 위치 확인됨: {}",
        'metric_label': "검색된 시설",
        'metric_dist': "가장 가까운 곳",
        'search_placeholder': "시설 이름으로 검색...",
        'select_label': "시설 선택 (상세보기)",
        'warn_no_result': "검색 결과가 없습니다.",
        'popup_current': "현 위치",
        'error_no_loc': "위치를 찾을 수 없습니다.",
        'btn_label': "Switch to English",
        'detail_title': "DETAILS",
        'col_name': "이름",
        'col_addr': "주소",
        'col_time': "운영시간",
        'col_facility': "주요시설",
        'fb_title': "FEEDBACK",
        'fb_type': "유형 선택",
        'fb_types': ["정보 수정", "오류 신고", "기타 의견"],
        'fb_msg': "내용을 입력해주세요",
        'fb_btn': "의견 보내기",
        'fb_success': "소중한 의견이 전달되었습니다. 감사합니다! 💙",
        'youtube_title': "📺 주변 분위기 (Vlog)",
        'youtube_error': "영상을 불러올 수 없습니다.",
        'youtube_need_key': "⚠️ 설정(Secrets)에 YouTube API Key를 등록해주세요."
    },
    'en': {
        'title': "SEOUL TOILET FINDER",
        'desc': "Find nearby public toilets, subway stations, and safe stores.",
        'sidebar_header': "SEARCH OPTION",
        'input_label': "Enter Location (e.g., Gangnam Station)",
        'radius_label': "Search Radius (km)",
        'show_toilet': "Public Toilet",
        'show_subway': "Subway Station",
        'show_store': "Convenience Store",
        'upload_label': "Upload CSV File",
        'error_file': "⚠️ Data file missing.",
        'success_loc': "📍 Location: {}",
        'metric_label': "Found Places",
        'metric_dist': "Nearest",
        'search_placeholder': "Search by name...",
        'select_label': "Select Place",
        'warn_no_result': "No results found.",
        'popup_current': "Current Location",
        'error_no_loc': "Location not found.",
        'btn_label': "한국어로 변경",
        'detail_title': "DETAILS",
        'col_name': "Name",
        'col_addr': "Address",
        'col_time': "Hours",
        'col_facility': "Facilities",
        'fb_title': "FEEDBACK",
        'fb_type': "Type",
        'fb_types': ["Correction", "Bug Report", "Other"],
        'fb_msg': "Message",
        'fb_btn': "Submit",
        'fb_success': "Thank you! Feedback sent. 💙",
        'youtube_title': "📺 Nearby Vibe (Vlog)",
        'youtube_error': "Cannot load video.",
        'youtube_need_key': "⚠️ Please set YouTube API Key in Secrets."
    }
}

if 'lang' not in st.session_state: st.session_state.lang = 'ko'
def toggle_language(): st.session_state.lang = 'en' if st.session_state.lang == 'ko' else 'ko'
txt = lang_dict[st.session_state.lang]

# 유튜브 검색 함수
def search_youtube(query):
    if not YOUTUBE_API_KEY: return []
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': f"{query} 맛집 핫플 브이로그", 
        'key': YOUTUBE_API_KEY,
        'maxResults': 3,
        'type': 'video'
    }
    video_urls = []
    try:
        response = requests.get(search_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                for item in data['items']:
                    video_id = item['id']['videoId']
                    video_urls.append(f"https://www.youtube.com/watch?v={video_id}")
    except:
        pass
    return video_urls

def save_feedback(fb_type, message):
    file_name = 'user_feedback.csv'
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_data = pd.DataFrame([[timestamp, fb_type, message]], columns=['Time', 'Type', 'Message'])
    if not os.path.exists(file_name): new_data.to_csv(file_name, index=False, encoding='utf-8-sig')
    else: new_data.to_csv(file_name, mode='a', header=False, index=False, encoding='utf-8-sig')

def get_sample_extra_data():
    subway_data = [{'name': '시청역 1호선', 'lat': 37.5635, 'lon': 126.9754}, {'name': '시청역 2호선', 'lat': 37.5620, 'lon': 126.9750}, {'name': '을지로입구역', 'lat': 37.5660, 'lon': 126.9826}, {'name': '광화문역', 'lat': 37.5716, 'lon': 126.9768}, {'name': '종각역', 'lat': 37.5702, 'lon': 126.9831}, {'name': '명동역', 'lat': 37.5609, 'lon': 126.9863}, {'name': '강남역', 'lat': 37.4979, 'lon': 127.0276}, {'name': '홍대입구역', 'lat': 37.5575, 'lon': 126.9245}]
    store_data = [{'name': 'CU 시청광장점', 'lat': 37.5640, 'lon': 126.9770}, {'name': 'GS25 을지로점', 'lat': 37.5655, 'lon': 126.9810}, {'name': '세븐일레븐 무교점', 'lat': 37.5675, 'lon': 126.9790}, {'name': 'CU 강남대로점', 'lat': 37.4985, 'lon': 127.0280}, {'name': 'GS25 홍대파크', 'lat': 37.5580, 'lon': 126.9250}]
    return pd.DataFrame(subway_data), pd.DataFrame(store_data)

@st.cache_data
def load_data(file):
    try: df = pd.read_csv(file, encoding='utf-8')
    except:
        try: df = pd.read_csv(file, encoding='cp949')
        except: df = pd.read_csv(file, encoding='euc-kr')
    target_cols = {'건물명': 'name', '도로명주소': 'addr', '개방시간': 'hours', 'x 좌표': 'lon', 'y 좌표': 'lat', '남녀공용화장실여부': 'unisex', '기저귀교환대장소': 'diaper', '비상벨설치여부': 'bell', 'CCTV설치여부': 'cctv'}
    existing_cols = [c for c in target_cols.keys() if c in df.columns]
    df = df[existing_cols]
    df.rename(columns=target_cols, inplace=True)
    for col in ['unisex', 'diaper', 'bell', 'cctv']:
        if col not in df.columns: df[col] = '-'
        else: df[col] = df[col].fillna('정보없음')
    for col in df.columns:
        if df[col].dtype == object: df[col] = df[col].astype(str).str.replace('|', '', regex=False)
    if 'lat' in df.columns and 'lon' in df.columns:
        df = df[(df['lat'] > 37.4) & (df['lat'] < 37.8)]
        df = df[(df['lon'] > 126.7) & (df['lon'] < 127.3)]
    return df

with st.sidebar:
    st.button(txt['btn_label'], on_click=toggle_language)
    st.divider()
    st.subheader(txt['sidebar_header'])
    show_toilet = st.checkbox(txt['show_toilet'], value=True)
    show_subway = st.checkbox(txt['show_subway'], value=True)
    show_store = st.checkbox(txt['show_store'], value=False)
    st.divider()
    uploaded_file = st.file_uploader(txt['upload_label'], type=['csv'])
    default_val = "서울시청" if st.session_state.lang == 'ko' else "Seoul City Hall"
    user_address = st.text_input(txt['input_label'], default_val)
    search_radius = st.slider(txt['radius_label'], 0.5, 5.0, 1.0)
    st.divider()
    if st.checkbox("Admin Mode"):
        if os.path.exists('user_feedback.csv'): st.write("📥 Feedback List:"); st.dataframe(pd.read_csv('user_feedback.csv'))
        else: st.caption("No feedback yet.")

st.title(txt['title'])
st.caption(txt['desc'])

df_toilet = None
if uploaded_file: df_toilet = load_data(uploaded_file)
else:
    try: df_toilet = load_data('seoul_toilet.csv')
    except: st.warning(txt['error_file']); st.stop()

df_subway, df_store = get_sample_extra_data()

# 선택된 화장실 정보를 담을 변수 초기화
row = None

if user_address and df_toilet is not None:
    geolocator = Nominatim(user_agent="korea_toilet_fullwidth_v1", timeout=10)
    try:
        search_query = f"Seoul {user_address}" if "Seoul" not in user_address and "서울" not in user_address else user_address
        location = geolocator.geocode(search_query)
        if location:
            user_lat, user_lon = location.latitude, location.longitude
            st.success(txt['success_loc'].format(location.address))
            
            def calculate_distance(row): return geodesic((user_lat, user_lon), (row['lat'], row['lon'])).km
            df_toilet['dist'] = df_toilet.apply(calculate_distance, axis=1)
            nearby_toilet = df_toilet[df_toilet['dist'] <= search_radius].sort_values(by='dist')
            df_subway['dist'] = df_subway.apply(calculate_distance, axis=1)
            nearby_subway = df_subway[df_subway['dist'] <= search_radius]
            df_store['dist'] = df_store.apply(calculate_distance, axis=1)
            nearby_store = df_store[df_store['dist'] <= search_radius]
            
            st.markdown("---")
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1: st.metric(label="TOILET", value=f"{len(nearby_toilet)}")
            with m_col2: st.metric(label="SUBWAY", value=f"{len(nearby_subway)}")
            with m_col3:
                 if not nearby_toilet.empty: st.metric(label="NEAREST", value=f"{nearby_toilet.iloc[0]['dist']:.1f} km")
                 else: st.metric(label="NEAREST", value="-")
            st.markdown("---")

            col1, col2 = st.columns([1, 1.5])
            
            # --- 왼쪽 컬럼 (목록 & 상세정보) ---
            with col1:
                if not nearby_toilet.empty:
                    search_keyword = st.text_input("🔍 " + txt['search_placeholder'])
                    if search_keyword: nearby_filtered = nearby_toilet[nearby_toilet['name'].str.contains(search_keyword)]
                    else: nearby_filtered = nearby_toilet

                    if not nearby_filtered.empty:
                        selected_name = st.selectbox(txt['select_label'], nearby_filtered['name'].tolist())
                        row = nearby_filtered[nearby_filtered['name'] == selected_name].iloc[0]
                        
                        st.markdown(f"""
                        <div style="background-color:#F8F9FA; padding:20px; border-radius:10px; border:1px solid #E0E0E0;">
                            <h4 style="color:#2962FF; margin-top:0;">{row['name']}</h4>
                            <p style="margin-bottom:5px;"><b>📍 {txt['col_addr']}</b><br>{row['addr']}</p>
                            <p style="margin-bottom:5px;"><b>⏰ {txt['col_time']}</b><br>{row['hours']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        safety_icons = ""
                        if row['diaper'] != '-' and row['diaper'] != '정보없음': safety_icons += "👶 "
                        if row['bell'] == 'Y' or '설치' in str(row['bell']): safety_icons += "🚨 "
                        if row['cctv'] == 'Y' or '설치' in str(row['cctv']): safety_icons += "📷 "
                        if row['unisex'] == 'Y': safety_icons += "👫"
                        if safety_icons: st.info(f"**Facility:** {safety_icons}")
                            
                        with st.expander(txt['detail_title']):
                            st.write(f"- 기저귀교환대: {row['diaper']}")
                            st.write(f"- 안전시설: 비상벨({row['bell']}), CCTV({row['cctv']})")
                            st.write(f"- 남녀공용: {row['unisex']}")

                    else: st.warning(txt['warn_no_result']); row = None
                else: st.warning(txt['warn_no_result']); row = None

            # --- 오른쪽 컬럼 (지도) ---
            with col2:
                m = folium.Map(location=[user_lat, user_lon], zoom_start=15, tiles='CartoDB positron')
                folium.Marker([user_lat, user_lon], popup=txt['popup_current'], icon=folium.Icon(color='red', icon='user')).add_to(m)
                marker_cluster = MarkerCluster().add_to(m)
                if show_toilet:
                    for idx, r in nearby_toilet.iterrows():
                        if row is not None and r['name'] == row['name']: folium.Marker([r['lat'], r['lon']], popup=f"<b>{r['name']}</b>", icon=folium.Icon(color='green', icon='star')).add_to(m)
                        else: folium.Marker([r['lat'], r['lon']], popup=f"<b>{r['name']}</b>", icon=folium.Icon(color='green', icon='info-sign')).add_to(marker_cluster)
                if show_subway:
                    for idx, r in nearby_subway.iterrows(): folium.Marker([r['lat'], r['lon']], popup=f"<b>🚇 {r['name']}</b>", tooltip=r['name'], icon=folium.Icon(color='orange', icon='arrow-down', prefix='fa')).add_to(m)
                if show_store:
                    for idx, r in nearby_store.iterrows(): folium.Marker([r['lat'], r['lon']], popup=f"<b>🏪 {r['name']}</b>", tooltip=r['name'], icon=folium.Icon(color='purple', icon='shopping-cart', prefix='fa')).add_to(m)
                st_folium(m, width="100%", height=500)
            
            # =================================================================
            # 📺 [NEW] 유튜브 영상 섹션 (컬럼 밖으로 꺼내서 넓게 배치)
            # =================================================================
            if row is not None:
                st.markdown("---")
                st.subheader(txt['youtube_title'])
                
                if not YOUTUBE_API_KEY:
                    st.warning(txt['youtube_need_key'])
                else:
                    with st.spinner("Finding Vlogs..."):
                        yt_query = f"{user_address} 맛집 핫플"
                        video_urls = search_youtube(yt_query)
                        
                        if video_urls:
                            # 넓어진 공간을 3등분해서 꽉 채우기
                            cols = st.columns(len(video_urls))
                            for idx, url in enumerate(video_urls):
                                with cols[idx]:
                                    st.video(url)
                            st.caption(f"👀 '{yt_query}' 검색 결과")
                        else:
                            st.caption("관련 영상을 찾을 수 없습니다.")

        else: st.error(txt['error_no_loc'])
    except Exception as e:
        if "503" in str(e): st.error("⚠️ Server busy. Try again.")
        else: st.error(f"Error: {e}")

st.markdown("---")
st.subheader(txt['fb_title'])
with st.form("feedback_form"):
    fb_type = st.selectbox(txt['fb_type'], txt['fb_types'])
    fb_msg = st.text_area(txt['fb_msg'])
    submitted = st.form_submit_button(txt['fb_btn'])
    if submitted:
        save_feedback(fb_type, fb_msg)
        st.success(txt['fb_success'])
