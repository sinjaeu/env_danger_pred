"""
기상 예측 모듈
과거 기상 데이터를 기반으로 미래 기온과 습도를 예측하는 기능을 담당합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st


class WeatherPredictor:
    """기상 예측 클래스"""
    
    def __init__(self):
        self.seasonal_patterns = {
            "봄": {"temp_trend": 0.1, "humidity_trend": -0.05},
            "여름": {"temp_trend": 0.05, "humidity_trend": 0.1},
            "가을": {"temp_trend": -0.1, "humidity_trend": -0.05},
            "겨울": {"temp_trend": -0.05, "humidity_trend": 0.05}
        }
    
    def predict_weather(self, historical_data: pd.DataFrame, days_ahead: int) -> pd.DataFrame:
        """과거 데이터를 기반으로 미래 기상을 예측합니다."""
        
        if historical_data.empty:
            st.error("예측을 위한 과거 데이터가 없습니다.")
            return pd.DataFrame()
        
        # 최근 30일 데이터 사용
        recent_data = historical_data.tail(30).copy()
        
        if recent_data.empty:
            st.error("최근 30일 데이터가 없습니다.")
            return pd.DataFrame()
        
        # 예측 데이터 생성
        predictions = []
        last_date = recent_data['date'].max()
        
        for i in range(1, days_ahead + 1):
            future_date = last_date + timedelta(days=i)
            month = future_date.month
            
            # 계절 결정
            if month in [3, 4, 5]:
                season = "봄"
            elif month in [6, 7, 8]:
                season = "여름"
            elif month in [9, 10, 11]:
                season = "가을"
            else:
                season = "겨울"
            
            # 계절별 평균값 계산
            season_data = recent_data[recent_data['season'] == season]
            
            if not season_data.empty:
                base_temp = season_data['temperature'].mean()
                base_humidity = season_data['humidity'].mean()
            else:
                base_temp = recent_data['temperature'].mean()
                base_humidity = recent_data['humidity'].mean()
            
            # 계절별 트렌드 적용
            temp_trend = self.seasonal_patterns[season]["temp_trend"]
            humidity_trend = self.seasonal_patterns[season]["humidity_trend"]
            
            # 예측값 계산 (랜덤 변동 추가)
            predicted_temp = base_temp + (temp_trend * i) + np.random.normal(0, 2)
            predicted_humidity = base_humidity + (humidity_trend * i) + np.random.normal(0, 5)
            
            # 값 범위 제한
            predicted_temp = max(-20, min(40, predicted_temp))
            predicted_humidity = max(0, min(100, predicted_humidity))
            
            predictions.append({
                'date': future_date,
                'city': recent_data['city'].iloc[0],
                'temperature': round(predicted_temp, 1),
                'humidity': round(predicted_humidity, 1),
                'month': month,
                'year': future_date.year,
                'season': season,
                'is_prediction': True
            })
        
        return pd.DataFrame(predictions)
    
    def get_weather_for_date(self, historical_data: pd.DataFrame, target_date: datetime) -> dict:
        """특정 날짜의 기상 데이터를 반환합니다 (과거는 실제, 미래는 예측)."""
        
        if historical_data.empty:
            return None
        
        # 과거 데이터에서 해당 날짜 찾기
        target_date_str = target_date.strftime('%Y-%m-%d')
        historical_data['date_str'] = historical_data['date'].dt.strftime('%Y-%m-%d')
        
        existing_data = historical_data[historical_data['date_str'] == target_date_str]
        
        if not existing_data.empty:
            # 실제 데이터가 있는 경우
            data = existing_data.iloc[0]
            return {
                'date': data['date'],
                'city': data['city'],
                'temperature': data['temperature'],
                'humidity': data['humidity'],
                'season': data['season'],
                'is_prediction': False
            }
        else:
            # 예측 데이터 생성
            days_ahead = (target_date - historical_data['date'].max()).days
            
            if days_ahead > 0:
                # 미래 날짜인 경우 예측
                prediction_data = self.predict_weather(historical_data, days_ahead)
                if not prediction_data.empty:
                    target_prediction = prediction_data[prediction_data['date'].dt.strftime('%Y-%m-%d') == target_date_str]
                    if not target_prediction.empty:
                        data = target_prediction.iloc[0]
                        return {
                            'date': data['date'],
                            'city': data['city'],
                            'temperature': data['temperature'],
                            'humidity': data['humidity'],
                            'season': data['season'],
                            'is_prediction': True
                        }
            
            return None 