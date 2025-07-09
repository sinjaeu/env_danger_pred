"""
사망률 계산 모듈
기상 데이터를 기반으로 사망률을 계산하는 기능을 담당합니다.
"""

import pandas as pd
import numpy as np
import streamlit as st


class MortalityCalculator:
    """사망률 계산 클래스"""
    
    def __init__(self):
        # 논문 기반 위험도 모델 파라미터
        self.risk_factors = {
            # 온도 위험도 (U자 곡선 모델)
            "temp_risk": {
                "optimal_temp": 22,  # 최적 온도
                "cold_threshold": 10,  # 추위 임계값
                "heat_threshold": 30,  # 더위 임계값
                "cold_risk_factor": 1.5,
                "heat_risk_factor": 2.0
            },
            
            # 습도 위험도
            "humidity_risk": {
                "optimal_humidity": 60,  # 최적 습도
                "low_threshold": 30,  # 낮은 습도 임계값
                "high_threshold": 80,  # 높은 습도 임계값
                "low_risk_factor": 1.2,
                "high_risk_factor": 1.3
            },
            
            # 계절 위험도
            "seasonal_risk": {
                "봄": 1.0,
                "여름": 1.1,
                "가을": 1.0,
                "겨울": 1.2
            },
            
            # 지역 위험도 (도시별 기후 특성)
            "regional_risk": {
                "서울": 1.0,
                "부산": 0.9,
                "대구": 1.1,
                "인천": 1.0,
                "광주": 0.95,
                "대전": 0.95,
                "울산": 0.9,
                "제주": 0.85
            },
            
            # 연령 위험도
            "age_risk": {
                "전체": 1.0,
                "20세 미만": 0.3,
                "20-74세": 1.0,
                "75세 이상": 2.5
            },
            
            # 성별 위험도
            "gender_risk": {
                "전체": 1.0,
                "남성": 1.1,
                "여성": 0.9
            },
            
            # 시간적 위험도 (월별)
            "temporal_risk": {
                1: 1.2,   # 1월
                2: 1.1,   # 2월
                3: 1.0,   # 3월
                4: 0.95,  # 4월
                5: 0.9,   # 5월
                6: 0.95,  # 6월
                7: 1.0,   # 7월
                8: 1.05,  # 8월
                9: 0.95,  # 9월
                10: 1.0,  # 10월
                11: 1.05, # 11월
                12: 1.15  # 12월
            }
        }
        
        # 기본 사망률 (10만명당)
        self.base_mortality_rate = 5.0
    
    def calculate_temperature_risk(self, temperature: float) -> float:
        """온도 기반 위험도를 계산합니다."""
        temp_risk = self.risk_factors["temp_risk"]
        
        if temperature < temp_risk["cold_threshold"]:
            # 추위 위험도 (선형 증가)
            cold_risk = 1 + (temp_risk["cold_threshold"] - temperature) * 0.1
            return min(cold_risk, temp_risk["cold_risk_factor"])
        elif temperature > temp_risk["heat_threshold"]:
            # 더위 위험도 (지수 증가)
            heat_risk = 1 + (temperature - temp_risk["heat_threshold"]) * 0.15
            return min(heat_risk, temp_risk["heat_risk_factor"])
        else:
            # 최적 온도 범위
            return 1.0
    
    def calculate_humidity_risk(self, humidity: float) -> float:
        """습도 기반 위험도를 계산합니다."""
        humidity_risk = self.risk_factors["humidity_risk"]
        
        if humidity < humidity_risk["low_threshold"]:
            # 낮은 습도 위험도
            low_risk = 1 + (humidity_risk["low_threshold"] - humidity) * 0.01
            return min(low_risk, humidity_risk["low_risk_factor"])
        elif humidity > humidity_risk["high_threshold"]:
            # 높은 습도 위험도
            high_risk = 1 + (humidity - humidity_risk["high_threshold"]) * 0.01
            return min(high_risk, humidity_risk["high_risk_factor"])
        else:
            # 최적 습도 범위
            return 1.0
    
    def calculate_seasonal_risk(self, season: str) -> float:
        """계절 기반 위험도를 계산합니다."""
        return self.risk_factors["seasonal_risk"].get(season, 1.0)
    
    def calculate_regional_risk(self, city: str) -> float:
        """지역 기반 위험도를 계산합니다."""
        return self.risk_factors["regional_risk"].get(city, 1.0)
    
    def calculate_age_risk(self, age_group: str) -> float:
        """연령대 기반 위험도를 계산합니다."""
        return self.risk_factors["age_risk"].get(age_group, 1.0)
    
    def calculate_gender_risk(self, gender: str) -> float:
        """성별 기반 위험도를 계산합니다."""
        return self.risk_factors["gender_risk"].get(gender, 1.0)
    
    def calculate_temporal_risk(self, month: int) -> float:
        """시간적 위험도를 계산합니다."""
        return self.risk_factors["temporal_risk"].get(month, 1.0)
    
    def calculate_mortality_rate(self, weather_data: dict, age_group: str = "전체", 
                               gender: str = "전체") -> dict:
        """종합적인 사망률을 계산합니다."""
        
        if not weather_data:
            return None
        
        # 각 위험도 계산
        temp_risk = self.calculate_temperature_risk(weather_data['temperature'])
        humidity_risk = self.calculate_humidity_risk(weather_data['humidity'])
        seasonal_risk = self.calculate_seasonal_risk(weather_data['season'])
        regional_risk = self.calculate_regional_risk(weather_data['city'])
        age_risk = self.calculate_age_risk(age_group)
        gender_risk = self.calculate_gender_risk(gender)
        temporal_risk = self.calculate_temporal_risk(weather_data['date'].month)
        
        # 종합 위험도 계산 (곱셈 모델)
        total_risk = (temp_risk * humidity_risk * seasonal_risk * regional_risk * 
                     age_risk * gender_risk * temporal_risk)
        
        # 사망률 계산 (10만명당)
        mortality_rate = self.base_mortality_rate * total_risk
        
        # 95% 신뢰구간 계산
        confidence_interval = mortality_rate * 0.2  # ±20%
        lower_bound = max(0, mortality_rate - confidence_interval)
        upper_bound = mortality_rate + confidence_interval
        
        # 위험 수준 분류
        if mortality_rate < 3:
            risk_level = "낮음"
        elif mortality_rate < 5:
            risk_level = "보통"
        elif mortality_rate < 8:
            risk_level = "높음"
        else:
            risk_level = "매우 높음"
        
        return {
            'mortality_rate': round(mortality_rate, 2),
            'lower_bound': round(lower_bound, 2),
            'upper_bound': round(upper_bound, 2),
            'risk_level': risk_level,
            'risk_factors': {
                'temperature_risk': round(temp_risk, 3),
                'humidity_risk': round(humidity_risk, 3),
                'seasonal_risk': round(seasonal_risk, 3),
                'regional_risk': round(regional_risk, 3),
                'age_risk': round(age_risk, 3),
                'gender_risk': round(gender_risk, 3),
                'temporal_risk': round(temporal_risk, 3),
                'total_risk': round(total_risk, 3)
            }
        }
    
    def calculate_mortality_trend(self, weather_data: pd.DataFrame, age_group: str = "전체", 
                                gender: str = "전체") -> pd.DataFrame:
        """시계열 사망률 트렌드를 계산합니다."""
        
        if weather_data.empty:
            return pd.DataFrame()
        
        mortality_data = []
        
        for _, row in weather_data.iterrows():
            weather_dict = {
                'date': row['date'],
                'city': row['city'],
                'temperature': row['temperature'],
                'humidity': row['humidity'],
                'season': row['season']
            }
            
            mortality_result = self.calculate_mortality_rate(weather_dict, age_group, gender)
            
            if mortality_result:
                mortality_data.append({
                    'date': row['date'],
                    'mortality_rate': mortality_result['mortality_rate'],
                    'risk_level': mortality_result['risk_level'],
                    'temperature': row['temperature'],
                    'humidity': row['humidity'],
                    'season': row['season']
                })
        
        return pd.DataFrame(mortality_data) 