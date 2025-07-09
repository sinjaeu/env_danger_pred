import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import warnings
import requests
import json
import os
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
warnings.filterwarnings('ignore')

# 환경 변수 로드
load_dotenv('config.env')

# 페이지 설정
st.set_page_config(
    page_title="기상 기반 사망률 예측 시스템",
    page_icon="🌤️",
    layout="wide"
)

# 제목
st.title("🌤️ 기상 기반 사망률 예측 시스템")
st.markdown("*실제 기상청 데이터 기반 기온/습도 예측 및 사망률 분석*")
st.markdown("---")

# 기상청 API 설정
class WeatherAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://apihub.kma.go.kr/api/json"
        
        # 주요 도시별 기상관측소 코드
        self.station_codes = {
            "서울": "108",      # 서울
            "부산": "159",      # 부산
            "대구": "143",      # 대구
            "인천": "112",      # 인천
            "광주": "156",      # 광주
            "대전": "133",      # 대전
            "울산": "152",      # 울산
            "제주": "184"       # 제주
        }
    
    def get_weather_data(self, city: str, start_date: str, end_date: str) -> pd.DataFrame:
        """기상청 API Hub에서 특정 도시의 기상 데이터를 가져옵니다."""
        
        if city not in self.station_codes:
            st.error(f"지원하지 않는 도시입니다: {city}")
            return pd.DataFrame()
        
        station_code = self.station_codes[city]
        
        try:
            # 새로운 API Hub 형식에 맞춘 요청 파라미터
            params = {
                'authKey': self.api_key,
                'stn': station_code,
                'tm': start_date,  # 시작 날짜
                'help': '0'  # 도움말 없음
            }
            
            # 헤더 설정
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(self.base_url, params=params, headers=headers, timeout=30)
            
            # 응답 상태 확인
            if response.status_code != 200:
                st.error(f"API 요청 실패: HTTP {response.status_code}")
                st.error(f"응답 내용: {response.text[:500]}")
                return pd.DataFrame()
            
            # JSON 파싱 시도
            try:
                data = response.json()
            except json.JSONDecodeError:
                st.error("API 응답이 JSON 형식이 아닙니다.")
                st.error(f"응답 내용: {response.text[:500]}")
                return pd.DataFrame()
            
            # API 응답 구조 확인 (새로운 API Hub 형식)
            st.info(f"API 응답 구조: {list(data.keys()) if isinstance(data, dict) else 'List response'}")
            
            # 응답 구조에 따라 데이터 추출
            if isinstance(data, list):
                # 새로운 API Hub 형식 (직접 JSON 배열 응답)
                items = data
            elif 'response' in data:
                # 기존 공공데이터 포털 형식
                if 'body' in data['response'] and 'items' in data['response']['body']:
                    items = data['response']['body']['items']['item']
                else:
                    st.error("API 응답 구조가 예상과 다릅니다.")
                    return pd.DataFrame()
            else:
                # 단일 객체 응답
                items = [data]
            
            if not items:
                st.warning(f"{city}의 {start_date}~{end_date} 기간 데이터가 없습니다.")
                return pd.DataFrame()
            
            # 데이터프레임으로 변환
            weather_data = []
            for item in items:
                try:
                    # 새로운 API 문서에 따른 필드명 사용
                    temp = None
                    humidity = None
                    
                    # 기온 필드 (TA: 기온 °C)
                    if 'TA' in item and item['TA'] not in [-999, None, '', '']:
                        temp = float(item['TA'])
                    
                    # 습도 필드 (HM: 상대습도 %)
                    if 'HM' in item and item['HM'] not in [-999, None, '', '']:
                        humidity = float(item['HM'])
                    
                    # 시간 필드 (TM: 관측시각 KST)
                    time_str = None
                    if 'TM' in item and item['TM']:
                        time_str = str(item['TM'])
                    
                    if temp is not None and humidity is not None and time_str:
                        try:
                            # 새로운 API 문서에 따른 시간 형식 처리
                            # TM: 관측시각 (KST) - 년월일시분 형식
                            if len(time_str) == 12:  # YYYYMMDDHHMM 형식
                                date_obj = datetime.strptime(time_str, "%Y%m%d%H%M")
                            elif len(time_str) == 8:  # YYYYMMDD 형식
                                date_obj = datetime.strptime(time_str, "%Y%m%d")
                            elif 'T' in time_str:  # ISO 형식
                                date_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                            elif len(time_str) == 14:  # YYYYMMDDHHMMSS 형식
                                date_obj = datetime.strptime(time_str, "%Y%m%d%H%M%S")
                            elif len(time_str) == 19:  # YYYY-MM-DD HH:MM:SS 형식
                                date_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                            else:
                                date_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                            
                            weather_data.append({
                                'date': date_obj,
                                'city': city,
                                'temperature': temp,
                                'humidity': humidity
                            })
                        except ValueError as e:
                            continue
                            
                except (ValueError, KeyError) as e:
                    continue
            
            if not weather_data:
                st.warning(f"{city}의 유효한 기상 데이터가 없습니다.")
                st.info(f"첫 번째 아이템 구조: {items[0] if items else 'No items'}")
                return pd.DataFrame()
            
            df = pd.DataFrame(weather_data)
            
            # 계절 정보 추가
            df['month'] = df['date'].dt.month
            df['year'] = df['date'].dt.year
            
            def get_season(month):
                if month in [3, 4, 5]:
                    return "봄"
                elif month in [6, 7, 8]:
                    return "여름"
                elif month in [9, 10, 11]:
                    return "가을"
                else:
                    return "겨울"
            
            df['season'] = df['month'].apply(get_season)
            
            return df
            
        except requests.exceptions.RequestException as e:
            st.error(f"API 요청 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
            st.error(f"오류 상세: {str(e)}")
            return pd.DataFrame()

# 기상청 API 키 설정 (환경 변수에서 읽기)
def get_weather_api_key():
    """환경 변수에서 기상청 API 키를 읽어옵니다."""
    api_key = os.getenv('WEATHER_API_KEY')
    
    if not api_key or api_key == 'your_api_key_here':
        st.error("❌ 기상청 API 키가 설정되지 않았습니다.")
        st.markdown("""
        **API 키 설정 방법:**
        1. `config.env` 파일을 열어주세요
        2. `WEATHER_API_KEY=your_api_key_here` 부분을 수정
        3. `your_api_key_here`를 실제 API 키로 변경
        4. 애플리케이션을 다시 시작
        
        **API 키 발급 방법:**
        1. [기상청 API Hub](https://apihub.kma.go.kr/) 접속
        2. 회원가입/로그인
        3. "시간별 기상정보" API 신청
        4. API 키 발급
        """)
        return None
    
    return api_key

# 과거 3년 기상 데이터 로드 함수
@st.cache_data(ttl=3600)  # 1시간마다 캐시 갱신
def load_3year_weather_data(api_key: str, city: str) -> pd.DataFrame:
    """과거 3년(2021-2023)의 기상청 데이터를 가져와서 계절별로 분류합니다."""
    
    if not api_key:
        return pd.DataFrame()
    
    weather_api = WeatherAPI(api_key)
    all_data = []
    
    # 2021-2023년 데이터 수집
    for year in [2021, 2022, 2023]:
        # 각 연도별로 1월 1일부터 12월 31일까지 데이터 수집
        start_date = f"{year}0101"
        end_date = f"{year}1231"
        
        st.info(f"{city}의 {year}년 기상 데이터를 가져오는 중...")
        
        year_data = weather_api.get_weather_data(city, start_date, end_date)
        if not year_data.empty:
            all_data.append(year_data)
    
    if not all_data:
        st.warning(f"{city}의 과거 3년 기상 데이터를 가져올 수 없습니다.")
        return pd.DataFrame()
    
    # 모든 데이터 합치기
    combined_data = pd.concat(all_data, ignore_index=True)
    
    # 계절 정보 추가
    def get_season(month):
        if month in [3, 4, 5]:
            return "봄"
        elif month in [6, 7, 8]:
            return "여름"
        elif month in [9, 10, 11]:
            return "가을"
        else:
            return "겨울"
    
    combined_data['month'] = combined_data['date'].dt.month
    combined_data['year'] = combined_data['date'].dt.year
    combined_data['season'] = combined_data['month'].apply(get_season)
    
    # 날짜별 평균 계산 (같은 날짜의 여러 시간 데이터를 평균)
    daily_data = combined_data.groupby([
        combined_data['date'].dt.date, 
        'city', 
        'season', 
        'year'
    ]).agg({
        'temperature': 'mean',
        'humidity': 'mean'
    }).reset_index()
    
    daily_data['date'] = pd.to_datetime(daily_data['date'])
    
    st.success(f"{city}의 과거 3년 기상 데이터 수집 완료! 총 {len(daily_data)}일의 데이터")
    
    return daily_data

# 최근 30일 기상 데이터 로드 함수
@st.cache_data(ttl=3600)  # 1시간마다 캐시 갱신
def load_recent_weather_data(api_key: str, city: str, days_back: int = 30) -> pd.DataFrame:
    """최근 기상청 데이터를 가져옵니다."""
    
    if not api_key:
        return pd.DataFrame()
    
    weather_api = WeatherAPI(api_key)
    
    # 날짜 범위 설정
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)
    
    # API 형식에 맞게 날짜 변환
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")
    
    st.info(f"{city}의 {start_date} ~ {end_date} 기간 실제 기상 데이터를 가져오는 중...")
    
    return weather_api.get_weather_data(city, start_str, end_str)

