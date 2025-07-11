"""
데이터 로더 모듈
30일 기상 데이터 로딩, 캐싱, 대체 데이터 생성 기능을 담당합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from typing import Optional, Dict, List
import os


class DataLoader:
    """30일 데이터 로더 클래스"""
    
    def __init__(self, weather_api):
        self.weather_api = weather_api
        self.cache = {}
    
    @st.cache_data
    def load_30day_data(_self, city: str) -> pd.DataFrame:
        """최근 30일 기상 데이터를 로드합니다 (오늘 제외)."""
        
        # 시작 날짜 계산 (오늘을 제외한 최근 30일)
        end_date = datetime.now() - timedelta(days=1)  # 어제까지 (오늘 제외)
        start_date = end_date - timedelta(days=29)  # 30일 전부터
        
        st.info(f"📅 {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')} (30일, 오늘 제외) 데이터를 가져옵니다.")
        
        # API로 실제 데이터 가져오기 시도
        historical_data = _self.weather_api.get_weather_data(
            city, 
            start_date.strftime('%Y%m%d'), 
            end_date.strftime('%Y%m%d')
        )
        
        if historical_data.empty:
            st.warning("⚠️ API에서 데이터를 가져올 수 없어 대체 데이터를 생성합니다.")
            historical_data = _self._generate_fallback_data(city, 30)
        
        return historical_data
    
    def _generate_fallback_data(self, city: str, days: int) -> pd.DataFrame:
        """대체 데이터를 생성합니다 (오늘 제외)."""
        
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
    
    def load_data_for_date_range(self, city: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """특정 날짜 범위의 데이터를 로드합니다."""
        
        # 오늘을 제외한 범위로 조정
        today = datetime.now().date()
        if end_date.date() >= today:
            end_date = datetime.combine(today - timedelta(days=1), datetime.min.time())
        
        if start_date >= end_date:
            st.error("❌ 시작 날짜는 종료 날짜보다 이전이어야 합니다.")
            return pd.DataFrame()
        
        st.info(f"📅 {start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%Y년 %m월 %d일')} 데이터를 가져옵니다.")
        
        # API로 실제 데이터 가져오기 시도
        historical_data = self.weather_api.get_weather_data(
            city, 
            start_date.strftime('%Y%m%d'), 
            end_date.strftime('%Y%m%d')
        )
        
        if historical_data.empty:
            st.warning("⚠️ API에서 데이터를 가져올 수 없어 대체 데이터를 생성합니다.")
            days = (end_date - start_date).days + 1
            historical_data = self._generate_fallback_data_for_range(city, start_date, end_date)
        
        return historical_data
    
    def _generate_fallback_data_for_range(self, city: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """특정 범위의 대체 데이터를 생성합니다."""
        
        all_data = []
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
            
            current_date += timedelta(days=1)
        
        df = pd.DataFrame(all_data)
        st.success(f"✅ {city}의 {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} 대체 데이터 생성 완료 ({len(df)}개 데이터)")
        
        return df
    
    def get_data_info(self, data: pd.DataFrame) -> Dict:
        """데이터 정보를 반환합니다."""
        if data.empty:
            return {}
        
        # 기온 정보 (평균/최고/최저)
        temp_info = ""
        if 'temp_max' in data.columns and 'temp_min' in data.columns:
            temp_info = f"평균: {data['temperature'].mean():.1f}°C, 최고: {data['temp_max'].max():.1f}°C, 최저: {data['temp_min'].min():.1f}°C"
        else:
            temp_info = f"{data['temperature'].min():.1f}°C ~ {data['temperature'].max():.1f}°C"
        
        # 습도 정보
        humidity_info = f"{data['humidity'].min():.1f}% ~ {data['humidity'].max():.1f}%"
        
        return {
            'total_records': len(data),
            'date_range': f"{data['date'].min().strftime('%Y-%m-%d')} ~ {data['date'].max().strftime('%Y-%m-%d')}",
            'days_covered': (data['date'].max() - data['date'].min()).days + 1,
            'city': data['city'].iloc[0] if len(data) > 0 else '',
            'temperature_range': temp_info,
            'humidity_range': humidity_info,
            'is_complete_30days': len(data) == 30,
            'missing_days': 30 - len(data) if len(data) < 30 else 0
        }
    
    def validate_data_quality(self, data: pd.DataFrame) -> Dict:
        """데이터 품질을 검증합니다."""
        if data.empty:
            return {'is_valid': False, 'issues': ['데이터가 비어있습니다.']}
        
        issues = []
        
        # 데이터 수 검증
        if len(data) < 30:
            issues.append(f"데이터가 부족합니다. (현재: {len(data)}일, 필요: 30일)")
        
        # 필수 컬럼 검증
        required_columns = ['date', 'city', 'temperature', 'humidity']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            issues.append(f"필수 컬럼이 누락되었습니다: {missing_columns}")
        
        # 데이터 타입 검증
        if 'temperature' in data.columns and not pd.api.types.is_numeric_dtype(data['temperature']):
            issues.append("기온 데이터가 숫자가 아닙니다.")
        
        if 'humidity' in data.columns and not pd.api.types.is_numeric_dtype(data['humidity']):
            issues.append("습도 데이터가 숫자가 아닙니다.")
        
        # 값 범위 검증
        if 'temperature' in data.columns:
            temp_range = data['temperature'].describe()
            if temp_range['min'] < -50 or temp_range['max'] > 50:
                issues.append("기온 값이 비정상적인 범위입니다.")
        
        if 'humidity' in data.columns:
            humidity_range = data['humidity'].describe()
            if humidity_range['min'] < 0 or humidity_range['max'] > 100:
                issues.append("습도 값이 비정상적인 범위입니다.")
        
        # 날짜 순서 검증
        if 'date' in data.columns:
            dates = data['date'].sort_values()
            if not dates.equals(data['date']):
                issues.append("날짜가 순서대로 정렬되지 않았습니다.")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'quality_score': max(0, 100 - len(issues) * 10)
        }
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """데이터를 정리합니다."""
        if data.empty:
            return data
        
        # 날짜 순서로 정렬
        data = data.sort_values('date').reset_index(drop=True)
        
        # 중복 제거
        data = data.drop_duplicates(subset=['date', 'city']).reset_index(drop=True)
        
        # 결측값 처리
        if 'temperature' in data.columns:
            data['temperature'] = data['temperature'].fillna(data['temperature'].mean())
        
        if 'humidity' in data.columns:
            data['humidity'] = data['humidity'].fillna(data['humidity'].mean())
        
        # 월 정보 추가 (없는 경우)
        if 'month' not in data.columns:
            data['month'] = data['date'].dt.month
        
        return data
    
 