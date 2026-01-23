import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import os
from datetime import datetime

st.set_page_config(layout="wide", page_title="서울시 공중화장실 찾기")

# 1. 다국어 설정
lang_dict = {
    'ko': {
        'title': "🚽 서울시 공중화장실 찾기",
        'desc': "화장실, 지하철, 편의점 위치를 한눈에 확인하고 의견도 남겨주세요.",
        'sidebar_header': "🔍 검색 옵션",
        'input_label': "현재 위치 입력 (예: 강남역, 시청)",
        'radius_label': "검색 반경 (km)",
        'show_toilet': "화장실 보기 (초록색)",
        'show_subway': "지하철역 보기 (노란색)",
        'show_store': "편의점 보기 (보라색)",
        'upload_label': "CSV 파일 업로드 (화장실 데이터)",
        'error_file': "⚠️ 데이터 파일을 찾을 수 없습니다. (seoul_toilet.csv)",
        'success_loc': "📍 검색된 위치: {}",
        'metric_label': "주변 시설",
        'metric_dist': "가장 가까운 화장실",
        'search_placeholder': "목록에서 화장실 이름 검색...",
        'select_label': "화장실 선택 (상세보기)",
        'warn_no_result': "조건에 맞는 화장실이 없습니다.",
        'popup_current': "현 위치",
        'error_no_loc': "위치를 찾을 수 없습니다.",
        'btn_label': "🇺🇸 Switch to English",
        'detail_title': "📋 상세 정보",
        'col_name': "이름",
        'col_addr': "주소",
        'col_time': "운영시간",
        'col_facility': "주요시설",
        'fb_title': "💬 의견 보내기",
        'fb_type': "의견 유형",
        'fb_types': ["정보 수정 요청", "버그 신고", "칭찬하기", "기타"],
        'fb_msg': "내용을 입력하세요",
        'fb_btn': "제출하기",
        'fb_success': "소중한 의견 감사합니다! 개발자에게 전달되었습니다. 💌"
    },
    'en': {
        'title': "🚽 Seoul Public Toilet Finder",
        'desc': "Find toilets, subway stations, and stores. We value your feedback!",
        'sidebar_header': "🔍 Search Options",
        'input_label': "Enter Location (e.g., Gangnam Station)",
        'radius_label': "Search Radius (km)",
        'show_toilet': "Show Toilets (Green)",
        'show_subway': "Show Subway (Yellow)",
        'show_store': "Show Stores (Purple)",
        'upload_label': "Upload CSV File (Toilet Data)",
        'error_file': "⚠️ Data file missing. (seoul_toilet.csv)",
        'success_loc': "📍 Location found: {}",
        'metric_label': "Nearby Places",
        'metric_dist': "Nearest Toilet",
        'search_placeholder': "Search toilet name...",
        'select_label': "Select a Toilet",
        'warn_no_result': "No restrooms match your search.",
        'popup_current': "Current Location",
        'error_no_loc': "Location not found.",
        'btn_label': "🇰🇷 한국어로 변경",
        'detail_title': "📋 Details",
        'col_name': "Name",
        'col_addr': "Address",
        'col_time': "Hours",
        'col_facility': "Facilities",
        'fb_title': "💬 Send Feedback",
        'fb_type': "Feedback Type",
        'fb_types': ["Data Correction", "Bug Report", "Praise", "Other"],
        'fb_msg': "Enter your message",
        'fb_btn': "Submit",
        'fb_success': "Thank you! Your feedback has been sent. 💌"
    }
}

if 'lang' not in st.session_state:
    st.session_state.lang = 'ko'

def toggle_language():
    st.session_state.lang = 'en' if st.session_state.lang == 'ko' else 'ko'

txt = lang_dict[st.session_state.lang]

# 2. 피드백 저장 함수
def save_feedback(fb_type, message):
    file_name = 'user_feedback.csv'
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_data = pd.DataFrame([[timestamp, fb_type, message]], columns=['Time', 'Type', 'Message'])
    
    if not os.path.exists(file_name):
        new_data.to_csv(file_name, index=False, encoding='utf-8-sig')
    else:
        new_data.to_csv(file_name, mode='a', header=False, index=False, encoding='utf-8-sig')

