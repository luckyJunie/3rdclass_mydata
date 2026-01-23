import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster # [추가] 핀을 묶어주는 기능
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(layout="wide", page_title="서울시 공중화장실 찾기")

# 1. 다국어 설정
lang_dict = {
    'ko': {
        'title': "🚽 서울시 공중화장실 찾기 (Pro Ver.)",
        'desc': "위치를 입력하면 스마트한 지도로 화장실을 안내합니다.",
        'sidebar_header': "🔍 검색 설정",
        'input_label': "현재 위치 입력 (예: 강남역, 시청)",
        'radius_label': "검색 반경 (km)",
        'upload_label': "CSV 파일 업로드 (비상용)",
        'error_file': "⚠️ 데이터 파일을 찾을 수 없습니다. (seoul_toilet.csv)",
        'success_loc': "📍 검색된 위치: {}",
        'metric_label': "검색된 화장실", # 변경
        'metric_dist': "가장 가까운 곳", # 추가
        'search_placeholder': "목록에서 이름으로 검색 (예: 공원)",
        'select_label': "화장실 선택 (클릭하여 펼치기)",
        'warn_no_result': "조건에 맞는 화장실이 없습니다.",
        'popup_current': "현 위치",
        'error_no_loc': "위치를 찾을 수 없습니다.",
        'btn_label': "🇺🇸 Switch to English",
        'detail_title': "📋 상세 정보",
        'col_name': "화장실명",
        'col_addr': "주소",
        'col_time': "운영시간",
        'col_diaper': "기저귀교환대",
        'col_safety': "안전시설",
        'col_unisex': "남녀공용"
    },
    'en': {
        'title': "🚽 Seoul Public Toilet Finder (Pro Ver.)",
        'desc': "Smart map guidance for public restrooms.",
        'sidebar_header': "🔍 Search Settings",
        'input_label': "Enter Location (e.g., Gangnam Station)",
        'radius_label': "Search Radius (km)",
        'upload_label': "Upload CSV File (Backup)",
        'error_file': "⚠️ Data file missing. (seoul_toilet.csv)",
        'success_loc': "📍 Location found: {}",
        'metric_label': "Restrooms Found",
        'metric_dist': "Nearest",
        'search_placeholder': "Filter by name (e.g., Park)",
        'select_label': "Select a restroom",
        'warn_no_result': "No restrooms match your search.",
        'popup_current': "Current Location",
        'error_no_loc': "Location not found.",
        'btn_label': "🇰🇷 한국어로 변경",
        'detail_title': "📋 Details",
        'col_name': "Name",
        'col_addr': "Address",
        'col_time': "Hours",
        'col_diaper': "Diaper Station",
        'col_safety': "Safety",
        'col_unisex': "Unisex"
    }
}

if 'lang' not in st.session_state:
    st.session_state.lang = 'ko'

def toggle_language():
    st.session_state.lang = 'en' if st.session_state.lang == 'ko' else 'ko'

txt = lang_dict[st.session_state.lang]

# 2. 데이터 로드
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

# 3. 사이드바
with st.sidebar:
    st.button(txt['btn_label'], on_click=toggle_language)
    st.divider()
    st.header(txt['sidebar_header'])
    uploaded_file = st.file_uploader(txt['upload_label'], type=['csv'])
    
    default_val = "서울시청" if st.session_state.lang == 'ko' else "Seoul City Hall"
    user_address = st.text_input(txt['input_label'], default_val)
    search_radius = st.slider(txt['radius_label'], 0.5, 5.0, 1.0)

# 4. 메인 화면
st.title(txt['title'])
st.markdown(txt['desc'])

df = None
if uploaded_file: df = load_data(uploaded_file)
else:
    try: df = load_data('seoul_toilet.csv')
    except: st.warning(txt['error_file']); st.stop()