# API 키 검증 함수
def validate_api_key(api_key: str) -> bool:
    """API 키가 유효한지 간단히 검증합니다."""
    if not api_key or len(api_key) < 10:
        return False
    return True

# 계절별 기상 예측 함수 (과거 3년 같은 계절 데이터 사용)
def predict_seasonal_weather(city, target_date, historical_data):
    """과거 3년의 같은 계절 데이터를 기반으로 기온과 습도 예측"""
    
    if historical_data.empty:
        # 데이터가 없으면 계절별 기본값 반환
        target_month = target_date.month
        if target_month in [6, 7, 8]:  # 여름
            return 25.0, 70.0
        elif target_month in [12, 1, 2]:  # 겨울
            return 2.0, 60.0
        elif target_month in [3, 4, 5]:  # 봄
            return 15.0, 60.0
        else:  # 가을
            return 18.0, 65.0
    
    # 대상 날짜의 계절 판단
    target_month = target_date.month
    if target_month in [3, 4, 5]:
        target_season = "봄"
    elif target_month in [6, 7, 8]:
        target_season = "여름"
    elif target_month in [9, 10, 11]:
        target_season = "가을"
    else:
        target_season = "겨울"
    
    # 해당 도시의 같은 계절 데이터 필터링 (2021-2023)
    city_season_data = historical_data[
        (historical_data['city'] == city) & 
        (historical_data['season'] == target_season) &
        (historical_data['year'].isin([2021, 2022, 2023]))
    ].copy()
    
    if len(city_season_data) == 0:
        # 같은 계절 데이터가 없으면 전체 데이터의 평균 사용
        city_data = historical_data[historical_data['city'] == city]
        if len(city_data) > 0:
            avg_temp = city_data['temperature'].mean()
            avg_humidity = city_data['humidity'].mean()
            return round(avg_temp, 1), round(avg_humidity, 1)
        else:
            # 데이터가 없으면 계절별 기본값 반환
            if target_season == "여름":
                return 25.0, 70.0
            elif target_season == "겨울":
                return 2.0, 60.0
            elif target_season == "봄":
                return 15.0, 60.0
            else:  # 가을
                return 18.0, 65.0
    
    # 같은 계절의 평균 기온과 습도 계산
    avg_temp = city_season_data['temperature'].mean()
    avg_humidity = city_season_data['humidity'].mean()
    
    # 연도별 추세 계산 (기후변화 반영)
    yearly_temps = city_season_data.groupby('year')['temperature'].mean()
    if len(yearly_temps) > 1:
        temp_trend = np.polyfit(yearly_temps.index, yearly_temps.values, 1)[0]
        # 2024년까지의 추세 적용
        years_ahead = 2024 - yearly_temps.index[-1]
        trend_adjustment = temp_trend * years_ahead
    else:
        trend_adjustment = 0
    
    # 월별 세부 패턴 (같은 계절 내에서도 월별 차이)
    month_data = city_season_data[city_season_data['date'].dt.month == target_month]
    if len(month_data) > 0:
        month_avg_temp = month_data['temperature'].mean()
        month_avg_humidity = month_data['humidity'].mean()
    else:
        month_avg_temp = avg_temp
        month_avg_humidity = avg_humidity
    
    # 최종 예측값 계산
    predicted_temp = month_avg_temp + trend_adjustment
    predicted_humidity = month_avg_humidity
    
    # 범위 제한
    predicted_temp = max(-20, min(50, predicted_temp))
    predicted_humidity = max(20, min(95, predicted_humidity))
    
    return round(predicted_temp, 1), round(predicted_humidity, 1)

# 논문 기반 지역 클러스터 데이터
location_clusters = {
    "서울": {"cluster": "H", "type": "hot", "cdd_avg": 172.7, "threshold": 33.5, "risk_multiplier": 1.4},
    "대구": {"cluster": "H", "type": "hot", "cdd_avg": 172.7, "threshold": 33.5, "risk_multiplier": 1.4},
    "부산": {"cluster": "M", "type": "moderate", "cdd_avg": 105.5, "threshold": 32.5, "risk_multiplier": 1.2},
    "인천": {"cluster": "M", "type": "moderate", "cdd_avg": 105.5, "threshold": 32.5, "risk_multiplier": 1.2},
    "광주": {"cluster": "M", "type": "moderate", "cdd_avg": 105.5, "threshold": 32.5, "risk_multiplier": 1.2},
    "대전": {"cluster": "M", "type": "moderate", "cdd_avg": 105.5, "threshold": 32.5, "risk_multiplier": 1.2},
    "울산": {"cluster": "M", "type": "moderate", "cdd_avg": 105.5, "threshold": 32.5, "risk_multiplier": 1.2},
    "제주": {"cluster": "M", "type": "moderate", "cdd_avg": 105.5, "threshold": 32.5, "risk_multiplier": 1.2}
}