# 3. 샘플 데이터 생성
def get_sample_extra_data():
    subway_data = [
        {'name': '시청역 1호선', 'lat': 37.5635, 'lon': 126.9754},
        {'name': '시청역 2호선', 'lat': 37.5620, 'lon': 126.9750},
        {'name': '을지로입구역', 'lat': 37.5660, 'lon': 126.9826},
        {'name': '광화문역', 'lat': 37.5716, 'lon': 126.9768},
        {'name': '종각역', 'lat': 37.5702, 'lon': 126.9831},
        {'name': '명동역', 'lat': 37.5609, 'lon': 126.9863},
        {'name': '강남역', 'lat': 37.4979, 'lon': 127.0276},
        {'name': '홍대입구역', 'lat': 37.5575, 'lon': 126.9245}
    ]
    store_data = [
        {'name': 'CU 시청광장점', 'lat': 37.5640, 'lon': 126.9770},
        {'name': 'GS25 을지로점', 'lat': 37.5655, 'lon': 126.9810},
        {'name': '세븐일레븐 무교점', 'lat': 37.5675, 'lon': 126.9790},
        {'name': 'CU 강남대로점', 'lat': 37.4985, 'lon': 127.0280},
        {'name': 'GS25 홍대파크', 'lat': 37.5580, 'lon': 126.9250}
    ]
    return pd.DataFrame(subway_data), pd.DataFrame(store_data)

# 4. 데이터 로드 함수
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, encoding='utf-8')
    except:
        try:
            df = pd.read_csv(file, encoding='cp949')
        except:
            df = pd.read_csv(file, encoding='euc-kr')

    target_cols = {
        '건물명': 'name', '도로명주소': 'addr', '개방시간': 'hours', 
        'x 좌표': 'lon', 'y 좌표': 'lat',
        '남녀공용화장실여부': 'unisex', '기저귀교환대장소': 'diaper', 
        '비상벨설치여부': 'bell', 'CCTV설치여부': 'cctv'
    }
    
    existing_cols = [c for c in target_cols.keys() if c in df.columns]
    df = df[existing_cols]
    df.rename(columns=target_cols, inplace=True)
    
    for col in ['unisex', 'diaper', 'bell', 'cctv']:
        if col not in df.columns: df[col] = '-'
        else: df[col] = df[col].fillna('정보없음')

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace('|', '', regex=False)

    if 'lat' in df.columns and 'lon' in df.columns:
        df = df[(df['lat'] > 37.4) & (df['lat'] < 37.8)]
        df = df[(df['lon'] > 126.7) & (df['lon'] < 127.3)]

    return df

# 5. 사이드바 UI
with st.sidebar:
    st.button(txt['btn_label'], on_click=toggle_language)
    st.divider()
    st.header(txt['sidebar_header'])
    
    show_toilet = st.checkbox(txt['show_toilet'], value=True)
    show_subway = st.checkbox(txt['show_subway'], value=True)
    show_store = st.checkbox(txt['show_store'], value=False)
    
    st.divider()
    
    uploaded_file = st.file_uploader(txt['upload_label'], type=['csv'])
    default_val = "서울시청" if st.session_state.lang == 'ko' else "Seoul City Hall"
    user_address = st.text_input(txt['input_label'], default_val)
    search_radius = st.slider(txt['radius_label'], 0.5, 5.0, 1.0)
    
    # [NEW] 관리자용 피드백 확인 기능 (비밀스럽게 추가)
    st.divider()
    if st.checkbox("Admin Mode (View Feedback)"):
        if os.path.exists('user_feedback.csv'):
            st.write("📥 Received Feedback:")
            st.dataframe(pd.read_csv('user_feedback.csv'))
        else:
            st.write("No feedback yet.")

# 6. 메인 화면
st.title(txt['title'])
st.markdown(txt['desc'])

df_toilet = None
if uploaded_file: df_toilet = load_data(uploaded_file)
else:
    try: df_toilet = load_data('seoul_toilet.csv')
    except: st.warning(txt['error_file']); st.stop()

df_subway, df_store = get_sample_extra_data()