if user_address and df is not None:
    geolocator = Nominatim(user_agent="korea_toilet_pro_v3", timeout=10)
    
    try:
        search_query = f"Seoul {user_address}" if "Seoul" not in user_address and "서울" not in user_address else user_address
        location = geolocator.geocode(search_query)
        
        if location:
            user_lat = location.latitude
            user_lon = location.longitude
            st.success(txt['success_loc'].format(location.address))
            
            def calculate_distance(row):
                return geodesic((user_lat, user_lon), (row['lat'], row['lon'])).km

            df['dist'] = df.apply(calculate_distance, axis=1)
            nearby = df[df['dist'] <= search_radius].sort_values(by='dist')
            
            # [UI 업그레이드 1] 대시보드형 숫자 표시 (Metric)
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.metric(label=txt['metric_label'], value=f"{len(nearby)} Places")
            with m_col2:
                if not nearby.empty:
                    nearest_dist = nearby.iloc[0]['dist']
                    st.metric(label=txt['metric_dist'], value=f"{nearest_dist:.1f} km")

            st.markdown("---")

            col1, col2 = st.columns([1, 1.5])
            
            # -----------------------------------------------------
            # 왼쪽 목록 영역
            # -----------------------------------------------------
            with col1:
                if not nearby.empty:
                    search_keyword = st.text_input("🔍 " + txt['search_placeholder'])
                    
                    if search_keyword:
                        nearby_filtered = nearby[nearby['name'].str.contains(search_keyword)]
                    else:
                        nearby_filtered = nearby

                    if not nearby_filtered.empty:
                        selected_name = st.selectbox(txt['select_label'], nearby_filtered['name'].tolist())
                        row = nearby_filtered[nearby_filtered['name'] == selected_name].iloc[0]
                        
                        # 상세 정보 카드
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
                        
                        if safety_icons:
                            st.success(f"**Facility:** {safety_icons}")
                            
                        with st.expander(txt['detail_title']):
                            st.write(f"- {txt['col_diaper']}: {row['diaper']}")
                            st.write(f"- {txt['col_safety']}: 비상벨({row['bell']}), CCTV({row['cctv']})")
                            st.write(f"- {txt['col_unisex']}: {row['unisex']}")
                            
                    else:
                        st.warning(txt['warn_no_result'])
                        row = None
                else:
                    st.warning(txt['warn_no_result'])
                    row = None

            # -----------------------------------------------------
            # 오른쪽 지도 영역 (대폭 업그레이드!)
            # -----------------------------------------------------
            with col2:
                # [UI 업그레이드 2] 모던한 지도 스타일 (CartoDB positron)
                m = folium.Map(location=[user_lat, user_lon], zoom_start=15, tiles='CartoDB positron')
                
                # 내 위치 (빨간색)
                folium.Marker(
                    [user_lat, user_lon], 
                    popup=txt['popup_current'], 
                    icon=folium.Icon(color='red', icon='user')
                ).add_to(m)
                
                # [UI 업그레이드 3] 마커 클러스터링 (핀 묶기 기능)
                marker_cluster = MarkerCluster().add_to(m)
                
                for idx, r in nearby.iterrows():
                    # 선택된 화장실은 클러스터 밖에 따로 표시 (잘 보이게)
                    if row is not None and r['name'] == row['name']:
                        folium.Marker(
                            [r['lat'], r['lon']], 
                            popup=f"<b>{r['name']}</b>", 
                            tooltip=r['name'], 
                            icon=folium.Icon(color='green', icon='star') # 초록색 별
                        ).add_to(m) # 클러스터가 아니라 지도에 직접 추가
                    else:
                        # 선택 안 된 화장실들은 클러스터로 묶기
                        folium.Marker(
                            [r['lat'], r['lon']], 
                            popup=f"<b>{r['name']}</b>", 
                            tooltip=r['name'], 
                            icon=folium.Icon(color='blue', icon='info-sign')
                        ).add_to(marker_cluster) # 클러스터에 추가
                
                st_folium(m, width="100%", height=500)
        else:
            st.error(txt['error_no_loc'])
            
    except Exception as e:
        if "503" in str(e): st.error("⚠️ Server busy. Try again.")
        else: st.error(f"Error: {e}")