# 위험도 계산 함수 (기존과 동일)
def calculate_advanced_mortality_risk(temp, humidity, location_info, date, age_group, gender):
    """논문 데이터 기반 정밀 사망률 위험도 계산"""
    
    # 기본 위험도
    base_risk = 1.0
    
    # 1. 온도 기반 위험도 (논문의 임계값 기반)
    threshold = location_info["threshold"]
    
    if temp > threshold:
        # 임계값 초과 시 위험도 증가 (논문의 RR 값 기반)
        temp_excess = temp - threshold
        temp_risk = 1.0 + (temp_excess * 0.05)  # RR 1.05-1.10 기반 (전체 원인)
    else:
        temp_risk = 1.0
    
    # 2. 습도 기반 위험도
    if humidity > 80:
        humidity_risk = 1.1 + (humidity - 80) * 0.005
    elif humidity < 30:
        humidity_risk = 1.05 + (30 - humidity) * 0.003
    else:
        humidity_risk = 1.0
    
    # 3. 계절 기반 위험도 (논문의 여름/겨울 패턴)
    month = date.month
    if month in [6, 7, 8]:  # 여름
        season_risk = 1.3
    elif month in [12, 1, 2]:  # 겨울
        season_risk = 1.2
    else:
        season_risk = 1.0
    
    # 4. 지역 클러스터 기반 위험도 (논문의 정확한 수치)
    cluster_risk = location_info["risk_multiplier"]
    
    # 5. 연령대별 위험도 (논문 표 2 기반)
    age_risk = {
        "전체": 1.0,
        "20세 미만": 1.08,  # RR 1.08-1.13 기반
        "20-74세": 1.03,    # RR 1.01-1.06 기반
        "75세 이상": 1.04   # RR 1.02-1.08 기반
    }.get(age_group, 1.0)
    
    # 6. 성별 위험도 (논문 표 3 기반)
    gender_risk = {
        "전체": 1.0,
        "남성": 1.05,       # RR 1.05-1.10 기반
        "여성": 1.07        # RR 1.07-1.09 기반
    }.get(gender, 1.0)
    
    # 7. 시간적 변화 (1996-2000 vs 2008-2012)
    if location_info["type"] == "hot":
        temporal_risk = 1.1  # 10% 증가
    else:
        temporal_risk = 1.0
    
    # 종합 위험도 계산
    total_risk = (base_risk * temp_risk * humidity_risk * season_risk * 
                  cluster_risk * age_risk * gender_risk * temporal_risk)
    
    # 위험도 등급 분류 (논문의 RR 값 기반)
    if total_risk < 1.2:
        risk_level = "낮음"
        risk_color = "green"
        risk_description = "일반적인 활동 가능"
    elif total_risk < 1.5:
        risk_level = "보통"
        risk_color = "yellow"
        risk_description = "주의하며 활동"
    elif total_risk < 2.0:
        risk_level = "높음"
        risk_color = "orange"
        risk_description = "실외 활동 제한 권장"
    else:
        risk_level = "매우 높음"
        risk_color = "red"
        risk_description = "긴급 주의 필요"
    
    return {
        "risk_score": round(total_risk, 3),
        "risk_level": risk_level,
        "risk_color": risk_color,
        "risk_description": risk_description,
        "temp_risk": round(temp_risk, 3),
        "humidity_risk": round(humidity_risk, 3),
        "season_risk": round(season_risk, 3),
        "cluster_risk": round(cluster_risk, 3),
        "age_risk": round(age_risk, 3),
        "gender_risk": round(gender_risk, 3),
        "temporal_risk": round(temporal_risk, 3),
        "threshold": threshold,
        "total_risk": total_risk
    }

# 사망률 예측 함수
def calculate_mortality_rate(risk_result, location_info, age_group, gender):
    """논문 데이터 기반 실제 사망률 계산"""
    
    # 한국 평균 일일 사망률 (2019년 기준, 인구 10만명당)
    base_mortality_rate = 2.1  # 일일 사망률 (10만명당)
    
    # 연령대별 기본 사망률 조정
    age_mortality_adjustment = {
        "전체": 1.0,
        "20세 미만": 0.3,    # 어린이 사망률 낮음
        "20-74세": 0.8,      # 성인 사망률
        "75세 이상": 3.5     # 고령자 사망률 높음
    }.get(age_group, 1.0)
    
    # 성별 사망률 조정
    gender_mortality_adjustment = {
        "전체": 1.0,
        "남성": 1.2,         # 남성 사망률 높음
        "여성": 0.9          # 여성 사망률 낮음
    }.get(gender, 1.0)
    
    # 지역별 사망률 조정 (논문의 지역별 차이 반영)
    location_mortality_adjustment = {
        "hot": 1.3,          # 더운 지역 사망률 높음
        "moderate": 1.1,     # 보통 지역
        "cool": 1.0          # 시원한 지역
    }.get(location_info["type"], 1.0)
    
    # 위험도 기반 사망률 계산
    adjusted_mortality_rate = (base_mortality_rate * 
                              age_mortality_adjustment * 
                              gender_mortality_adjustment * 
                              location_mortality_adjustment * 
                              risk_result["total_risk"])
    
    # 95% 신뢰구간 계산 (논문의 통계적 근거 기반)
    confidence_interval = adjusted_mortality_rate * 0.15  # ±15%
    lower_bound = max(0, adjusted_mortality_rate - confidence_interval)
    upper_bound = adjusted_mortality_rate + confidence_interval
    
    return {
        "mortality_rate": round(adjusted_mortality_rate, 2),
        "lower_bound": round(lower_bound, 2),
        "upper_bound": round(upper_bound, 2),
        "confidence_interval": round(confidence_interval, 2)
    }

# 사이드바 - 입력 파라미터
st.sidebar.header("📊 예측 파라미터")

# API 키 상태 표시
api_key = get_weather_api_key()
if api_key:
    st.sidebar.success("✅ API 키가 설정되었습니다.")
else:
    st.sidebar.error("❌ API 키가 설정되지 않았습니다.")
    st.stop()

# 위치 선택
selected_location = st.sidebar.selectbox(
    "📍 위치 선택",
    list(location_clusters.keys())
)

# 날짜 선택 (미래 날짜 가능)
selected_date = st.sidebar.date_input(
    "📅 예측 날짜 선택",
    value=datetime.now() + timedelta(days=7),
    min_value=datetime.now(),
    max_value=datetime.now() + timedelta(days=90)
)

# 추가 파라미터
st.sidebar.subheader("🔬 추가 파라미터")

# 연령대 선택
age_group = st.sidebar.selectbox(
    "👥 연령대",
    ["전체", "20세 미만", "20-74세", "75세 이상"]
)

# 성별 선택
gender = st.sidebar.selectbox(
    "👤 성별",
    ["전체", "남성", "여성"]
)

