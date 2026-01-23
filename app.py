import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# 1. 페이지 기본 설정
st.set_page_config(layout="wide", page_title="서울시 공중화장실 찾기 / Seoul Toilet Finder")

# 2. 다국어 사전 (한국어/영어)
lang_dict = {
    'ko': {
        'title': "🚽 서울시 내 주변 공중화장실 찾기",
        'desc': "본인의 위치(주소/건물명)를 입력하면 가장 가까운 공중화장실을 찾아줍니다.",
        'sidebar_header': "🔍 검색 설정",
        'input_label': "현재 위치 입력 (예: 강남역, 시청)",
        'radius_label': "검색 반경 (km)",
        'upload_label': "CSV 파일 업로드 (파일을 못 찾을 경우)",
        'error_file': "⚠️ 'seoul_toilet.csv' 파일을 찾을 수 없습니다. 깃허브에 파일을 올렸는지 확인하거나, 아래 박스에 파일을 직접 드래그하세요.",
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
        'input_label': "Enter Location (e.g., Gangnam Station)",
        'radius_label': "Search Radius (km)",
        'upload_label': "Upload CSV File (If file is missing)",
        'error_file': "⚠️ Could not find 'seoul_toilet.csv'. Please check if it's uploaded to GitHub or upload it here manually.",
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

# 3. 언어 상태 관리
if 'lang' not in st.session_state:
    st.session_state.lang = 'ko'

def toggle_language():
    st.session_state.lang = 'en' if st.session_state.lang == 'ko' else 'ko'

txt = lang_dict[st.session_state.lang]

# 4. 사이드바 구성
with st.sidebar:
    st.button(txt['btn_label'], on_click=toggle_language)
    st.divider()
    st.header(txt['sidebar_header'])
    
    # 파일 업로더 (비상용)
    uploaded_file = st.file_uploader(txt['upload_label'], type=['csv'])
    
    default_value = "서울시청" if st.session_state.lang == 'ko' else "Seoul City Hall"
    user_address = st.text_input(txt['input_label'], default_value)
    search_radius = st.slider(txt['radius_label'], 0.5, 5.0, 1.0)

# 5. 데이터 로드 함수
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file, encoding='cp949')
        except UnicodeDecodeError:
            df = pd.read_csv(file, encoding='euc-kr')

    # 필요한 컬럼만 선택 및 이름 변경
    df = df[['건물명', '도로명주소', '개방시간', 'x 좌표', 'y 좌표', '유형', '비고']]
    df.rename(columns={'x 좌표': 'lon', 'y 좌표': 'lat'}, inplace=True)

    # 전처리 (파이프 기호 제거 등)
    cols_to_clean = ['건물명', '도로명주소', '개방시간', '유형', '비고']
    for col in cols_to_clean:
        df[col] = df[col].astype(str).str.replace('|', '', regex=False)

    # 서울 좌표 범위로 필터링 (이상한 좌표 제거)
    df = df[(df['lat'] > 37.4) & (df['lat'] < 37.8)]
    df = df[(df['lon'] > 126.7) & (df['lon'] < 127.3)]
    return df

# 6. 메인 로직 실행
st.title(txt['title'])
st.markdown(txt['desc'])

# 파일 읽기 시도
df = None
default_path = 'seoul_toilet.csv'

if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    try:
        df = load_data(default_path)
    except FileNotFoundError:
        st.warning(txt['error_file'])
        st.stop()
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

# 7. 위치 검색 및 지도 표시
if user_address and df is not None:
    # [수정된 부분] user_agent를 아주 독특하게 변경하고, timeout을 추가했습니다.
    # 이렇게 하면 서버가 '새로운 사용자구나' 하고 받아줄 확률이 높아집니다.
    geolocator = Nominatim(user_agent="korea_toilet_map_project_v1_unique", timeout=10)
    
    try:
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
                folium.Marker(
                    [user_lat, user_lon], 
                    popup=txt['popup_current'], 
                    icon=folium.Icon(color='red', icon='user')
                ).add_to(m)
                
                for idx, row in nearby_toilets.iterrows():
                    icon_color = 'green' if selected_row is not None and row['건물명'] == selected_row['건물명'] else 'blue'
                    folium.Marker(
                        [row['lat'], row['lon']], 
                        popup=f"<b>{row['건물명']}</b><br>{row['개방시간']}", 
                        tooltip=row['건물명'], 
                        icon=folium.Icon(color=icon_color, icon='info-sign')
                    ).add_to(m)
                
                st_folium(m, width="100%", height=500)
        else:
            st.error(txt['error_no_loc'])
            
    except Exception as e:
        # 503 에러가 또 나면 조금 더 친절하게 알려줍니다.
        if "503" in str(e):
            st.error("⚠️ 지도 서비스가 일시적으로 바쁩니다. 5초 뒤에 다시 시도해보거나, 주소를 조금 더 정확하게 입력해주세요.")
        else:
            st.error(f"An error occurred: {e}")
