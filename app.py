import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# ---------------------------------------------------------
# 1. 페이지 설정 및 제목
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="서울시 공중화장실 찾기")
st.title("🚽 서울시 내 주변 공중화장실 찾기")
st.markdown("본인의 위치(주소/건물명)를 입력하면 가장 가까운 공중화장실을 찾아줍니다.")

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리 (캐싱을 통해 속도 향상)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    file_path = '서울시 공중화장실 위치정보.csv'
    
    # 인코딩 문제 해결을 위한 예외 처리
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='cp949')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='euc-kr')

    # 필요한 컬럼만 선택 및 이름 변경 (가독성)
    df = df[['건물명', '도로명주소', '개방시간', 'x 좌표', 'y 좌표', '유형', '비고']]
    df.rename(columns={'x 좌표': 'lon', 'y 좌표': 'lat'}, inplace=True)

    # 데이터 정제 1: 문자열 끝의 불필요한 '|' 제거
    cols_to_clean = ['건물명', '도로명주소', '개방시간', '유형', '비고']
    for col in cols_to_clean:
        df[col] = df[col].astype(str).str.replace('|', '', regex=False)

    # 데이터 정제 2: 좌표 이상치 제거 (서울 범위를 벗어난 데이터 제거)
    # 서울 대략적 위도: 37.4 ~ 37.7, 경도: 126.7 ~ 127.2
    df = df[(df['lat'] > 37.4) & (df['lat'] < 37.8)]
    df = df[(df['lon'] > 126.7) & (df['lon'] < 127.3)]

    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("CSV 파일이 없습니다. '서울시 공중화장실 위치정보.csv' 파일을 같은 폴더에 넣어주세요.")
    st.stop()

# ---------------------------------------------------------
# 3. 사이드바: 사용자 설정
# ---------------------------------------------------------
st.sidebar.header("🔍 검색 설정")
user_address = st.sidebar.text_input("현재 위치 입력 (예: 강남역, 세종대로 175)", "서울시청")
search_radius = st.sidebar.slider("검색 반경 (km)", 0.5, 5.0, 1.0)

# ---------------------------------------------------------
# 4. 메인 로직: 위치 검색 및 거리 계산
# ---------------------------------------------------------
if user_address:
    # 4-1. 주소를 좌표로 변환 (Geocoding)
    geolocator = Nominatim(user_agent="seoul_toilet_finder")
    
    try:
        # 정확도를 위해 검색어 앞에 '서울'을 붙임
        location = geolocator.geocode(f"서울 {user_address}")
        
        if location:
            user_lat = location.latitude
            user_lon = location.longitude
            
            st.success(f"📍 검색된 위치: {location.address}")
            
            # 4-2. 거리 계산 함수
            def calculate_distance(row):
                toilet_loc = (row['lat'], row['lon'])
                user_loc = (user_lat, user_lon)
                return geodesic(user_loc, toilet_loc).km

            # 거리 계산 적용
            df['거리(km)'] = df.apply(calculate_distance, axis=1)
            
            # 반경 내 화장실 필터링
            nearby_toilets = df[df['거리(km)'] <= search_radius].sort_values(by='거리(km)')
            
            # ---------------------------------------------------------
            # 5. 결과 목록 및 지도 시각화
            # ---------------------------------------------------------
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader(f"총 {len(nearby_toilets)}개의 화장실 발견")
                
                if not nearby_toilets.empty:
                    # 목록에서 선택 기능
                    selected_toilet_name = st.radio(
                        "지도에서 보고 싶은 화장실을 선택하세요:",
                        nearby_toilets['건물명'].tolist()
                    )
                    
                    # 선택된 화장실 정보 가져오기
                    selected_row = nearby_toilets[nearby_toilets['건물명'] == selected_toilet_name].iloc[0]
                    
                    st.info(f"🏠 **{selected_row['건물명']}**\n\n"
                            f"📍 {selected_row['도로명주소']}\n\n"
                            f"⏰ {selected_row['개방시간']}\n\n"
                            f"🚶 거리: {selected_row['거리(km)']:.2f} km")
                else:
                    st.warning("설정된 반경 내에 화장실이 없습니다.")
                    selected_row = None

            with col2:
                # 지도 생성 (초기 중심: 사용자 위치)
                m = folium.Map(location=[user_lat, user_lon], zoom_start=15)
                
                # 사용자 위치 마커 (빨간색)
                folium.Marker(
                    [user_lat, user_lon],
                    popup="현 위치",
                    tooltip="현 위치",
                    icon=folium.Icon(color='red', icon='user')
                ).add_to(m)
                
                # 주변 화장실 마커 (파란색)
                for idx, row in nearby_toilets.iterrows():
                    # 선택된 화장실은 초록색으로 강조
                    if selected_row is not None and row['건물명'] == selected_row['건물명']:
                        icon_color = 'green'
                        icon_type = 'star'
                    else:
                        icon_color = 'blue'
                        icon_type = 'info-sign'

                    folium.Marker(
                        [row['lat'], row['lon']],
                        popup=f"<b>{row['건물명']}</b><br>{row['개방시간']}",
                        tooltip=row['건물명'],
                        icon=folium.Icon(color=icon_color, icon=icon_type)
                    ).add_to(m)
                
                # Streamlit에 지도 출력
                st_folium(m, width="100%", height=500)

        else:
            st.error("위치를 찾을 수 없습니다. 정확한 주소나 건물명을 입력해주세요.")

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.write("일시적인 네트워크 오류일 수 있습니다. 잠시 후 다시 시도해주세요.")