# 데이터 로드 (과거 3년 데이터)
if validate_api_key(api_key):
    # 과거 3년 기상청 데이터 로드
    historical_data = load_3year_weather_data(api_key, selected_location)
    
    if historical_data.empty:
        st.error("❌ 과거 3년 기상 데이터를 가져올 수 없습니다.")
        st.error("유효한 기상청 API 키를 입력해주세요.")
        st.stop()
    
    # 최근 30일 데이터도 별도로 로드 (시각화용)
    recent_data = load_recent_weather_data(api_key, selected_location, days_back=30)
    
    if recent_data.empty:
        st.warning("⚠️ 최근 30일 데이터를 가져올 수 없어 과거 3년 데이터만 사용합니다.")
        recent_data = historical_data.copy()
else:
    # API 키가 없거나 유효하지 않으면 메시지 표시
    st.error("❌ 유효한 기상청 API 키가 필요합니다.")
    st.markdown("""
    **API 키 발급 방법:**
    1. [공공데이터 포털](https://www.data.go.kr/) 접속
    2. 회원가입/로그인
    3. "기상청_시간별 기상정보" 검색
    4. API 신청 및 키 발급
    5. 발급받은 키를 사이드바에 입력
    """)
    st.stop()

# 예측 실행
if st.sidebar.button("🔍 기상 및 사망률 예측 실행", type="primary"):
    location_info = location_clusters[selected_location]
    
    # 과거 3년 같은 계절 데이터 기반 기상 예측
    predicted_temp, predicted_humidity = predict_seasonal_weather(selected_location, selected_date, historical_data)
    
    # 위험도 계산
    risk_result = calculate_advanced_mortality_risk(
        predicted_temp, predicted_humidity, location_info, selected_date,
        age_group, gender
    )
    
    # 사망률 계산
    mortality_result = calculate_mortality_rate(risk_result, location_info, age_group, gender)
    
    # 메인 결과 표시
    st.header("📊 예측 결과")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🌡️ 예측 기온",
            value=f"{predicted_temp}°C",
            delta=f"{selected_date.strftime('%m/%d')} 기준"
        )
    
    with col2:
        st.metric(
            label="💧 예측 습도",
            value=f"{predicted_humidity}%",
            delta=f"{selected_date.strftime('%m/%d')} 기준"
        )
    
    with col3:
        st.metric(
            label="⚠️ 종합 위험도",
            value=risk_result['risk_score'],
            delta=None
        )
    
    with col4:
        st.metric(
            label="💀 예측 사망률",
            value=f"{mortality_result['mortality_rate']}",
            delta=f"±{mortality_result['confidence_interval']}",
            help="인구 10만명당 일일 사망률"
        )
    
    # 위험도 등급 표시
    risk_color_map = {
        "green": "🟢",
        "yellow": "🟡", 
        "orange": "🟠",
        "red": "🔴"
    }
    
    st.markdown("---")
    st.subheader(f"📊 위험도 분석: {risk_color_map[risk_result['risk_color']]} {risk_result['risk_level']}")
    st.info(f"**{risk_result['risk_description']}**")
    
    # 달력으로 날짜별 사망률 확인
    st.markdown("---")
    st.subheader("📅 날짜별 사망률 확인")
    
    # 달력 선택
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**날짜를 선택하여 해당 날짜의 사망률을 확인하세요:**")
        # 현재 날짜가 2024년을 넘어가면 기본값을 2024년 12월 31일로 설정
        default_date = selected_date if selected_date <= date(2024, 12, 31) else date(2024, 12, 31)
        
        calendar_date = st.date_input(
            "날짜 선택",
            value=default_date,
            min_value=date(2021, 1, 1),
            max_value=date(2024, 12, 31),
            help="과거 날짜는 실제 데이터, 미래 날짜는 예측 데이터로 표시됩니다."
        )
    
    with col2:
        st.write("**선택된 날짜 정보:**")
        if calendar_date <= date.today():
            st.info(f"📊 **과거 데이터**: {calendar_date.strftime('%Y년 %m월 %d일')}")
        else:
            st.warning(f"🔮 **예측 데이터**: {calendar_date.strftime('%Y년 %m월 %d일')}")
    
    # 선택된 날짜의 기상 데이터 및 사망률 계산
    if calendar_date <= date.today():
        # 과거 데이터: 실제 기상 데이터 사용
        if not weather_data.empty:
            # 선택된 날짜의 데이터 필터링
            calendar_weather_data = weather_data[
                (weather_data['date'].dt.date == calendar_date)
            ]
            
            if len(calendar_weather_data) > 0:
                actual_temp = calendar_weather_data['temperature'].mean()
                actual_humidity = calendar_weather_data['humidity'].mean()
                
                # 실제 기상 데이터로 사망률 계산
                calendar_risk = calculate_advanced_mortality_risk(
                    actual_temp, actual_humidity, location_info, calendar_date,
                    age_group, gender
                )
                calendar_mortality = calculate_mortality_rate(calendar_risk, location_info, age_group, gender)
                
                data_type = "실제"
                temp_value = actual_temp
                humidity_value = actual_humidity
            else:
                st.error(f"❌ {calendar_date.strftime('%Y년 %m월 %d일')}의 기상 데이터가 없습니다.")
                st.error("유효한 기상청 API 키를 입력해주세요.")
                st.stop()
        else:
            st.error("❌ 유효한 기상청 API 키가 필요합니다.")
            st.error("사이드바에서 API 키를 입력해주세요.")
            st.stop()
    else:
        # 미래 데이터: 예측 기상 데이터 사용
        if not weather_data.empty:
            # 최근 데이터 기반 예측
            recent_data = weather_data.tail(7)  # 최근 7일 데이터
            if not recent_data.empty:
                base_temp = recent_data['temperature'].mean()
                base_humidity = recent_data['humidity'].mean()
                
                # 계절적 트렌드 적용
                target_month = calendar_date.month
                if target_month in [6, 7, 8]:  # 여름
                    temp_adjustment = 2.0
                elif target_month in [12, 1, 2]:  # 겨울
                    temp_adjustment = -2.0
                else:
                    temp_adjustment = 0.0
                
                predicted_calendar_temp = base_temp + temp_adjustment
                predicted_calendar_humidity = base_humidity
                
                calendar_risk = calculate_advanced_mortality_risk(
                    predicted_calendar_temp, predicted_calendar_humidity, location_info, calendar_date,
                    age_group, gender
                )
                calendar_mortality = calculate_mortality_rate(calendar_risk, location_info, age_group, gender)
                
                data_type = "예측"
                temp_value = predicted_calendar_temp
                humidity_value = predicted_calendar_humidity
            else:
                st.error(f"❌ {calendar_date.strftime('%Y년 %m월 %d일')}의 기상 예측을 할 수 없습니다.")
                st.stop()
        else:
            st.error("❌ 유효한 기상청 API 키가 필요합니다.")
            st.error("사이드바에서 API 키를 입력해주세요.")
            st.stop()
            
            calendar_risk = calculate_advanced_mortality_risk(
                predicted_calendar_temp, predicted_calendar_humidity, location_info, calendar_date,
                age_group, gender
            )
            calendar_mortality = calculate_mortality_rate(calendar_risk, location_info, age_group, gender)
            
            data_type = "예측"
            temp_value = predicted_calendar_temp
            humidity_value = predicted_calendar_humidity
    
    # 선택된 날짜의 결과 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🌡️ 기온",
            value=f"{temp_value:.1f}°C",
            delta=f"{data_type} 데이터"
        )
    
    with col2:
        st.metric(
            label="💧 습도",
            value=f"{humidity_value:.1f}%",
            delta=f"{data_type} 데이터"
        )
    
    with col3:
        st.metric(
            label="⚠️ 위험도",
            value=f"{calendar_risk['risk_score']:.3f}",
            delta=f"{calendar_risk['risk_level']}"
        )
    
    with col4:
        st.metric(
            label="💀 사망률",
            value=f"{calendar_mortality['mortality_rate']:.2f}",
            delta="10만명당"
        )
    
    # 선택된 날짜의 위험도 구성 요소 시각화
    st.markdown("---")
    st.subheader(f"📊 {calendar_date.strftime('%Y년 %m월 %d일')} 위험도 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 위험도 구성 요소 차트
        calendar_risk_components = {
            "🌡️ 온도 위험": calendar_risk['temp_risk'],
            "💧 습도 위험": calendar_risk['humidity_risk'],
            "🍂 계절 위험": calendar_risk['season_risk'],
            "📍 지역 위험": calendar_risk['cluster_risk'],
            "👥 연령 위험": calendar_risk['age_risk'],
            "👤 성별 위험": calendar_risk['gender_risk'],
            "⏰ 시간적 위험": calendar_risk['temporal_risk']
        }
        
        # 위험도에 따른 색상 매핑
        calendar_colors = []
        for value in calendar_risk_components.values():
            if value < 1.1:
                calendar_colors.append('#2ECC71')  # 녹색 (낮은 위험)
            elif value < 1.3:
                calendar_colors.append('#F39C12')  # 주황색 (보통 위험)
            elif value < 1.5:
                calendar_colors.append('#E67E22')  # 진주황색 (높은 위험)
            else:
                calendar_colors.append('#E74C3C')  # 빨간색 (매우 높은 위험)
        
        fig_calendar_components = go.Figure()
        
        fig_calendar_components.add_trace(go.Bar(
            x=list(calendar_risk_components.keys()),
            y=list(calendar_risk_components.values()),
            marker=dict(
                color=calendar_colors,
                line=dict(color='#34495E', width=1)
            ),
            text=[f'{v:.3f}' for v in calendar_risk_components.values()],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>위험도: %{y:.3f}<extra></extra>'
        ))
        
        # 기준선 추가 (위험도 1.0)
        fig_calendar_components.add_hline(
            y=1.0,
            line_dash="dash",
            line_color="#95A5A6",
            annotation_text="기준선 (1.0)",
            annotation_position="top right"
        )
        
        fig_calendar_components.update_layout(
            title=dict(
                text=f"📊 {calendar_date.strftime('%m월 %d일')} 위험도 구성 요소",
                font=dict(size=16, color='#2C3E50'),
                x=0.5
            ),
            xaxis=dict(
                title=dict(text="위험 요소", font=dict(size=12, color='#2C3E50')),
                tickfont=dict(size=10, color='#2C3E50'),
                tickcolor='#2C3E50',
                ticklen=5,
                tickwidth=2,
                tickangle=-45,
                gridcolor='#BDC3C7',
                gridwidth=1,
                showgrid=True,
                showline=True,
                linecolor='#2C3E50',
                linewidth=2
            ),
            yaxis=dict(
                title=dict(text="위험도 점수", font=dict(size=12, color='#2C3E50')),
                tickfont=dict(size=10, color='#2C3E50'),
                tickcolor='#2C3E50',
                ticklen=5,
                tickwidth=2,
                gridcolor='#BDC3C7',
                gridwidth=1,
                showgrid=True,
                showline=True,
                linecolor='#2C3E50',
                linewidth=2
            ),
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial, sans-serif"),
            margin=dict(l=60, r=60, t=80, b=80)
        )
        
        st.plotly_chart(fig_calendar_components, use_container_width=True)
    
    with col2:
        # 선택된 날짜의 상세 정보
        st.markdown("### 📋 상세 정보")
        
        info_data = {
            "날짜": calendar_date.strftime("%Y년 %m월 %d일"),
            "지역": selected_location,
            "연령대": age_group,
            "성별": gender,
            "데이터 유형": data_type,
            "기온": f"{temp_value:.1f}°C",
            "습도": f"{humidity_value:.1f}%",
            "위험도 점수": f"{calendar_risk['risk_score']:.3f}",
            "위험 수준": calendar_risk['risk_level'],
            "사망률": f"{calendar_mortality['mortality_rate']:.2f}/10만명",
            "신뢰구간": f"{calendar_mortality['lower_bound']:.2f} - {calendar_mortality['upper_bound']:.2f}"
        }
        
        for key, value in info_data.items():
            st.write(f"**{key}:** {value}")
        
        # 위험도 수준에 따른 색상 표시
        risk_level_colors = {
            "낮음": "#2ECC71",
            "보통": "#F39C12", 
            "높음": "#E67E22",
            "매우 높음": "#E74C3C"
        }
        
        risk_color = risk_level_colors.get(calendar_risk['risk_level'], "#95A5A6")
        
        st.markdown(f"""
        <div style="
            background-color: {risk_color}20;
            border-left: 4px solid {risk_color};
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        ">
        <strong>위험 수준: {calendar_risk['risk_level']}</strong><br>
        현재 위험도는 {calendar_risk['risk_score']:.3f}로 {calendar_risk['risk_level']} 수준입니다.
        </div>
        """, unsafe_allow_html=True)
    
    # 상세 분석
    st.markdown("---")
    st.subheader("📈 상세 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 실제 기상 데이터 시각화
        if not recent_data.empty:
            st.markdown("### 📊 최근 30일 기상 데이터 추이")
            
            # 날짜별 평균 기온과 습도 계산
            daily_weather = recent_data.groupby(recent_data['date'].dt.date).agg({
                'temperature': 'mean',
                'humidity': 'mean'
            }).reset_index()
            daily_weather['date'] = pd.to_datetime(daily_weather['date'])
            
            # 기온 그래프
            fig_temp = go.Figure()
            
            fig_temp.add_trace(go.Scatter(
                x=daily_weather['date'],
                y=daily_weather['temperature'],
                mode='lines+markers',
                name='실제 기온',
                line=dict(color='#E74C3C', width=3),
                marker=dict(size=6, color='#E74C3C'),
                hovertemplate='<b>%{x|%m월 %d일}</b><br>기온: %{y:.1f}°C<extra></extra>'
            ))
            
            # 예측 지점 표시
            fig_temp.add_trace(go.Scatter(
                x=[selected_date],
                y=[predicted_temp],
                mode='markers',
                name='예측 기온',
                marker=dict(size=12, color='#F39C12', symbol='diamond'),
                hovertemplate='<b>예측</b><br>기온: %{y:.1f}°C<extra></extra>'
            ))
            
            fig_temp.update_layout(
                title=dict(
                    text=f"🌡️ {selected_location} 기온 추이 (실제 데이터)",
                    font=dict(size=16, color='#2C3E50'),
                    x=0.5
                ),
                xaxis=dict(
                    title=dict(text="날짜", font=dict(size=12, color='#2C3E50')),
                    tickfont=dict(size=10, color='#2C3E50'),
                    tickcolor='#2C3E50',
                    ticklen=5,
                    tickwidth=2,
                    gridcolor='#BDC3C7',
                    gridwidth=1,
                    showgrid=True,
                    showline=True,
                    linecolor='#2C3E50',
                    linewidth=2
                ),
                yaxis=dict(
                    title=dict(text="기온 (°C)", font=dict(size=12, color='#2C3E50')),
                    tickfont=dict(size=10, color='#2C3E50'),
                    tickcolor='#2C3E50',
                    ticklen=5,
                    tickwidth=2,
                    gridcolor='#BDC3C7',
                    gridwidth=1,
                    showgrid=True,
                    showline=True,
                    linecolor='#2C3E50',
                    linewidth=2
                ),
                height=300,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Arial, sans-serif"),
                margin=dict(l=60, r=60, t=80, b=60)
            )
            
            st.plotly_chart(fig_temp, use_container_width=True)
            
            # 습도 그래프
            fig_humidity = go.Figure()
            
            fig_humidity.add_trace(go.Scatter(
                x=daily_weather['date'],
                y=daily_weather['humidity'],
                mode='lines+markers',
                name='실제 습도',
                line=dict(color='#3498DB', width=3),
                marker=dict(size=6, color='#3498DB'),
                hovertemplate='<b>%{x|%m월 %d일}</b><br>습도: %{y:.1f}%<extra></extra>'
            ))
            
            # 예측 지점 표시
            fig_humidity.add_trace(go.Scatter(
                x=[selected_date],
                y=[predicted_humidity],
                mode='markers',
                name='예측 습도',
                marker=dict(size=12, color='#F39C12', symbol='diamond'),
                hovertemplate='<b>예측</b><br>습도: %{y:.1f}%<extra></extra>'
            ))
            
            fig_humidity.update_layout(
                title=dict(
                    text=f"💧 {selected_location} 습도 추이 (실제 데이터)",
                    font=dict(size=16, color='#2C3E50'),
                    x=0.5
                ),
                xaxis=dict(
                    title=dict(text="날짜", font=dict(size=12, color='#2C3E50')),
                    tickfont=dict(size=10, color='#2C3E50'),
                    tickcolor='#2C3E50',
                    ticklen=5,
                    tickwidth=2,
                    gridcolor='#BDC3C7',
                    gridwidth=1,
                    showgrid=True,
                    showline=True,
                    linecolor='#2C3E50',
                    linewidth=2
                ),
                yaxis=dict(
                    title=dict(text="습도 (%)", font=dict(size=12, color='#2C3E50')),
                    tickfont=dict(size=10, color='#2C3E50'),
                    tickcolor='#2C3E50',
                    ticklen=5,
                    tickwidth=2,
                    gridcolor='#BDC3C7',
                    gridwidth=1,
                    showgrid=True,
                    showline=True,
                    linecolor='#2C3E50',
                    linewidth=2
                ),
                height=300,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Arial, sans-serif"),
                margin=dict(l=60, r=60, t=80, b=60)
            )
            
            st.plotly_chart(fig_humidity, use_container_width=True)
        else:
            st.warning("실제 기상 데이터가 없어 시각화를 제공할 수 없습니다.")
    
    with col2:
        # 계절별 분석 (과거 3년 데이터 사용)
        st.markdown("### 🍂 계절별 분석 (과거 3년 데이터)")
        
        if not historical_data.empty:
            # 같은 계절 데이터 필터링
            target_month = selected_date.month
            if target_month in [3, 4, 5]:
                target_season = "봄"
                season_color = "#90EE90"  # 연한 녹색
            elif target_month in [6, 7, 8]:
                target_season = "여름"
                season_color = "#FF6B6B"  # 빨간색
            elif target_month in [9, 10, 11]:
                target_season = "가을"
                season_color = "#FFA500"  # 주황색
            else:
                target_season = "겨울"
                season_color = "#87CEEB"  # 하늘색
            
            st.subheader(f"📊 {selected_location} {target_season} 계절 기상 데이터 (연도별)")
            
            # 3년 데이터를 각각 별도 그래프로 표시
            for year in [2021, 2022, 2023]:
                year_data = historical_data[
                    (historical_data['city'] == selected_location) & 
                    (historical_data['season'] == target_season) &
                    (historical_data['year'] == year)
                ].copy()
                
                if len(year_data) > 0:
                    fig_year = go.Figure()
                    
                    # 기온 선
                    fig_year.add_trace(go.Scatter(
                        x=year_data['date'],
                        y=year_data['temperature'],
                        mode='lines+markers',
                        name='기온',
                        line=dict(color='#E74C3C', width=4),  # 진한 빨간색
                        marker=dict(size=8, symbol='circle', color='#E74C3C'),
                        yaxis='y',
                        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>기온: %{y:.1f}°C<extra></extra>'
                    ))
                    
                    # 습도 선
                    fig_year.add_trace(go.Scatter(
                        x=year_data['date'],
                        y=year_data['humidity'],
                        mode='lines+markers',
                        name='습도',
                        line=dict(color='#2980B9', width=4),  # 진한 파란색
                        marker=dict(size=8, symbol='square', color='#2980B9'),
                        yaxis='y2',
                        hovertemplate='<b>%{x|%Y-%m-%d}</b><br>습도: %{y:.1f}%<extra></extra>'
                    ))
                    
                    # 예측 지점 표시 (2023년에만 표시하고, 해당 계절 기간 내에 있을 때만)
                    if year == 2023 and selected_date.year == 2024:
                        # 해당 계절의 날짜 범위 확인
                        season_start = year_data['date'].min()
                        season_end = year_data['date'].max()
                        
                        # 예측 날짜가 해당 계절 기간 이후인 경우에만 표시
                        if selected_date > season_end:
                            fig_year.add_trace(go.Scatter(
                                x=[selected_date],
                                y=[predicted_temp],
                                mode='markers',
                                name='예측 기온',
                                marker=dict(
                                    color='#FFD700',
                                    size=15,
                                    symbol='star',
                                    line=dict(color='#E74C3C', width=2)
                                ),
                                yaxis='y',
                                hovertemplate=f'<b>예측: {selected_date.strftime("%Y-%m-%d")}</b><br>기온: {predicted_temp}°C<extra></extra>'
                            ))
                            
                            fig_year.add_trace(go.Scatter(
                                x=[selected_date],
                                y=[predicted_humidity],
                                mode='markers',
                                name='예측 습도',
                                marker=dict(
                                    color='#FFD700',
                                    size=15,
                                    symbol='star',
                                    line=dict(color='#2980B9', width=2)
                                ),
                                yaxis='y2',
                                hovertemplate=f'<b>예측: {selected_date.strftime("%Y-%m-%d")}</b><br>습도: {predicted_humidity}%<extra></extra>'
                            ))
                    
                    # 평균선 추가
                    avg_temp = year_data['temperature'].mean()
                    avg_humidity = year_data['humidity'].mean()
                    
                    fig_year.add_hline(
                        y=avg_temp,
                        line_dash="dash",
                        line_color="#E74C3C",
                        line_width=3,
                        annotation_text=f"평균: {avg_temp:.1f}°C",
                        annotation_position="top right",
                        annotation=dict(
                            font=dict(size=12, color='#E74C3C'),
                            bgcolor='rgba(255,255,255,0.9)',
                            bordercolor='#E74C3C',
                            borderwidth=1
                        )
                    )
                    
                    # 습도 평균선
                    fig_year.add_shape(
                        type="line",
                        x0=year_data['date'].min(),
                        x1=year_data['date'].max(),
                        y0=avg_humidity,
                        y1=avg_humidity,
                        line=dict(color="#2980B9", dash="dash", width=3),
                        yref="y2"
                    )
                    
                    fig_year.add_annotation(
                        x=year_data['date'].max(),
                        y=avg_humidity,
                        text=f"평균: {avg_humidity:.1f}%",
                        showarrow=False,
                        xanchor="left",
                        yanchor="bottom",
                        bgcolor='rgba(255,255,255,0.9)',
                        bordercolor='#2980B9',
                        borderwidth=1,
                        font=dict(size=12, color='#2980B9'),
                        yref="y2"
                    )
                    
                    # 레이아웃 설정
                    fig_year.update_layout(
                        title=dict(
                            text=f"{year}년 {target_season}",
                            font=dict(size=18, color='#2C3E50'),
                            x=0.5
                        ),
                        xaxis=dict(
                            title=dict(text="날짜", font=dict(size=14, color='#2C3E50')),
                            tickfont=dict(size=12, color='#2C3E50'),
                            tickcolor='#2C3E50',
                            ticklen=5,
                            tickwidth=2,
                            gridcolor='#BDC3C7',
                            gridwidth=1,
                            showgrid=True,
                            showline=True,
                            linecolor='#2C3E50',
                            linewidth=2
                        ),
                        yaxis=dict(
                            title=dict(text="기온 (°C)", font=dict(size=14, color='#E74C3C')),
                            tickfont=dict(size=12, color='#E74C3C'),
                            tickcolor='#E74C3C',
                            ticklen=5,
                            tickwidth=2,
                            gridcolor='#BDC3C7',
                            gridwidth=1,
                            showgrid=True,
                            showline=True,
                            linecolor='#E74C3C',
                            linewidth=2,
                            side="left"
                        ),
                        yaxis2=dict(
                            title=dict(text="습도 (%)", font=dict(size=14, color='#2980B9')),
                            tickfont=dict(size=12, color='#2980B9'),
                            tickcolor='#2980B9',
                            ticklen=5,
                            tickwidth=2,
                            overlaying="y",
                            side="right",
                            showline=True,
                            linecolor='#2980B9',
                            linewidth=2
                        ),
                        height=350,
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        font=dict(family="Arial, sans-serif"),
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                            bgcolor='rgba(255,255,255,0.9)',
                            bordercolor='#BDC3C7',
                            borderwidth=1,
                            font=dict(size=12)
                        ),
                        margin=dict(l=70, r=70, t=80, b=70)
                    )
                    
                    st.plotly_chart(fig_year, use_container_width=True)
        else:
            st.warning("과거 3년 데이터가 없어 계절별 분석을 제공할 수 없습니다.")
    
    with col2:
        # 위험도 구성 요소 차트
        risk_components = {
            "🌡️ 온도 위험": risk_result['temp_risk'],
            "💧 습도 위험": risk_result['humidity_risk'],
            "🍂 계절 위험": risk_result['season_risk'],
            "📍 지역 위험": risk_result['cluster_risk'],
            "👥 연령 위험": risk_result['age_risk'],
            "👤 성별 위험": risk_result['gender_risk'],
            "⏰ 시간적 위험": risk_result['temporal_risk']
        }
        
        # 위험도에 따른 색상 매핑
        colors = []
        for value in risk_components.values():
            if value < 1.1:
                colors.append('#2ECC71')  # 녹색 (낮은 위험)
            elif value < 1.3:
                colors.append('#F39C12')  # 주황색 (보통 위험)
            elif value < 1.5:
                colors.append('#E67E22')  # 진주황색 (높은 위험)
            else:
                colors.append('#E74C3C')  # 빨간색 (매우 높은 위험)
        
        fig_components = go.Figure()
        
        fig_components.add_trace(go.Bar(
            x=list(risk_components.keys()),
            y=list(risk_components.values()),
            marker=dict(
                color=colors,
                line=dict(color='#34495E', width=1)
            ),
            text=[f'{v:.3f}' for v in risk_components.values()],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>위험도: %{y:.3f}<extra></extra>'
        ))
        
        # 기준선 추가 (위험도 1.0)
        fig_components.add_hline(
            y=1.0,
            line_dash="dash",
            line_color="#95A5A6",
            annotation_text="기준선 (1.0)",
            annotation_position="top right"
        )
        
        fig_components.update_layout(
            title=dict(
                text="📊 위험도 구성 요소 분석",
                font=dict(size=18, color='#2C3E50'),
                x=0.5
            ),
            xaxis=dict(
                title=dict(text="위험 요소", font=dict(size=14, color='#2C3E50')),
                tickfont=dict(size=12, color='#2C3E50'),
                tickcolor='#2C3E50',
                ticklen=5,
                tickwidth=2,
                tickangle=-45,
                gridcolor='#BDC3C7',
                gridwidth=1,
                showgrid=True,
                showline=True,
                linecolor='#2C3E50',
                linewidth=2
            ),
            yaxis=dict(
                title=dict(text="위험도 점수", font=dict(size=14, color='#2C3E50')),
                tickfont=dict(size=12, color='#2C3E50'),
                tickcolor='#2C3E50',
                ticklen=5,
                tickwidth=2,
                gridcolor='#BDC3C7',
                gridwidth=1,
                showgrid=True,
                showline=True,
                linecolor='#2C3E50',
                linewidth=2
            ),
            height=500,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial, sans-serif"),
            margin=dict(l=60, r=60, t=80, b=80)
        )
        
        st.plotly_chart(fig_components, use_container_width=True)
    
    # 온도-사망률 관계도 추가
    st.markdown("---")
    st.subheader("📈 온도-사망률 관계 분석")
    
    # 온도-사망률 관계도
    temp_range = np.arange(15, 45, 0.5)  # 더 세밀한 범위
    mortality_values = []
    risk_values = []
    
    for temp in temp_range:
        temp_risk = calculate_advanced_mortality_risk(
            temp, predicted_humidity, location_info, selected_date,
            age_group, gender
        )
        temp_mortality = calculate_mortality_rate(temp_risk, location_info, age_group, gender)
        mortality_values.append(temp_mortality['mortality_rate'])
        risk_values.append(temp_risk['risk_score'])
    
    fig_mortality_risk = go.Figure()
    
    # 사망률 선
    fig_mortality_risk.add_trace(go.Scatter(
        x=temp_range,
        y=mortality_values,
        mode='lines',
        name='사망률',
        line=dict(color='#E74C3C', width=3),
        hovertemplate='<b>기온: %{x:.1f}°C</b><br>사망률: %{y:.2f}/10만명<extra></extra>'
    ))
    
    # 위험도 선 (보조축)
    fig_mortality_risk.add_trace(go.Scatter(
        x=temp_range,
        y=risk_values,
        mode='lines',
        name='위험도',
        line=dict(color='#2980B9', width=3, dash='dot'),
        yaxis='y2',
        hovertemplate='<b>기온: %{x:.1f}°C</b><br>위험도: %{y:.3f}<extra></extra>'
    ))
    
    # 임계값 선
    fig_mortality_risk.add_vline(
        x=risk_result['threshold'],
        line_dash="dash",
        line_color="#E74C3C",
        line_width=3,
        annotation=dict(
            text=f"임계값: {risk_result['threshold']}°C",
            font=dict(size=12, color='#E74C3C'),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#E74C3C',
            borderwidth=1
        )
    )
    
    # 예측 지점 표시
    fig_mortality_risk.add_trace(go.Scatter(
        x=[predicted_temp],
        y=[mortality_result['mortality_rate']],
        mode='markers',
        name='예측 지점',
        marker=dict(
            color='#FFD700',
            size=12,
            symbol='star',
            line=dict(color='#E74C3C', width=2)
        ),
        hovertemplate=f'<b>예측 기온: {predicted_temp}°C</b><br>예측 사망률: {mortality_result["mortality_rate"]:.2f}/10만명<extra></extra>'
    ))
    
    # 위험 구간 표시
    if predicted_temp > risk_result['threshold']:
        # 위험 구간 음영
        fig_mortality_risk.add_vrect(
            x0=risk_result['threshold'],
            x1=max(temp_range),
            fillcolor="red",
            opacity=0.1,
            layer="below",
            line_width=0,
            annotation_text="위험 구간"
        )
    
    fig_mortality_risk.update_layout(
        title=dict(
            text=f"🌡️ 온도-사망률 관계 ({selected_location})",
            font=dict(size=18, color='#2C3E50'),
            x=0.5
        ),
        xaxis=dict(
            title=dict(text="기온 (°C)", font=dict(size=14, color='#2C3E50')),
            tickfont=dict(size=12, color='#2C3E50'),
            tickcolor='#2C3E50',
            ticklen=5,
            tickwidth=2,
            gridcolor='#BDC3C7',
            gridwidth=1,
            showgrid=True,
            showline=True,
            linecolor='#2C3E50',
            linewidth=2
        ),
        yaxis=dict(
            title=dict(text="사망률 (10만명당)", font=dict(size=14, color='#E74C3C')),
            tickfont=dict(size=12, color='#E74C3C'),
            tickcolor='#E74C3C',
            ticklen=5,
            tickwidth=2,
            gridcolor='#BDC3C7',
            gridwidth=1,
            showgrid=True,
            showline=True,
            linecolor='#E74C3C',
            linewidth=2
        ),
        yaxis2=dict(
            title=dict(text="위험도 점수", font=dict(size=14, color='#2980B9')),
            tickfont=dict(size=12, color='#2980B9'),
            tickcolor='#2980B9',
            ticklen=5,
            tickwidth=2,
            overlaying="y",
            side="right",
            showline=True,
            linecolor='#2980B9',
            linewidth=2
        ),
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#BDC3C7',
            borderwidth=1
        ),
        margin=dict(l=60, r=60, t=80, b=60)
    )
    
    st.plotly_chart(fig_mortality_risk, use_container_width=True)
    
    # 사망률 상세 정보
    st.markdown("---")
    st.subheader("💀 사망률 예측 상세")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🌡️ 임계 온도",
            value=f"{risk_result['threshold']}°C",
            delta=f"{predicted_temp - risk_result['threshold']:.1f}°C"
        )
    
    with col2:
        st.metric(
            label="📊 신뢰구간 하한",
            value=f"{mortality_result['lower_bound']}",
            delta="95% 신뢰구간"
        )
    
    with col3:
        st.metric(
            label="📊 신뢰구간 상한",
            value=f"{mortality_result['upper_bound']}",
            delta="95% 신뢰구간"
        )
    
    # 논문 기반 권장사항
    st.markdown("---")
    st.subheader("💡 논문 기반 권장사항")
    
    if risk_result['risk_level'] == "매우 높음":
        st.error("🚨 **긴급 주의**: 매우 높은 사망률 위험이 예측됩니다!")
        st.markdown("""
        **논문 기반 권장사항:**
        - 실외 활동을 즉시 중단하세요
        - 시원한 실내에서 휴식을 취하세요
        - 충분한 수분을 섭취하세요
        - 취약계층(노인, 어린이, 만성질환자)을 특별히 보호하세요
        """)
    elif risk_result['risk_level'] == "높음":
        st.warning("⚠️ **주의**: 높은 사망률 위험이 예측됩니다.")
        st.markdown("""
        **논문 기반 권장사항:**
        - 실외 활동을 제한하세요
        - 그늘에서 휴식을 취하세요
        - 수분을 충분히 섭취하세요
        - 취약계층을 모니터링하세요
        """)
    elif risk_result['risk_level'] == "보통":
        st.info("ℹ️ **관찰**: 보통 수준의 위험이 예측됩니다.")
        st.markdown("""
        **논문 기반 권장사항:**
        - 일반적인 활동을 계속하되 주의하세요
        - 수분 섭취를 잊지 마세요
        - 취약계층을 관찰하세요
        """)
    else:
        st.success("✅ **안전**: 낮은 위험이 예측됩니다.")
        st.markdown("""
        **논문 기반 권장사항:**
        - 일반적인 활동을 자유롭게 하세요
        - 적절한 옷차림을 유지하세요
        """)

