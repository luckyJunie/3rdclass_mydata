import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(layout="wide", page_title="서울시 공중화장실 찾기 / Seoul Toilet Finder")

# 1. 다국어 설정 (메뉴는 영어/한국어 지원)
lang_dict = {
    'ko': {
        'title': "🚽 서울시 공중화장실 찾기 (상세보기)",
        'desc': "위치를 입력하면 가까운 화장실의 상세 정보를 보여줍니다.",
        'sidebar_header': "🔍 검색 설정",
        'input_label': "현재 위치 입력 (예: 강남역, 시청)",
        'radius_label': "검색 반경 (km)",
        'upload_label': "CSV 파일 업로드 (비상용)",
        'error_file': "⚠️ 데이터 파일을 찾을 수 없습니다. (seoul_toilet.csv)",
        'success_loc': "📍 검색된 위치: {}",
        'result_header': "총 {}개의 화장실 발견",
        'radio_label': "목록에서 화장실을 선택하세요:",
        'warn_no_result': "반경 내 화장실이 없습니다.",
        'popup_current': "현 위치",
        'error_no_loc': "위치를 찾을 수 없습니다.",
        'btn_label': "🇺🇸 Switch to English",
        'detail_title': "📋 상세 정보",
        'col_name': "화장실명",
        'col_addr': "주소",
        'col_time': "운영시간",
        'col_diaper': "기저귀교환대",
        'col_safety': "안전시설(비상벨/CCTV)",
        'col_unisex': "남녀공용여부"
    },
    'en': {
        'title': "🚽 Seoul Public Toilet Finder (Detail View)",
        'desc': "Find nearby toilets with detailed facility information.",
        'sidebar_header': "🔍 Search Settings",
        'input_label': "Enter Location (e.g., Gangnam Station)",
        'radius_label': "Search Radius (km)",
        'upload_label': "Upload CSV File (Backup)",
        'error_file': "⚠️ Data file missing. (seoul_toilet.csv)",
        'success_loc': "📍 Location found: {}",
        'result_header': "Found {} restrooms",
        'radio_label': "Select a restroom from the list:",
        'warn_no_result': "No restrooms found nearby.",
        'popup_current': "Current Location",
        'error_no_loc': "Location not found.",
        'btn_label': "🇰🇷 한국어로 변경",
        'detail_title': "📋 Details",
        'col_name': "Name",
        'col_addr': "Address",
        'col_time': "Hours",
        'col_diaper': "Diaper Station",
        'col_safety': "Safety (Bell/CCTV)",
        'col_unisex': "Unisex"
    }
}

if 'lang' not in st.session_state:
    st.session_state.lang = 'ko'

def toggle_language():
    st.session_state.lang = 'en' if st.session_state.lang == 'ko' else 'ko'

txt = lang_dict[st.session_state.lang]

# 2. 데이터 로드 및 전처리 (상세 정보 컬럼 추가)
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, encoding='utf-8')
    except:
        try:
            df = pd.read_csv(file, encoding='cp949')
        except:
            df = pd.read_csv(file, encoding='euc-kr')

    # 필요한 컬럼이 있는지 확인하고 없으면 '정보없음'으로 채움
    # (데이터 파일마다 컬럼 이름이 조금씩 다를 수 있어 유연하게 처리)
    target_cols = {
        '건물명': 'name', 
        '도로명주소': 'addr', 
        '개방시간': 'hours', 
        'x 좌표': 'lon', 
        'y 좌표': 'lat',
        # 상세 정보 컬럼 매핑 (데이터 파일에 실제 존재하는 컬럼명이어야 함)
        # 만약 CSV 파일에 이 컬럼들이 없다면 아래 로직에서 '정보없음' 처리됨
        '남녀공용화장실여부': 'unisex',
        '대변기수(남)': 'men_toilet',
        '대변기수(여)': 'women_toilet',
        '기저귀교환대장소': 'diaper', # 또는 '기저귀교환대유무'
        '비상벨설치여부': 'bell',
        'CCTV설치여부': 'cctv'
    }
    
    # 실제 파일에 있는 컬럼만 가져오기
    existing_cols = [c for c in target_cols.keys() if c in df.columns]
    df = df[existing_cols]
    
    # 컬럼 이름 영문 변수로 변경
    df.rename(columns=target_cols, inplace=True)
    
    # 상세 정보가 없는 경우를 대비해 기본값 채우기
    for col in ['unisex', 'diaper', 'bell', 'cctv']:
        if col not in df.columns:
            df[col] = '-' # 컬럼 자체가 없으면 하이픈 처리
        else:
            df[col] = df[col].fillna('정보없음') # 빈칸이면 정보없음

    # 텍스트 정리
    str_cols = ['name', 'addr', 'hours', 'unisex', 'diaper', 'bell', 'cctv']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('|', '', regex=False)

    # 좌표 필터링
    if 'lat' in df.columns and 'lon' in df.columns:
        df = df[(df['lat'] > 37.4) & (df['lat'] < 37.8)]
        df = df[(df['lon'] > 126.7) & (df['lon'] < 127.3)]

    return df

