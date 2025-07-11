"""
유틸리티 모듈
공통으로 사용되는 유틸리티 함수들을 담당합니다.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from typing import Dict


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
            
            # 월별 기본 기상 특성
            if month in [3, 4, 5]:
                base_temp = 15
                base_humidity = 55
                temp_variation = 8
                humidity_variation = 15
            elif month in [6, 7, 8]:
                base_temp = 25
                base_humidity = 70
                temp_variation = 6
                humidity_variation = 20
            elif month in [9, 10, 11]:
                base_temp = 18
                base_humidity = 60
                temp_variation = 7
                humidity_variation = 15
            else:
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
                'year': year
            })
            
            current_date += timedelta(days=1)
    
    df = pd.DataFrame(all_data)
    st.success(f"✅ {city}의 {len(years)}년 대체 데이터 생성 완료 ({len(df)}개 데이터)")
    
    return df


def generate_fallback_data_recent(city: str, days: int) -> pd.DataFrame:
    """최근 데이터용 대체 데이터를 생성합니다 (오늘 제외)."""
    
    st.info(f"📊 {city}의 최근 {days}일 대체 데이터를 생성합니다 (오늘 제외)...")
    
    all_data = []
    end_date = datetime.now() - timedelta(days=1)  # 어제까지 (오늘 제외)
    
    for i in range(days):
        current_date = end_date - timedelta(days=i)
        month = current_date.month
        
        # 월별 기본 기상 특성
        if month in [3, 4, 5]:
            base_temp = 15
            base_humidity = 55
            temp_variation = 8
            humidity_variation = 15
        elif month in [6, 7, 8]:
            base_temp = 25
            base_humidity = 70
            temp_variation = 6
            humidity_variation = 20
        elif month in [9, 10, 11]:
            base_temp = 18
            base_humidity = 60
            temp_variation = 7
            humidity_variation = 15
        else:
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
        
        # 평균 기온과 습도 생성 (정규분포 기반)
        avg_temperature = base_temp + modifier["temp"] + np.random.normal(0, temp_variation)
        avg_humidity = base_humidity + modifier["humidity"] + np.random.normal(0, humidity_variation)
        
        # 최고/최저 기온 생성 (평균 기온 기준으로 변동)
        temp_range = temp_variation * 1.5
        max_temperature = avg_temperature + np.random.uniform(0, temp_range)
        min_temperature = avg_temperature - np.random.uniform(0, temp_range)
        
        # 값 범위 제한
        avg_temperature = max(-20, min(40, avg_temperature))
        max_temperature = max(-20, min(40, max_temperature))
        min_temperature = max(-20, min(40, min_temperature))
        avg_humidity = max(0, min(100, avg_humidity))
        
        # 최고/최저 기온이 평균 기온보다 적절한 순서가 되도록 조정
        if max_temperature < avg_temperature:
            max_temperature = avg_temperature + np.random.uniform(1, 5)
        if min_temperature > avg_temperature:
            min_temperature = avg_temperature - np.random.uniform(1, 5)
        
        all_data.append({
            'date': current_date,
            'city': city,
            'temperature': round(avg_temperature, 1),  # 평균 기온
            'temp_max': round(max_temperature, 1),     # 최고 기온
            'temp_min': round(min_temperature, 1),     # 최저 기온
            'humidity': round(avg_humidity, 1),        # 평균 습도
            'month': month,
            'year': current_date.year
        })
    
    df = pd.DataFrame(all_data)
    st.success(f"✅ {city}의 최근 {days}일 대체 데이터 생성 완료 ({len(df)}개 데이터, 오늘 제외)")
    
    return df


def analyze_30day_patterns(data: pd.DataFrame) -> dict:
    """30일 데이터의 패턴을 분석합니다."""
    if data.empty:
        return {}
    
    analysis = {}
    
    # 기본 통계
    analysis['total_days'] = len(data)
    analysis['date_range'] = f"{data['date'].min().strftime('%Y-%m-%d')} ~ {data['date'].max().strftime('%Y-%m-%d')}"
    
    # 기온 분석
    temp_data = data['temperature']
    analysis['temperature'] = {
        'mean': round(temp_data.mean(), 1),
        'std': round(temp_data.std(), 1),
        'min': round(temp_data.min(), 1),
        'max': round(temp_data.max(), 1),
        'trend': '상승' if temp_data.iloc[-1] > temp_data.iloc[0] else '하락' if temp_data.iloc[-1] < temp_data.iloc[0] else '안정',
        'volatility': round(temp_data.std() / temp_data.mean() * 100, 1) if temp_data.mean() != 0 else 0
    }
    
    # 습도 분석
    humidity_data = data['humidity']
    analysis['humidity'] = {
        'mean': round(humidity_data.mean(), 1),
        'std': round(humidity_data.std(), 1),
        'min': round(humidity_data.min(), 1),
        'max': round(humidity_data.max(), 1),
        'trend': '상승' if humidity_data.iloc[-1] > humidity_data.iloc[0] else '하락' if humidity_data.iloc[-1] < humidity_data.iloc[0] else '안정',
        'volatility': round(humidity_data.std() / humidity_data.mean() * 100, 1) if humidity_data.mean() != 0 else 0
    }
    
    # 월별 분석
    month_counts = data['month'].value_counts()
    analysis['months'] = {
        'primary_month': month_counts.index[0] if len(month_counts) > 0 else '없음',
        'month_distribution': month_counts.to_dict(),
        'month_count': len(month_counts)
    }
    
    # 이상치 탐지
    temp_outliers = detect_outliers(temp_data)
    humidity_outliers = detect_outliers(humidity_data)
    
    analysis['outliers'] = {
        'temperature_outliers': len(temp_outliers),
        'humidity_outliers': len(humidity_outliers),
        'total_outliers': len(temp_outliers) + len(humidity_outliers)
    }
    
    # 트렌드 분석
    analysis['trends'] = analyze_trends(data)
    
    return analysis


def detect_outliers(data: pd.Series, threshold: float = 2.0) -> list:
    """데이터에서 이상치를 탐지합니다."""
    if len(data) < 2:
        return []
    
    # NaN 값 제거
    data_clean = data.dropna()
    if len(data_clean) < 2:
        return []
    
    mean = data_clean.mean()
    std = data_clean.std()
    
    # 표준편차가 0이거나 너무 작은 경우 처리
    if std == 0 or np.isnan(std) or std < 1e-10:
        return []
    
    outliers = []
    for i, value in enumerate(data):
        if pd.isna(value):
            continue
        z_score = abs((value - mean) / std)
        if z_score > threshold:
            outliers.append(i)
    
    return outliers


def analyze_trends(data: pd.DataFrame) -> dict:
    """30일 데이터의 트렌드를 분석합니다."""
    trends = {}
    
    # 기온 트렌드
    temp_data = data['temperature'].values
    if len(temp_data) > 1:
        temp_slope = np.polyfit(range(len(temp_data)), temp_data, 1)[0]
        trends['temperature_trend'] = {
            'slope': round(temp_slope, 3),
            'direction': '상승' if temp_slope > 0.1 else '하락' if temp_slope < -0.1 else '안정',
            'strength': '강함' if abs(temp_slope) > 0.5 else '보통' if abs(temp_slope) > 0.2 else '약함'
        }
    
    # 습도 트렌드
    humidity_data = data['humidity'].values
    if len(humidity_data) > 1:
        humidity_slope = np.polyfit(range(len(humidity_data)), humidity_data, 1)[0]
        trends['humidity_trend'] = {
            'slope': round(humidity_slope, 3),
            'direction': '상승' if humidity_slope > 0.5 else '하락' if humidity_slope < -0.5 else '안정',
            'strength': '강함' if abs(humidity_slope) > 2.0 else '보통' if abs(humidity_slope) > 1.0 else '약함'
        }
    
    return trends


def calculate_30day_statistics(data: pd.DataFrame) -> dict:
    """30일 데이터의 상세 통계를 계산합니다."""
    if data.empty:
        return {}
    
    stats = {}
    
    # 기본 통계
    stats['total_days'] = len(data)
    stats['date_range'] = f"{data['date'].min().strftime('%Y-%m-%d')} ~ {data['date'].max().strftime('%Y-%m-%d')}"
    
    # 기온 통계
    temp_data = data['temperature'].dropna()
    if len(temp_data) > 0:
        temp_mean = temp_data.mean()
        temp_std = temp_data.std()
        temp_volatility = round(temp_std / temp_mean * 100, 1) if temp_mean != 0 and not np.isnan(temp_mean) else 0
        
        stats['temperature'] = {
            'mean': round(temp_mean, 1),
            'std': round(temp_std, 1),
            'min': round(temp_data.min(), 1),
            'max': round(temp_data.max(), 1),
            'trend': '상승' if temp_data.iloc[-1] > temp_data.iloc[0] else '하락' if temp_data.iloc[-1] < temp_data.iloc[0] else '안정',
            'volatility': temp_volatility
        }
    else:
        stats['temperature'] = {
            'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'trend': '안정', 'volatility': 0
        }
    
    # 습도 통계
    humidity_data = data['humidity'].dropna()
    if len(humidity_data) > 0:
        humidity_mean = humidity_data.mean()
        humidity_std = humidity_data.std()
        humidity_volatility = round(humidity_std / humidity_mean * 100, 1) if humidity_mean != 0 and not np.isnan(humidity_mean) else 0
        
        stats['humidity'] = {
            'mean': round(humidity_mean, 1),
            'std': round(humidity_std, 1),
            'min': round(humidity_data.min(), 1),
            'max': round(humidity_data.max(), 1),
            'trend': '상승' if humidity_data.iloc[-1] > humidity_data.iloc[0] else '하락' if humidity_data.iloc[-1] < humidity_data.iloc[0] else '안정',
            'volatility': humidity_volatility
        }
    else:
        stats['humidity'] = {
            'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'trend': '안정', 'volatility': 0
        }
    
    # 월별 분석
    month_counts = data['month'].value_counts()
    stats['months'] = {
        'primary_month': month_counts.index[0] if len(month_counts) > 0 else '없음',
        'month_distribution': month_counts.to_dict(),
        'month_count': len(month_counts)
    }
    
    # 이상치 탐지
    temp_outliers = detect_outliers(temp_data)
    humidity_outliers = detect_outliers(humidity_data)
    
    stats['outliers'] = {
        'temperature_outliers': len(temp_outliers),
        'humidity_outliers': len(humidity_outliers),
        'total_outliers': len(temp_outliers) + len(humidity_outliers)
    }
    
    # 트렌드 분석
    trends = analyze_trends(data)
    stats['trends'] = trends
    
    return stats


def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """날짜 범위의 유효성을 검증합니다."""
    
    if start_date >= end_date:
        st.error("❌ 시작 날짜는 종료 날짜보다 이전이어야 합니다.")
        return False
    
    if end_date > datetime.now() + timedelta(days=90):
        st.error("❌ 종료 날짜는 현재로부터 90일 이후일 수 없습니다.")
        return False
    
    return True


def format_date_for_api(date: datetime) -> str:
    """날짜를 API용 형식으로 변환합니다."""
    return date.strftime('%Y%m%d')





def calculate_statistics(data: pd.DataFrame) -> Dict:
    """기상 데이터의 기본 통계를 계산합니다."""
    if data.empty:
        return {}
    
    # 기온 통계 계산 (안전장치 추가)
    temp_data = data['temperature'].dropna()
    if len(temp_data) > 0:
        temp_mean = temp_data.mean()
        temp_std = temp_data.std()
        temp_max = temp_data.max()
        temp_min = temp_data.min()
    else:
        temp_mean = temp_std = temp_max = temp_min = 0
    
    # 습도 통계 계산 (안전장치 추가)
    humidity_data = data['humidity'].dropna()
    if len(humidity_data) > 0:
        humidity_mean = humidity_data.mean()
        humidity_std = humidity_data.std()
        humidity_max = humidity_data.max()
        humidity_min = humidity_data.min()
    else:
        humidity_mean = humidity_std = humidity_max = humidity_min = 0
    
    stats = {
        '기본 정보': {
            '총 데이터 수': len(data),
            '분석 기간': f"{data['date'].min().strftime('%Y-%m-%d')} ~ {data['date'].max().strftime('%Y-%m-%d')}",
            '도시': data['city'].iloc[0] if len(data) > 0 else 'N/A'
        },
        '기온 통계 (°C)': {
            '평균 기온': round(temp_mean, 1),
            '최고 기온': round(temp_max, 1),
            '최저 기온': round(temp_min, 1),
            '기온 표준편차': round(temp_std, 1)
        },
        '습도 통계 (%)': {
            '평균 습도': round(humidity_mean, 1),
            '최고 습도': round(humidity_max, 1),
            '최저 습도': round(humidity_min, 1),
            '습도 표준편차': round(humidity_std, 1)
        }
    }
    
    # 최고/최저 기온 정보가 있는 경우 추가
    if 'temp_max' in data.columns and 'temp_min' in data.columns:
        stats['기온 통계 (°C)'].update({
            '일 최고 기온 평균': round(data['temp_max'].mean(), 1),
            '일 최저 기온 평균': round(data['temp_min'].mean(), 1),
            '최고 기온 범위': f"{data['temp_max'].min():.1f} ~ {data['temp_max'].max():.1f}",
            '최저 기온 범위': f"{data['temp_min'].min():.1f} ~ {data['temp_min'].max():.1f}"
        })
    
    return stats


def display_statistics(stats: Dict):
    """통계 정보를 표시합니다."""
    if not stats:
        st.warning("표시할 통계가 없습니다.")
        return
    
    st.subheader("📊 기본 통계 정보")
    
    # 기본 정보
    if '기본 정보' in stats:
        basic_info = stats['기본 정보']
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("총 데이터 수", basic_info.get('총 데이터 수', 0))
        
        with col2:
            st.metric("도시", basic_info.get('도시', 'N/A'))
        
        with col3:
            st.metric("분석 기간", basic_info.get('분석 기간', 'N/A'))
    
    # 기온 통계
    if '기온 통계 (°C)' in stats:
        st.subheader("🌡️ 기온 통계")
        temp_stats = stats['기온 통계 (°C)']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("평균 기온", f"{temp_stats.get('평균 기온', 0)}°C")
        
        with col2:
            st.metric("최고 기온", f"{temp_stats.get('최고 기온', 0)}°C")
        
        with col3:
            st.metric("최저 기온", f"{temp_stats.get('최저 기온', 0)}°C")
        
        with col4:
            st.metric("표준편차", f"{temp_stats.get('기온 표준편차', 0)}°C")
        
        # 최고/최저 기온 정보가 있는 경우 추가 표시
        if '일 최고 기온 평균' in temp_stats:
            st.info(f"📈 일 최고 기온 평균: {temp_stats['일 최고 기온 평균']}°C | 📉 일 최저 기온 평균: {temp_stats['일 최저 기온 평균']}°C")
    
    # 습도 통계
    if '습도 통계 (%)' in stats:
        st.subheader("💧 습도 통계")
        humidity_stats = stats['습도 통계 (%)']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("평균 습도", f"{humidity_stats.get('평균 습도', 0)}%")
        
        with col2:
            st.metric("최고 습도", f"{humidity_stats.get('최고 습도', 0)}%")
        
        with col3:
            st.metric("최저 습도", f"{humidity_stats.get('최저 습도', 0)}%")
        
        with col4:
            st.metric("표준편차", f"{humidity_stats.get('습도 표준편차', 0)}%")
    
    return


def create_cache_key(city: str, years: list) -> str:
    """캐시 키를 생성합니다."""
    return f"{city}_{'_'.join(map(str, years))}"


def clear_cache():
    """캐시를 초기화합니다."""
    st.cache_data.clear()
    st.success("✅ 캐시가 초기화되었습니다.") 