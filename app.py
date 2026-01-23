import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# 1. 페이지 설정 (가장 먼저 와야 함)
st.set_page_config(layout="wide", page_title="서울시 공중화장실 찾기 / Seoul Toilet Finder")

# ==========================================
# 2. 다국어 사전 (Dictionary) 설정
# ==========================================
# 화면에 표시될 모든 텍스트를 이곳에 정리합니다.
lang_dict = {
    'ko': {
        'title': "🚽 서울시 내 주변 공중화장실 찾기",
        'desc': "본인의 위치(주소/건물명)를 입력하면 가장 가까운 공중화장실을 찾아줍니다.",
        'sidebar_header': "🔍 검색 설정",
        'input_label': "현재 위치 입력 (예: 강남역, 세종대로 175)",
        'radius_label': "검색 반경 (km)",
        'error_csv': "CSV 파일이 없습니다.",
        'success_loc': "📍 검색된 위치: {}",
        'result_header': "총 {}개의 화장실 발견",
        'radio_label': "지도에서 보고 싶은 화장실을 선택하세요:",
        'info_name': "🏠 건물명",
        'info_addr': "📍 주소",
        'info_time': "⏰ 개방시간",
        'info_dist': "🚶 거리",
        'warn_no_result': "설정된 반경 내에 화장실이 없습니다.",
        'popup_current': "현 위치",
        'error_no_loc': "위치를 찾을 수 없습니다. 주소를 다시 확인해주세요.",
        'btn_label': "🇺🇸 Switch to English"
    },
    'en': {
        'title': "🚽 Public Restrooms in Seoul",
        'desc': "Enter your location to find the nearest public restrooms.",
        'sidebar_header': "🔍 Search Settings",
        'input_label': "Enter Location (e.g., Gangnam Station, City Hall)",
        'radius_label': "Search Radius (km)",
        'error_csv': "CSV file not found.",
        'success_loc': "📍 Location found: {}",
        'result_header': "Found {} restrooms",
        'radio_label': "Select a restroom to view on map:",
        'info_name': "🏠 Name",
        'info_addr': "📍 Address",
        'info_time': "⏰ Hours",
        'info_dist': "🚶 Distance",
        'warn_no_result': "No restrooms found within the radius.",
        'popup_current': "Current Location",
        'error_no_loc': "Location not found. Please check the address.",
        'btn_label': "🇰🇷 한국어로 변경"
    }
}

# ==========================================
# 3. 언어 상태 관리 (Session State)
# ==========================================
if 'lang' not in st.session_state:
    st.session_state.lang = 'ko'  # 기본값 한국어

def toggle_language():
    if st.session_state.lang == 'ko':
        st.session_state.lang = 'en'
    else:
        st.session_state.lang = 'ko'

# 현재 언어에 맞는 텍스트 가져오기
txt = lang_dict[st.session_state.lang]

# ==========================================
# 4. 사이드바 (언어 변경 버튼 & 입력창)
# ==========================================
with st.sidebar:
    # 언어 변경 버튼 (맨 위에 배치)
    st.button(txt['btn_label'], on_click=toggle_language)
    st.divider() # 구분선
    
    st.header(txt['sidebar_header'])
    # 영어일 때 기본값을 'Seoul City Hall'로 변경하면 더 자연스러움
    default_value = "서울시청" if st.session_state.lang == 'ko' else "Seoul City Hall"
    user_address = st.text_input(txt['input_label'], default_value)
    search_radius = st.slider(txt['radius_label'], 0.5, 5.0, 1.0)

# ==========================================
# 5. 메인 로직
# ==========================================
st.title(txt['title'])
st.markdown(txt['desc'])

@st.cache_data
def load_data():
    file_path = '서울시 공중화장실 위치정보.csv'
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='cp949')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='euc-kr')

    df = df[['건물명', '도로명주소', '개방시간', 'x 좌표', 'y 좌표', '유형', '비고']]
    df.rename(columns={'x 좌표': 'lon', 'y 좌표': 'lat'}, inplace=True)

    cols_to_clean = ['건물명', '도로명주소', '개방시간', '유형', '비고']
    for col in cols_to_clean:
        df[col] = df[col].astype(str).str.replace('|', '', regex=False)

    df = df[(df['lat'] > 37.4) & (df['lat'] < 37.8)]
    df = df[(df['lon'] > 126.7) & (df['lon'] < 127.3)]
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error(txt['error_csv'])
    st.stop()

if user_address:
    geolocator = Nominatim(user_agent="seoul_toilet_finder_v2") # user_agent 이름 변경 권장
    try:
        # 영어 검색일 경우 "Seoul"을 앞에 붙여주면 정확도 향상
        search_query = f"Seoul {user_address}" if "Seoul" not in user_address and "서울" not in user_address else user_address
        
        location = geolocator.geocode(search_query)
        if location:
            user_lat = location.latitude
            user_lon = location.longitude
            st.success(txt['success_loc'].format(location.address))
            
            def calculate_distance(row):
                return geodesic((user_lat, user_lon), (row['lat'], row['lon'])).km

            df['거리(km)'] = df.apply(calculate_distance, axis=1)
            nearby_toilets = df[df['거리(km)'] <= search_radius].sort_values(by='거리(km)')
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader(txt['result_header'].format(len(nearby_toilets)))
                if not nearby_toilets.empty:
                    selected_toilet_name = st.radio(
                        txt['radio_label'],
                        nearby_toilets['건물명'].tolist()
                    )
                    selected_row = nearby_toilets[nearby_toilets['건물명'] == selected_toilet_name].iloc[0]
                    
                    # 정보 표시 (라벨 다국어 적용)
                    st.info(
                        f"**{txt['info_name']}:** {selected_row['건물명']}\n\n"
                        f"{txt['info_addr']}: {selected_row['도로명주소']}\n\n"
                        f"{txt['info_time']}: {selected_row['개방시간']}\n\n"
                        f"{txt['info_dist']}: {selected_row['거리(km)']:.2f} km"
                    )
                else:
                    st.warning(txt['warn_no_result'])
                    selected_row = None

            with col2:
                m = folium.Map(location=[user_lat, user_lon], zoom_start=15)
                folium.Marker([user_lat, user_lon], popup=txt['popup_current'], icon=folium.Icon(color='red', icon='user')).add_to(m)
                for idx, row in nearby_toilets.iterrows():
                    icon_color = 'green' if selected_row is not None and row['건물명'] == selected_row['건물명'] else 'blue'
                    folium.Marker([row['lat'], row['lon']], popup=row['건물명'], tooltip=row['건물명'], icon=folium.Icon(color=icon_color, icon='info-sign')).add_to(m)
                st_folium(m, width="100%", height=500)
        else:
            st.error(txt['error_no_loc'])
    except Exception as e:
        st.error(f"Error: {e}")