if user_address and df_toilet is not None:
    geolocator = Nominatim(user_agent="korea_toilet_feedback_v1", timeout=10)
    
    try:
        search_query = f"Seoul {user_address}" if "Seoul" not in user_address and "서울" not in user_address else user_address
        location = geolocator.geocode(search_query)
        
        if location:
            user_lat = location.latitude
            user_lon = location.longitude
            st.success(txt['success_loc'].format(location.address))
            
            def calculate_distance(row):
                return geodesic((user_lat, user_lon), (row['lat'], row['lon'])).km

            df_toilet['dist'] = df_toilet.apply(calculate_distance, axis=1)
            nearby_toilet = df_toilet[df_toilet['dist'] <= search_radius].sort_values(by='dist')
            
            df_subway['dist'] = df_subway.apply(calculate_distance, axis=1)
            nearby_subway = df_subway[df_subway['dist'] <= search_radius]

            df_store['dist'] = df_store.apply(calculate_distance, axis=1)
            nearby_store = df_store[df_store['dist'] <= search_radius]
            
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1: st.metric(label="화장실 (Toilet)", value=f"{len(nearby_toilet)}")
            with m_col2: st.metric(label="지하철 (Subway)", value=f"{len(nearby_subway)}")
            with m_col3:
                 if not nearby_toilet.empty: st.metric(label=txt['metric_dist'], value=f"{nearby_toilet.iloc[0]['dist']:.1f} km")
                 else: st.metric(label=txt['metric_dist'], value="-")

            st.markdown("---")

            col1, col2 = st.columns([1, 1.5])
            
            with col1:
                if not nearby_toilet.empty:
                    search_keyword = st.text_input("🔍 " + txt['search_placeholder'])
                    
                    if search_keyword: nearby_filtered = nearby_toilet[nearby_toilet['name'].str.contains(search_keyword)]
                    else: nearby_filtered = nearby_toilet

                    if not nearby_filtered.empty:
                        selected_name = st.selectbox(txt['select_label'], nearby_filtered['name'].tolist())
                        row = nearby_filtered[nearby_filtered['name'] == selected_name].iloc[0]
                        
                        st.info(f"**🏠 {row['name']}**")
                        st.write(f"**📍 {txt['col_addr']}**")
                        st.caption(f"{row['addr']}")
                        st.write(f"**⏰ {txt['col_time']}**")
                        st.caption(f"{row['hours']}")
                        
                        safety_icons = ""
                        if row['diaper'] != '-' and row['diaper'] != '정보없음': safety_icons += "👶 "
                        if row['bell'] == 'Y' or '설치' in str(row['bell']): safety_icons += "🚨 "
                        if row['cctv'] == 'Y' or '설치' in str(row['cctv']): safety_icons += "📷 "
                        if row['unisex'] == 'Y': safety_icons += "👫"
                        
                        if safety_icons: st.success(f"**Facility:** {safety_icons}")
                            
                        with st.expander(txt['detail_title']):
                            st.write(f"- 기저귀교환대: {row['diaper']}")
                            st.write(f"- 안전시설: 비상벨({row['bell']}), CCTV({row['cctv']})")
                            st.write(f"- 남녀공용: {row['unisex']}")
                    else:
                        st.warning(txt['warn_no_result'])
                        row = None
                else:
                    st.warning(txt['warn_no_result'])
                    row = None

            with col2:
                m = folium.Map(location=[user_lat, user_lon], zoom_start=15, tiles='CartoDB positron')
                folium.Marker([user_lat, user_lon], popup=txt['popup_current'], icon=folium.Icon(color='red', icon='user')).add_to(m)
                marker_cluster = MarkerCluster().add_to(m)
                
                if show_toilet:
                    for idx, r in nearby_toilet.iterrows():
                        if row is not None and r['name'] == row['name']:
                            folium.Marker([r['lat'], r['lon']], popup=f"<b>{r['name']}</b>", icon=folium.Icon(color='green', icon='star')).add_to(m)
                        else:
                            folium.Marker([r['lat'], r['lon']], popup=f"<b>{r['name']}</b>", icon=folium.Icon(color='green', icon='info-sign')).add_to(marker_cluster)

                if show_subway:
                    for idx, r in nearby_subway.iterrows():
                        folium.Marker([r['lat'], r['lon']], popup=f"<b>🚇 {r['name']}</b>", tooltip=r['name'], icon=folium.Icon(color='orange', icon='arrow-down', prefix='fa')).add_to(m)

                if show_store:
                    for idx, r in nearby_store.iterrows():
                        folium.Marker([r['lat'], r['lon']], popup=f"<b>🏪 {r['name']}</b>", tooltip=r['name'], icon=folium.Icon(color='purple', icon='shopping-cart', prefix='fa')).add_to(m)
                
                st_folium(m, width="100%", height=500)
        else:
            st.error(txt['error_no_loc'])
            
    except Exception as e:
        if "503" in str(e): st.error("⚠️ Server busy. Try again.")
        else: st.error(f"Error: {e}")

# [NEW] 7. 피드백 섹션 (화면 맨 아래 추가)
st.markdown("---")
st.subheader(txt['fb_title'])

# 폼(Form)을 사용해 제출 버튼을 눌렀을 때만 동작하도록 설정
with st.form("feedback_form"):
    fb_type = st.selectbox(txt['fb_type'], txt['fb_types'])
    fb_msg = st.text_area(txt['fb_msg'])
    submitted = st.form_submit_button(txt['fb_btn'])
    
    if submitted:
        save_feedback(fb_type, fb_msg)
        st.success(txt['fb_success'])
        st.balloons() # 축하 풍선 효과! 🎉
