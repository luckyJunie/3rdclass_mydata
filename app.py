import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(layout="wide", page_title="서울시 공중화장실 찾기")
st.title("🚽 서울시 내 주변 공중화장실 찾기")
st.markdown("본인의 위치(주소/건물명)를 입력하면 가장 가까운 공중화장실을 찾아줍니다.")

@st.cache_data
def load_data():
    file_path = '서울시 공중화장실 위치정보.csv'
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
    st.error("CSV 파일이 없습니다.")
    st.stop()

st.sidebar.header("🔍 검색 설정")
user_address = st.sidebar.text_input("현재 위치 입력 (예: 강남역, 세종대로 175)", "서울시청")
search_radius = st.sidebar.slider("검색 반경 (km)", 0.5, 5.0, 1.0)

if user_address:
    geolocator = Nominatim(user_agent="seoul_toilet_finder")
    try:
        location = geolocator.geocode(f"서울 {user_address}")
        if location:
            user_lat = location.latitude
            user_lon = location.longitude
            st.success(f"📍 검색된 위치: {location.address}")
            
            def calculate_distance(row):
                return geodesic((user_lat, user_lon), (row['lat'], row['lon'])).km

            df['거리(km)'] = df.apply(calculate_distance, axis=1)
            nearby_toilets = df[df['거리(km)'] <= search_radius].sort_values(by='거리(km)')
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader(f"총 {len(nearby_toilets)}개의 화장실 발견")
                if not nearby_toilets.empty:
                    selected_toilet_name = st.radio(
                        "지도에서 보고 싶은 화장실을 선택하세요:",
                        nearby_toilets['건물명'].tolist()
                    )
                    selected_row = nearby_toilets[nearby_toilets['건물명'] == selected_toilet_name].iloc[0]
                    st.info(f"🏠 **{selected_row['건물명']}**\n\n📍 {selected_row['도로명주소']}\n\n⏰ {selected_row['개방시간']}\n\n🚶 거리: {selected_row['거리(km)']:.2f} km")
                else:
                    st.warning("설정된 반경 내에 화장실이 없습니다.")
                    selected_row = None

            with col2:
                m = folium.Map(location=[user_lat, user_lon], zoom_start=15)
                folium.Marker([user_lat, user_lon], popup="현 위치", icon=folium.Icon(color='red', icon='user')).add_to(m)
                for idx, row in nearby_toilets.iterrows():
                    icon_color = 'green' if selected_row is not None and row['건물명'] == selected_row['건물명'] else 'blue'
                    folium.Marker([row['lat'], row['lon']], popup=row['건물명'], tooltip=row['건물명'], icon=folium.Icon(color=icon_color, icon='info-sign')).add_to(m)
                st_folium(m, width="100%", height=500)
        else:
            st.error("위치를 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"오류: {e}")
