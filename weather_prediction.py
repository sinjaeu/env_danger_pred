"""
기상 예측 모듈 (XGBoost + 시간 가중치 적용)
최근 데이터에 높은 가중치를 적용하여 더 정확한 예측을 수행합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from typing import Dict, List, Optional, Tuple
import xgboost as xgb
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit
import warnings
warnings.filterwarnings('ignore')


class WeatherPredictor:
    """XGBoost 기반 시간 가중치 기상 예측 클래스"""
    
    def __init__(self):
        self.temp_model = None
        self.humidity_model = None
        self.scaler = RobustScaler()  # 이상치에 강한 스케일러
        self.is_trained = False
        self.feature_importance = {}
        
    def calculate_time_weights(self, data: pd.DataFrame, decay_factor: float = 0.92) -> np.ndarray:
        """
        시간 가중치를 계산합니다.
        최근 데이터일수록 높은 가중치를 부여합니다.
        
        Args:
            data: 기상 데이터 DataFrame
            decay_factor: 시간 감쇠 계수 (0.9~0.95 권장)
        
        Returns:
            시간 가중치 배열
        """
        n_samples = len(data)
        weights = np.zeros(n_samples)
        
        # 최신 데이터부터 역순으로 가중치 계산
        for i in range(n_samples):
            # 최신 데이터(인덱스 n_samples-1)가 가장 높은 가중치
            time_distance = n_samples - 1 - i
            weights[i] = decay_factor ** time_distance
        
        # 가중치 정규화 (합이 1이 되도록)
        weights = weights / np.sum(weights)
        
        return weights
    
    def create_advanced_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        고급 시간 관련 특성을 생성합니다.
        
        Args:
            data: 기상 데이터 DataFrame
        
        Returns:
            고급 특성이 추가된 DataFrame
        """
        df = data.copy()
        
        # 기본 시간 특성
        df['day_of_year'] = df['date'].dt.dayofyear
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['day_of_week'] = df['date'].dt.dayofweek
        df['quarter'] = df['date'].dt.quarter
        
        # 계절 특성 (사인/코사인 변환)
        df['season_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365.25)
        df['season_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365.25)
        
        # 월별 특성 (사인/코사인 변환)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # 주별 특성
        df['week_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 7)
        df['week_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 7)
        
        # 시간 지연 특성 (lag features) - 더 많은 지연
        for lag in [1, 2, 3, 5, 7, 10, 14]:  # 다양한 지연
            df[f'temp_lag_{lag}'] = df['temperature'].shift(lag)
            df[f'humidity_lag_{lag}'] = df['humidity'].shift(lag)
        
        # 이동평균 특성 (다양한 윈도우)
        for window in [3, 5, 7, 10, 14, 21]:  # 다양한 윈도우
            df[f'temp_ma_{window}'] = df['temperature'].rolling(window=window, min_periods=1).mean()
            df[f'humidity_ma_{window}'] = df['humidity'].rolling(window=window, min_periods=1).mean()
        
        # 이동중앙값 특성
        for window in [3, 7, 14]:
            df[f'temp_median_{window}'] = df['temperature'].rolling(window=window, min_periods=1).median()
            df[f'humidity_median_{window}'] = df['humidity'].rolling(window=window, min_periods=1).median()
        
        # 변동성 특성
        for window in [3, 7, 14]:
            df[f'temp_std_{window}'] = df['temperature'].rolling(window=window, min_periods=1).std()
            df[f'humidity_std_{window}'] = df['humidity'].rolling(window=window, min_periods=1).std()
        
        # 범위 특성
        for window in [3, 7, 14]:
            df[f'temp_range_{window}'] = df['temperature'].rolling(window=window, min_periods=1).max() - \
                                       df['temperature'].rolling(window=window, min_periods=1).min()
            df[f'humidity_range_{window}'] = df['humidity'].rolling(window=window, min_periods=1).max() - \
                                           df['humidity'].rolling(window=window, min_periods=1).min()
        
        # 변화율 특성
        df['temp_change_1d'] = df['temperature'].diff(1)
        df['humidity_change_1d'] = df['humidity'].diff(1)
        df['temp_change_3d'] = df['temperature'].diff(3)
        df['humidity_change_3d'] = df['humidity'].diff(3)
        
        # 상대적 위치 특성
        for window in [7, 14, 30]:
            df[f'temp_rank_{window}'] = df['temperature'].rolling(window=window, min_periods=1).rank(pct=True)
            df[f'humidity_rank_{window}'] = df['humidity'].rolling(window=window, min_periods=1).rank(pct=True)
        
        # 온습도 상호작용 특성
        df['temp_humidity_interaction'] = df['temperature'] * df['humidity'] / 100
        df['temp_humidity_ratio'] = df['temperature'] / (df['humidity'] + 1)
        
        # 추세 특성
        for window in [7, 14]:
            df[f'temp_trend_{window}'] = df['temperature'].rolling(window=window, min_periods=1).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
            )
            df[f'humidity_trend_{window}'] = df['humidity'].rolling(window=window, min_periods=1).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0
            )
        
        # 결측값 처리
        df = df.bfill().ffill()
        
        return df
    
    def create_xgboost_model(self, target_type: str = 'temperature') -> xgb.XGBRegressor:
        """
        XGBoost 모델을 생성합니다.
        
        Args:
            target_type: 예측 대상 ('temperature' 또는 'humidity')
        
        Returns:
            XGBoost 모델
        """
        if target_type == 'temperature':
            # 기온 예측용 하이퍼파라미터
            model = xgb.XGBRegressor(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                colsample_bylevel=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=-1
            )
        else:
            # 습도 예측용 하이퍼파라미터
            model = xgb.XGBRegressor(
                n_estimators=250,
                max_depth=5,
                learning_rate=0.06,
                subsample=0.85,
                colsample_bytree=0.85,
                colsample_bylevel=0.85,
                reg_alpha=0.05,
                reg_lambda=0.8,
                random_state=42,
                n_jobs=-1
            )
        
        return model
    
    def train_weighted_xgboost(self, data: pd.DataFrame, target_col: str, 
                              feature_cols: List[str], weights: np.ndarray) -> xgb.XGBRegressor:
        """
        가중치를 적용한 XGBoost 모델을 훈련합니다.
        
        Args:
            data: 훈련 데이터
            target_col: 예측 대상 컬럼
            feature_cols: 특성 컬럼들
            weights: 시간 가중치
        
        Returns:
            훈련된 XGBoost 모델
        """
        # 특성과 타겟 준비
        X = data[feature_cols].values
        y = data[target_col].values
        
        # 스케일링
        X_scaled = self.scaler.fit_transform(X)
        
        # 시간 가중치 적용
        sample_weights = weights * len(data)  # 가중치 스케일링
        
        # XGBoost 모델 생성
        model = self.create_xgboost_model(target_col)
        
        # 시계열 교차 검증
        tscv = TimeSeriesSplit(n_splits=3)
        
        # 모델 훈련
        model.fit(
            X_scaled, y,
            sample_weight=sample_weights
        )
        
        return model
    
    def predict_weather(self, historical_data: pd.DataFrame, days_ahead: int) -> pd.DataFrame:
        """
        XGBoost 기반 시간 가중치 기상 예측을 수행합니다.
        
        Args:
            historical_data: 과거 30일 기상 데이터
            days_ahead: 예측할 일수
        
        Returns:
            예측 결과 DataFrame
        """
        if historical_data.empty:
            st.error("❌ 예측을 위한 데이터가 없습니다.")
            return pd.DataFrame()
        
        st.info(f"🚀 XGBoost + 시간 가중치 기반 예측 모델로 {days_ahead}일 후까지 예측합니다...")
        
        # 고급 특성 생성
        data_with_features = self.create_advanced_features(historical_data)
        
        # 시간 가중치 계산
        weights = self.calculate_time_weights(data_with_features, decay_factor=0.92)
        
        # 가중치 시각화
        self._visualize_weights(weights, historical_data['date'])
        
        # 특성 컬럼 정의 (더 많은 특성)
        feature_cols = [
            'day_of_year', 'month', 'day', 'day_of_week', 'quarter',
            'season_sin', 'season_cos', 'month_sin', 'month_cos', 'week_sin', 'week_cos',
            'temp_lag_1', 'temp_lag_2', 'temp_lag_3', 'temp_lag_5', 'temp_lag_7', 'temp_lag_10', 'temp_lag_14',
            'humidity_lag_1', 'humidity_lag_2', 'humidity_lag_3', 'humidity_lag_5', 'humidity_lag_7', 'humidity_lag_10', 'humidity_lag_14',
            'temp_ma_3', 'temp_ma_5', 'temp_ma_7', 'temp_ma_10', 'temp_ma_14', 'temp_ma_21',
            'humidity_ma_3', 'humidity_ma_5', 'humidity_ma_7', 'humidity_ma_10', 'humidity_ma_14', 'humidity_ma_21',
            'temp_median_3', 'temp_median_7', 'temp_median_14',
            'humidity_median_3', 'humidity_median_7', 'humidity_median_14',
            'temp_std_3', 'temp_std_7', 'temp_std_14',
            'humidity_std_3', 'humidity_std_7', 'humidity_std_14',
            'temp_range_3', 'temp_range_7', 'temp_range_14',
            'humidity_range_3', 'humidity_range_7', 'humidity_range_14',
            'temp_change_1d', 'temp_change_3d', 'humidity_change_1d', 'humidity_change_3d',
            'temp_rank_7', 'temp_rank_14', 'temp_rank_30',
            'humidity_rank_7', 'humidity_rank_14', 'humidity_rank_30',
            'temp_humidity_interaction', 'temp_humidity_ratio',
            'temp_trend_7', 'temp_trend_14', 'humidity_trend_7', 'humidity_trend_14'
        ]
        
        # 결측값이 있는 특성 제거
        available_features = [col for col in feature_cols if col in data_with_features.columns]
        
        # 기온 모델 훈련
        st.info("🌡️ XGBoost 기온 예측 모델 훈련 중...")
        self.temp_model = self.train_weighted_xgboost(
            data_with_features, 'temperature', available_features, weights
        )
        
        # 습도 모델 훈련
        st.info("💧 XGBoost 습도 예측 모델 훈련 중...")
        self.humidity_model = self.train_weighted_xgboost(
            data_with_features, 'humidity', available_features, weights
        )
        
        self.is_trained = True
        
        # 특성 중요도 저장
        self.feature_importance = {
            'temperature': dict(zip(available_features, self.temp_model.feature_importances_)),
            'humidity': dict(zip(available_features, self.humidity_model.feature_importances_))
        }
        
        # 예측 수행
        predictions = []
        last_date = historical_data['date'].max()
        
        for i in range(1, days_ahead + 1):
            pred_date = last_date + timedelta(days=i)
            
            # 예측용 특성 생성
            pred_features = self._create_prediction_features(
                data_with_features, pred_date, available_features
            )
            
            # 스케일링 적용
            pred_features_scaled = self.scaler.transform([pred_features])
            
            # 예측 수행
            pred_temp = self.temp_model.predict(pred_features_scaled)[0]
            pred_humidity = self.humidity_model.predict(pred_features_scaled)[0]
            
            # 값 범위 제한
            pred_temp = max(-20, min(40, pred_temp))
            pred_humidity = max(0, min(100, pred_humidity))
            
            predictions.append({
                'date': pred_date,
                'temperature': round(pred_temp, 1),
                'humidity': round(pred_humidity, 1),
                'month': pred_date.month,
                'year': pred_date.year,
                'is_prediction': True
            })
        
        predictions_df = pd.DataFrame(predictions)
    
        # 모델 성능 평가
        self._evaluate_model_performance(data_with_features, available_features)
        
        # 특성 중요도 시각화
        self._visualize_feature_importance()
        
        st.success(f"✅ XGBoost 기반 예측 완료! (최근 데이터 가중치: {weights[-1]:.3f})")
        
        return predictions_df
    
    def _create_prediction_features(self, data: pd.DataFrame, pred_date: datetime, 
                                  feature_cols: List[str]) -> List[float]:
        """예측용 특성을 생성합니다."""
        features = []
        
        # 기본 시간 특성
        day_of_year = pred_date.timetuple().tm_yday
        month = pred_date.month
        day = pred_date.day
        day_of_week = pred_date.weekday()
        quarter = pred_date.quarter
        
        features.extend([
            day_of_year, month, day, day_of_week, quarter,
            np.sin(2 * np.pi * day_of_year / 365.25),
            np.cos(2 * np.pi * day_of_year / 365.25),
            np.sin(2 * np.pi * month / 12),
            np.cos(2 * np.pi * month / 12),
            np.sin(2 * np.pi * day_of_week / 7),
            np.cos(2 * np.pi * day_of_week / 7)
        ])
        
        # 지연 특성 (최근 데이터 사용)
        recent_data = data.tail(14)  # 최근 14일 데이터
        
        if len(recent_data) >= 14:
            features.extend([
                recent_data['temperature'].iloc[-1],  # 1일 전
                recent_data['temperature'].iloc[-2] if len(recent_data) >= 2 else recent_data['temperature'].iloc[-1],  # 2일 전
                recent_data['temperature'].iloc[-3] if len(recent_data) >= 3 else recent_data['temperature'].iloc[-1],  # 3일 전
                recent_data['temperature'].iloc[-5] if len(recent_data) >= 5 else recent_data['temperature'].iloc[-1],  # 5일 전
                recent_data['temperature'].iloc[-7] if len(recent_data) >= 7 else recent_data['temperature'].iloc[-1],  # 7일 전
                recent_data['temperature'].iloc[-10] if len(recent_data) >= 10 else recent_data['temperature'].iloc[-1],  # 10일 전
                recent_data['temperature'].iloc[-14] if len(recent_data) >= 14 else recent_data['temperature'].iloc[-1],  # 14일 전
                recent_data['humidity'].iloc[-1],  # 1일 전
                recent_data['humidity'].iloc[-2] if len(recent_data) >= 2 else recent_data['humidity'].iloc[-1],  # 2일 전
                recent_data['humidity'].iloc[-3] if len(recent_data) >= 3 else recent_data['humidity'].iloc[-1],  # 3일 전
                recent_data['humidity'].iloc[-5] if len(recent_data) >= 5 else recent_data['humidity'].iloc[-1],  # 5일 전
                recent_data['humidity'].iloc[-7] if len(recent_data) >= 7 else recent_data['humidity'].iloc[-1],  # 7일 전
                recent_data['humidity'].iloc[-10] if len(recent_data) >= 10 else recent_data['humidity'].iloc[-1],  # 10일 전
                recent_data['humidity'].iloc[-14] if len(recent_data) >= 14 else recent_data['humidity'].iloc[-1],  # 14일 전
            ])
        else:
            # 데이터가 부족한 경우 평균값 사용
            avg_temp = data['temperature'].mean()
            avg_humidity = data['humidity'].mean()
            features.extend([avg_temp] * 14 + [avg_humidity] * 14)
        
        # 이동평균 특성
        features.extend([
            data['temp_ma_3'].iloc[-1] if 'temp_ma_3' in data.columns else data['temperature'].mean(),
            data['temp_ma_5'].iloc[-1] if 'temp_ma_5' in data.columns else data['temperature'].mean(),
            data['temp_ma_7'].iloc[-1] if 'temp_ma_7' in data.columns else data['temperature'].mean(),
            data['temp_ma_10'].iloc[-1] if 'temp_ma_10' in data.columns else data['temperature'].mean(),
            data['temp_ma_14'].iloc[-1] if 'temp_ma_14' in data.columns else data['temperature'].mean(),
            data['temp_ma_21'].iloc[-1] if 'temp_ma_21' in data.columns else data['temperature'].mean(),
            data['humidity_ma_3'].iloc[-1] if 'humidity_ma_3' in data.columns else data['humidity'].mean(),
            data['humidity_ma_5'].iloc[-1] if 'humidity_ma_5' in data.columns else data['humidity'].mean(),
            data['humidity_ma_7'].iloc[-1] if 'humidity_ma_7' in data.columns else data['humidity'].mean(),
            data['humidity_ma_10'].iloc[-1] if 'humidity_ma_10' in data.columns else data['humidity'].mean(),
            data['humidity_ma_14'].iloc[-1] if 'humidity_ma_14' in data.columns else data['humidity'].mean(),
            data['humidity_ma_21'].iloc[-1] if 'humidity_ma_21' in data.columns else data['humidity'].mean(),
        ])
        
        # 중앙값 특성
        features.extend([
            data['temp_median_3'].iloc[-1] if 'temp_median_3' in data.columns else data['temperature'].median(),
            data['temp_median_7'].iloc[-1] if 'temp_median_7' in data.columns else data['temperature'].median(),
            data['temp_median_14'].iloc[-1] if 'temp_median_14' in data.columns else data['temperature'].median(),
            data['humidity_median_3'].iloc[-1] if 'humidity_median_3' in data.columns else data['humidity'].median(),
            data['humidity_median_7'].iloc[-1] if 'humidity_median_7' in data.columns else data['humidity'].median(),
            data['humidity_median_14'].iloc[-1] if 'humidity_median_14' in data.columns else data['humidity'].median(),
        ])
        
        # 변동성 특성
        features.extend([
            data['temp_std_3'].iloc[-1] if 'temp_std_3' in data.columns else data['temperature'].std(),
            data['temp_std_7'].iloc[-1] if 'temp_std_7' in data.columns else data['temperature'].std(),
            data['temp_std_14'].iloc[-1] if 'temp_std_14' in data.columns else data['temperature'].std(),
            data['humidity_std_3'].iloc[-1] if 'humidity_std_3' in data.columns else data['humidity'].std(),
            data['humidity_std_7'].iloc[-1] if 'humidity_std_7' in data.columns else data['humidity'].std(),
            data['humidity_std_14'].iloc[-1] if 'humidity_std_14' in data.columns else data['humidity'].std(),
        ])
        
        # 범위 특성
        features.extend([
            data['temp_range_3'].iloc[-1] if 'temp_range_3' in data.columns else data['temperature'].max() - data['temperature'].min(),
            data['temp_range_7'].iloc[-1] if 'temp_range_7' in data.columns else data['temperature'].max() - data['temperature'].min(),
            data['temp_range_14'].iloc[-1] if 'temp_range_14' in data.columns else data['temperature'].max() - data['temperature'].min(),
            data['humidity_range_3'].iloc[-1] if 'humidity_range_3' in data.columns else data['humidity'].max() - data['humidity'].min(),
            data['humidity_range_7'].iloc[-1] if 'humidity_range_7' in data.columns else data['humidity'].max() - data['humidity'].min(),
            data['humidity_range_14'].iloc[-1] if 'humidity_range_14' in data.columns else data['humidity'].max() - data['humidity'].min(),
        ])
        
        # 변화율 특성
        features.extend([
            data['temp_change_1d'].iloc[-1] if 'temp_change_1d' in data.columns else data['temperature'].diff(1).iloc[-1],
            data['temp_change_3d'].iloc[-1] if 'temp_change_3d' in data.columns else data['temperature'].diff(3).iloc[-1],
            data['humidity_change_1d'].iloc[-1] if 'humidity_change_1d' in data.columns else data['humidity'].diff(1).iloc[-1],
            data['humidity_change_3d'].iloc[-1] if 'humidity_change_3d' in data.columns else data['humidity'].diff(3).iloc[-1],
        ])
        
        # 상대적 위치 특성
        features.extend([
            data['temp_rank_7'].iloc[-1] if 'temp_rank_7' in data.columns else data['temperature'].rolling(window=7, min_periods=1).rank(pct=True).iloc[-1],
            data['temp_rank_14'].iloc[-1] if 'temp_rank_14' in data.columns else data['temperature'].rolling(window=14, min_periods=1).rank(pct=True).iloc[-1],
            data['temp_rank_30'].iloc[-1] if 'temp_rank_30' in data.columns else data['temperature'].rolling(window=30, min_periods=1).rank(pct=True).iloc[-1],
            data['humidity_rank_7'].iloc[-1] if 'humidity_rank_7' in data.columns else data['humidity'].rolling(window=7, min_periods=1).rank(pct=True).iloc[-1],
            data['humidity_rank_14'].iloc[-1] if 'humidity_rank_14' in data.columns else data['humidity'].rolling(window=14, min_periods=1).rank(pct=True).iloc[-1],
            data['humidity_rank_30'].iloc[-1] if 'humidity_rank_30' in data.columns else data['humidity'].rolling(window=30, min_periods=1).rank(pct=True).iloc[-1],
        ])
        
        # 온습도 상호작용 특성
        features.extend([
            data['temp_humidity_interaction'].iloc[-1] if 'temp_humidity_interaction' in data.columns else data['temperature'].iloc[-1] * data['humidity'].iloc[-1] / 100,
            data['temp_humidity_ratio'].iloc[-1] if 'temp_humidity_ratio' in data.columns else data['temperature'].iloc[-1] / (data['humidity'].iloc[-1] + 1),
        ])
        
        # 추세 특성
        features.extend([
            data['temp_trend_7'].iloc[-1] if 'temp_trend_7' in data.columns else data['temperature'].rolling(window=7, min_periods=1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0),
            data['temp_trend_14'].iloc[-1] if 'temp_trend_14' in data.columns else data['temperature'].rolling(window=14, min_periods=1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0),
            data['humidity_trend_7'].iloc[-1] if 'humidity_trend_7' in data.columns else data['humidity'].rolling(window=7, min_periods=1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0),
            data['humidity_trend_14'].iloc[-1] if 'humidity_trend_14' in data.columns else data['humidity'].rolling(window=14, min_periods=1).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) > 1 else 0),
        ])
        
        return features
    
    def _visualize_weights(self, weights: np.ndarray, dates: pd.Series):
        """시간 가중치를 시각화합니다."""
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=weights,
            mode='lines+markers',
            name='시간 가중치',
            line=dict(color='red', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="⏰ 시간 가중치 분포 (최근 데이터일수록 높은 가중치)",
            xaxis_title="날짜",
            yaxis_title="가중치",
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 가중치 통계 정보
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("최신 데이터 가중치", f"{weights[-1]:.3f}")
        with col2:
            st.metric("최고 가중치", f"{weights.max():.3f}")
        with col3:
            st.metric("평균 가중치", f"{weights.mean():.3f}")
        with col4:
            st.metric("가중치 표준편차", f"{weights.std():.3f}")
    
    def _evaluate_model_performance(self, data: pd.DataFrame, feature_cols: List[str]):
        """예측 성능을 평가합니다."""
        if not self.is_trained:
            return
        
        # 간단한 성능 평가 (교차 검증 대신)
        X = data[feature_cols].values
        y_temp = data['temperature'].values
        y_humidity = data['humidity'].values
        
        # 스케일링 적용
        X_scaled = self.scaler.transform(X)
        
        # 기온 모델 성능
        temp_pred = self.temp_model.predict(X_scaled)
        temp_r2 = r2_score(y_temp, temp_pred)
        temp_mae = mean_absolute_error(y_temp, temp_pred)
        
        # 습도 모델 성능
        humidity_pred = self.humidity_model.predict(X_scaled)
        humidity_r2 = r2_score(y_humidity, humidity_pred)
        humidity_mae = mean_absolute_error(y_humidity, humidity_pred)
        
        # 성능 표시
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("기온 예측 R²", f"{temp_r2:.3f}")
            st.caption(f"MAE: {temp_mae:.2f}°C")
        
        with col2:
            st.metric("습도 예측 R²", f"{humidity_r2:.3f}")
            st.caption(f"MAE: {humidity_mae:.2f}%") 

    def _visualize_feature_importance(self):
        """특성 중요도를 시각화합니다."""
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # 기온 모델 중요도
        fig.add_trace(go.Bar(
            x=list(self.feature_importance['temperature'].keys()),
            y=list(self.feature_importance['temperature'].values()),
            name='기온 예측 특성 중요도',
            marker_color='blue'
        ))
        
        # 습도 모델 중요도
        fig.add_trace(go.Bar(
            x=list(self.feature_importance['humidity'].keys()),
            y=list(self.feature_importance['humidity'].values()),
            name='습도 예측 특성 중요도',
            marker_color='green'
        ))
        
        fig.update_layout(
            title="🔍 특성 중요도 (XGBoost)",
            xaxis_title="특성",
            yaxis_title="중요도",
            barmode='group',
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True) 