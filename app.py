import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

st.set_page_config(layout="wide", page_title="서울시 공중화장실 찾기")

# 1. 다국어 설정 (검색 관련 멘트 추가)
lang_dict = {
    'ko': {
        'title': "🚽 서울시 공중화장실 찾기 (스마트 검색)",
        'desc': "위치를 입력하고 목록에서 원하는 화장실을 검색해보세요.",
        'sidebar_header': "🔍 검색 설정",
        'input_label': "현재 위치 입력 (예: 강남역, 시청)",
        'radius_label': "검색 반경 (km)",
        'upload_label': "CSV 파일 업로드 (비상용)",
        'error_file': "⚠️ 데이터 파일을 찾을 수 없습니다. (seoul_toilet.csv)",
        'success_loc': "📍 검색된 위치: {}",
        'result_header': "총 {}개의 화장실 발견",
        'search_placeholder': "목록에서 이름으로 검색 (예: 공원)", # 추가됨
        'select_label': "화장실 선택 (클릭하여 펼치기)", # 변경됨
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
        'title': "🚽 Seoul Public Toilet Finder (Smart Search)",
        'desc': "Enter location and search for specific toilets in the list.",
        'sidebar_header': "🔍 Search Settings",
        'input_label': "Enter Location (e.g., Gangnam Station)",
        'radius_label': "Search Radius (km)",
        'upload_label': "Upload CSV File (Backup)",
        'error_file': "⚠️ Data file missing. (seoul_toilet.csv)",
        'success_loc': "📍 Location found: {}",
        'result_header': "Found {} restrooms",
        'search_placeholder': "Filter by name (e.g., Park)", # 추가됨
        'select_label': "Select a restroom", # 변경됨
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
    geolocator = Nominatim(user_agent="korea_toilet_smart_search_v2", timeout=10)
    
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
            
            # ----------------------------------------------------------------
            # ✨ 여기가 핵심! UI 개선 부분 ✨
            # ----------------------------------------------------------------
            col1, col2 = st.columns([1, 1.5])
            
            with col1:
                st.subheader(txt['result_header'].format(len(nearby)))
                
                if not nearby.empty:
                    # [1] 검색 필터 (텍스트 입력창)
                    search_keyword = st.text_input("🔍 " + txt['search_placeholder'])
                    
                    # 사용자가 검색어를 입력하면 목록을 필터링함
                    if search_keyword:
                        nearby_filtered = nearby[nearby['name'].str.contains(search_keyword)]
                    else:
                        nearby_filtered = nearby

                    # [2] 검색 결과가 있는지 확인
                    if not nearby_filtered.empty:
                        # [3] 세련된 드롭다운 메뉴 (Selectbox)
                        selected_name = st.selectbox(
                            txt['select_label'], 
                            nearby_filtered['name'].tolist()
                        )
                        
                        row = nearby_filtered[nearby_filtered['name'] == selected_name].iloc[0]
                        
                        # [4] 상세 정보 표시 (카드 형태 디자인)
                        st.markdown("---")
                        st.info(f"**🏠 {row['name']}**") # 이름 강조
                        
                        st.write(f"**📍 {txt['col_addr']}**")
                        st.caption(f"{row['addr']}")
                        
                        st.write(f"**⏰ {txt['col_time']}**")
                        st.caption(f"{row['hours']}")
                        
                        # 아이콘 정보 한줄 요약
                        safety_icons = ""
                        if row['diaper'] != '-' and row['diaper'] != '정보없음': safety_icons += "👶 "
                        if row['bell'] == 'Y' or '설치' in str(row['bell']): safety_icons += "🚨 "
                        if row['cctv'] == 'Y' or '설치' in str(row['cctv']): safety_icons += "📷 "
                        if row['unisex'] == 'Y': safety_icons += "👫"
                        
                        if safety_icons:
                            st.success(f"**Facility:** {safety_icons}")
                            
                        # 남은 상세 정보
                        with st.expander(txt['detail_title'] + " (Click)"):
                            st.write(f"- {txt['col_diaper']}: {row['diaper']}")
                            st.write(f"- {txt['col_safety']}: 비상벨({row['bell']}), CCTV({row['cctv']})")
                            st.write(f"- {txt['col_unisex']}: {row['unisex']}")
                            
                    else:
                        st.warning(txt['warn_no_result'])
                        row = None
                else:
                    st.warning(txt['warn_no_result'])
                    row = None

            with col2:
                m = folium.Map(location=[user_lat, user_lon], zoom_start=15)
                folium.Marker([user_lat, user_lon], popup=txt['popup_current'], icon=folium.Icon(color='red', icon='user')).add_to(m)
                
                # 지도에는 필터링된 결과만 보여줄지, 전체를 보여줄지 선택 가능
                # 여기서는 전체를 보여주되, 선택된 것만 초록색으로 표시
                for idx, r in nearby.iterrows():
                    color = 'green' if row is not None and r['name'] == row['name'] else 'blue'
                    
                    # 선택된 마커는 좀 더 크게 보이게 하거나 아이콘 변경
                    icon_type = 'star' if row is not None and r['name'] == row['name'] else 'info-sign'
                    
                    popup_content = f"<div style='width:150px'><b>{r['name']}</b><br>{r['hours']}</div>"
                    
                    folium.Marker(
                        [r['lat'], r['lon']], 
                        popup=folium.Popup(popup_content, max_width=300), 
                        tooltip=r['name'], 
                        icon=folium.Icon(color=color, icon=icon_type)
                    ).add_to(m)
                
                st_folium(m, width="100%", height=500)
        else:
            st.error(txt['error_no_loc'])
            
    except Exception as e:
        if "503" in str(e): st.error("⚠️ Server busy. Try again.")
        else: st.error(f"Error: {e}")