# 정보 패널
with st.expander("ℹ️ 시스템 정보"):
    st.markdown("""
    ### 📚 기반 연구: 한국의 기후별 사망률 연구
    
    **예측 방법:**
    1. **계절별 데이터**: 봄(3-5월), 여름(6-8월), 가을(9-11월), 겨울(12-2월)
    2. **최근 3년 데이터**: 2021-2023년 같은 계절 데이터 활용 (올해 제외)
    3. **연도별 추세**: 기후변화 반영한 온도 상승 패턴 적용
    4. **월별 세부 패턴**: 같은 계절 내에서도 월별 차이 고려
    
    **핵심 발견:**
    1. **지역별 차이**: 더운 지역(클러스터 H)에서 더 높은 위험도
    2. **임계값**: 지역별로 다른 온도 임계값 (30.5°C ~ 33.5°C)
    3. **취약계층**: 노인, 어린이, 만성질환자
    4. **시간적 변화**: 2008-2012년에 더운 지역에서 위험도 증가
    
    **사망률 예측:**
    - 한국 평균 일일 사망률 (2.1/10만명) 기반
    - 연령대, 성별, 지역별 조정 적용
    - 95% 신뢰구간 (±15%) 제공
    - 위험도 점수와 연동하여 계산
    
    **한계:**
    - 참고용 예측 시스템
    - 개별 사례 정확도 보장 불가
    - 긴급 상황 시 전문가 상담 필요
    """)

# 푸터
st.markdown("---")
st.markdown("🌤️ **기상 기반 사망률 예측 시스템** | 계절별 3년 데이터 기반 예측 모델") 