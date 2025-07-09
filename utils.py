"""
유틸리티 모듈
공통으로 사용되는 유틸리티 함수들을 담당합니다.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st


def load_environment_variables():
    """환경 변수를 로드합니다."""
    try:
        from dotenv import load_dotenv
        load_dotenv('config.env')
        
        api_key = os.getenv('WEATHER_API_KEY')
        if not api_key:
            st.error("❌ config.env 파일에서 WEATHER_API_KEY를 찾을 수 없습니다.")
            st.info("config.env 파일을 생성하고 API 키를 설정해주세요.")
            return None
        
        return api_key
    except ImportError:
        st.error("❌ python-dotenv 패키지가 설치되지 않았습니다.")
        st.info("pip install python-dotenv 명령으로 설치해주세요.")
        return None
    except Exception as e:
        st.error(f"❌ 환경 변수 로드 중 오류가 발생했습니다: {e}")
        return None


def generate_fallback_data(city: str, years: list) -> pd.DataFrame:
    """API 실패 시 사용할 대체 데이터를 생성합니다."""
    
    st.info(f"📊 {city}의 대체 데이터를 생성합니다...")
    
    all_data = []
    
    for year in years:
        # 해당 년도의 1월 1일부터 12월 31일까지
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        
        current_date = start_date
        while current_date <= end_date:
            month = current_date.month
            
            # 계절 결정
            if month in [3, 4, 5]:
                season = "봄"
                base_temp = 15
                base_humidity = 55
                temp_variation = 8
                humidity_variation = 15
            elif month in [6, 7, 8]:
                season = "여름"
                base_temp = 25
                base_humidity = 70
                temp_variation = 6
                humidity_variation = 20
            elif month in [9, 10, 11]:
                season = "가을"
                base_temp = 18
                base_humidity = 60
                temp_variation = 7
                humidity_variation = 15
            else:
                season = "겨울"
                base_temp = 2
                base_humidity = 50
                temp_variation = 6
                humidity_variation = 20
            
            # 도시별 기후 특성 반영
            city_modifiers = {
                "서울": {"temp": 0, "humidity": 0},
                "부산": {"temp": 2, "humidity": 10},
                "대구": {"temp": 1, "humidity": -5},
                "인천": {"temp": -1, "humidity": 5},
                "광주": {"temp": 1, "humidity": 5},
                "대전": {"temp": 0, "humidity": 0},
                "울산": {"temp": 1, "humidity": 5},
                "제주": {"temp": 3, "humidity": 15}
            }
            
            modifier = city_modifiers.get(city, {"temp": 0, "humidity": 0})
            
            # 기온과 습도 생성 (정규분포 기반)
            temperature = base_temp + modifier["temp"] + np.random.normal(0, temp_variation)
            humidity = base_humidity + modifier["humidity"] + np.random.normal(0, humidity_variation)
            
            # 값 범위 제한
            temperature = max(-20, min(40, temperature))
            humidity = max(0, min(100, humidity))
            
            all_data.append({
                'date': current_date,
                'city': city,
                'temperature': round(temperature, 1),
                'humidity': round(humidity, 1),
                'month': month,
                'year': year,
                'season': season
            })
            
            current_date += timedelta(days=1)
    
    df = pd.DataFrame(all_data)
    st.success(f"✅ {city}의 {len(years)}년 대체 데이터 생성 완료 ({len(df)}개 데이터)")
    
    return df


def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """날짜 범위의 유효성을 검증합니다."""
    
    if start_date >= end_date:
        st.error("❌ 시작 날짜는 종료 날짜보다 이전이어야 합니다.")
        return False
    
    if end_date > datetime.now() + timedelta(days=90):
        st.error("❌ 예측 가능한 날짜는 현재로부터 최대 90일입니다.")
        return False
    
    return True


def format_date_for_display(date: datetime) -> str:
    """날짜를 표시용 형식으로 변환합니다."""
    return date.strftime('%Y년 %m월 %d일')


def format_date_for_api(date: datetime) -> str:
    """날짜를 API 요청용 형식으로 변환합니다."""
    return date.strftime('%Y%m%d')


def get_season_from_date(date: datetime) -> str:
    """날짜로부터 계절을 반환합니다."""
    month = date.month
    
    if month in [3, 4, 5]:
        return "봄"
    elif month in [6, 7, 8]:
        return "여름"
    elif month in [9, 10, 11]:
        return "가을"
    else:
        return "겨울"


def calculate_statistics(data: pd.DataFrame) -> dict:
    """데이터의 통계 정보를 계산합니다."""
    
    if data.empty:
        return {}
    
    stats = {
        'total_records': len(data),
        'date_range': {
            'start': data['date'].min().strftime('%Y-%m-%d'),
            'end': data['date'].max().strftime('%Y-%m-%d')
        },
        'temperature': {
            'mean': round(data['temperature'].mean(), 1),
            'min': round(data['temperature'].min(), 1),
            'max': round(data['temperature'].max(), 1),
            'std': round(data['temperature'].std(), 1)
        },
        'humidity': {
            'mean': round(data['humidity'].mean(), 1),
            'min': round(data['humidity'].min(), 1),
            'max': round(data['humidity'].max(), 1),
            'std': round(data['humidity'].std(), 1)
        },
        'seasonal_distribution': data['season'].value_counts().to_dict()
    }
    
    return stats


def display_statistics(stats: dict):
    """통계 정보를 표시합니다."""
    
    if not stats:
        st.warning("표시할 통계 정보가 없습니다.")
        return
    
    st.subheader("📈 데이터 통계")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("총 데이터 수", stats['total_records'])
        st.metric("평균 기온", f"{stats['temperature']['mean']}°C")
        st.metric("평균 습도", f"{stats['humidity']['mean']}%")
    
    with col2:
        st.metric("기온 범위", f"{stats['temperature']['min']}°C ~ {stats['temperature']['max']}°C")
        st.metric("습도 범위", f"{stats['humidity']['min']}% ~ {stats['humidity']['max']}%")
        st.metric("데이터 기간", f"{stats['date_range']['start']} ~ {stats['date_range']['end']}")
    
    # 계절별 분포
    st.subheader("🍂 계절별 데이터 분포")
    seasonal_data = pd.DataFrame(list(stats['seasonal_distribution'].items()), 
                                columns=['계절', '데이터 수'])
    
    st.bar_chart(seasonal_data.set_index('계절'))


def create_cache_key(city: str, years: list) -> str:
    """캐시 키를 생성합니다."""
    return f"{city}_{'_'.join(map(str, years))}"


def clear_cache():
    """캐시를 초기화합니다."""
    st.cache_data.clear()
    st.cache_resource.clear()
    st.success("✅ 캐시가 초기화되었습니다.") 