# 3. 사이드바 UI
with st.sidebar:
    st.button(txt['btn_label'], on_click=toggle_language)
    st.divider()
    st.header(txt['sidebar_header'])
    uploaded_file = st.file_uploader(txt['upload_label'], type=['csv'])
    
    default_val = "서울시청" if st.session_state.lang == 'ko' else "Seoul City Hall"
    user_address = st.text_input(txt['input_label'], default_val)
    search_radius = st.slider(txt['radius_label'], 0.5, 5.0, 1.0)

# 4. 데이터 불러오기
st.title(txt['title'])
st.markdown(txt['desc'])

df = None
if uploaded_file:
    df = load_data(uploaded_file)
else:
    try:
        df = load_data('seoul_toilet.csv')
    except:
        st.warning(txt['error_file'])
        st.stop()

# 5. 메인 로직
if user_address and df is not None:
    geolocator = Nominatim(user_agent="korea_toilet_detail_v1", timeout=10)
    
    try:
        search_query = f"Seoul {user_address}" if "Seoul" not in user_address and "서울" not in user_address else user_address
        location = geolocator.geocode(search_query)
        
        if location:
            user_lat = location.latitude
            user_lon = location.longitude
            st.success(txt['success_loc'].format(location.address))
            
            # 거리 계산
            def calculate_distance(row):
                return geodesic((user_lat, user_lon), (row['lat'], row['lon'])).km

            df['dist'] = df.apply(calculate_distance, axis=1)
            nearby = df[df['dist'] <= search_radius].sort_values(by='dist')
            
            col1, col2 = st.columns([1, 1.5])
            
            with col1:
                st.subheader(txt['result_header'].format(len(nearby)))
                if not nearby.empty:
                    # 라디오 버튼으로 선택
                    selected_name = st.radio(txt['radio_label'], nearby['name'].tolist())
                    row = nearby[nearby['name'] == selected_name].iloc[0]
                    
                    # ------------------------------------------------
                    # ✨ [상세 정보 보여주는 부분] ✨
                    # ------------------------------------------------
                    st.markdown("---")
                    st.markdown(f"### {txt['detail_title']}")
                    st.markdown(f"**🏠 {txt['col_name']}**: {row['name']}")
                    st.markdown(f"**📍 {txt['col_addr']}**: {row['addr']}")
                    st.markdown(f"**⏰ {txt['col_time']}**: {row['hours']}")
                    st.markdown(f"**👫 {txt['col_unisex']}**: {row['unisex']}")
                    
                    # 아이콘으로 가독성 높이기
                    diaper_info = row['diaper'] if row['diaper'] != '-' else "정보없음"
                    st.markdown(f"**👶 {txt['col_diaper']}**: {diaper_info}")
                    
                    safety_info = []
                    if row['bell'] == 'Y' or '설치' in str(row['bell']): safety_info.append("비상벨 🚨")
                    if row['cctv'] == 'Y' or '설치' in str(row['cctv']): safety_info.append("CCTV 📷")
                    
                    if not safety_info:
                        safety_str = "정보없음"
                    else:
                        safety_str = ", ".join(safety_info)
                        
                    st.markdown(f"**🛡️ {txt['col_safety']}**: {safety_str}")
                    
                else:
                    st.warning(txt['warn_no_result'])
                    row = None

            with col2:
                m = folium.Map(location=[user_lat, user_lon], zoom_start=15)
                folium.Marker([user_lat, user_lon], popup=txt['popup_current'], icon=folium.Icon(color='red', icon='user')).add_to(m)
                
                for idx, r in nearby.iterrows():
                    color = 'green' if row is not None and r['name'] == row['name'] else 'blue'
                    
                    # 팝업에도 간단한 정보 표시
                    popup_content = f"""
                    <div style='width:200px'>
                        <b>{r['name']}</b><br>
                        {r['hours']}<br>
                        남녀공용: {r['unisex']}
                    </div>
                    """
                    folium.Marker(
                        [r['lat'], r['lon']], 
                        popup=folium.Popup(popup_content, max_width=300), 
                        tooltip=r['name'], 
                        icon=folium.Icon(color=color, icon='info-sign')
                    ).add_to(m)
                
                st_folium(m, width="100%", height=500)
        else:
            st.error(txt['error_no_loc'])
            
    except Exception as e:
        if "503" in str(e):
             st.error("⚠️ Server busy. Try again.")
        else:
            st.error(f"Error: {e}")
