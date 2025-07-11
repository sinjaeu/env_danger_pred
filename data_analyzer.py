"""
30일 데이터 분석 모듈
최근 30일 기상 데이터의 분석, 패턴 탐지, 통계 계산 기능을 담당합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from typing import Dict, List, Tuple, Optional


class DataAnalyzer:
    """30일 데이터 분석 클래스"""
    
    def __init__(self):
        self.analysis_cache = {}
    
    def analyze_30day_data(self, data: pd.DataFrame) -> Dict:
        """30일 데이터의 종합 분석을 수행합니다."""
        if data.empty:
            return {}
        
        analysis = {
            'basic_info': self._get_basic_info(data),
            'temperature_analysis': self._analyze_temperature(data),
            'humidity_analysis': self._analyze_humidity(data),
            'monthly_analysis': self._analyze_monthly_patterns(data),
            'outlier_analysis': self._detect_outliers(data),
            'trend_analysis': self._analyze_trends(data),
            'correlation_analysis': self._analyze_correlations(data),
            'volatility_analysis': self._analyze_volatility(data)
        }
        
        return analysis
    
    def _get_basic_info(self, data: pd.DataFrame) -> Dict:
        """기본 정보를 추출합니다."""
        return {
            'total_days': len(data),
            'date_range': f"{data['date'].min().strftime('%Y-%m-%d')} ~ {data['date'].max().strftime('%Y-%m-%d')}",
            'days_covered': (data['date'].max() - data['date'].min()).days + 1,
            'data_completeness': len(data) / 30 * 100,  # 30일 기준 완성도
            'latest_date': data['date'].max().strftime('%Y-%m-%d'),
            'earliest_date': data['date'].min().strftime('%Y-%m-%d')
        }
    
    def _analyze_temperature(self, data: pd.DataFrame) -> Dict:
        """기온 데이터를 분석합니다."""
        temp_data = data['temperature'].dropna()
        
        if len(temp_data) == 0:
            return {
                'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0,
                'q25': 0, 'q75': 0, 'range': 0, 'trend_slope': 0,
                'trend_direction': '안정', 'trend_strength': '약함', 'volatility': 0
            }
        
        # 기본 통계
        stats = temp_data.describe()
        
        # 트렌드 분석
        x_numeric = list(range(len(temp_data)))
        if len(temp_data) > 1:
            slope = np.polyfit(x_numeric, temp_data, 1)[0]
            trend_direction = '상승' if slope > 0.1 else '하락' if slope < -0.1 else '안정'
            trend_strength = '강함' if abs(slope) > 0.5 else '보통' if abs(slope) > 0.2 else '약함'
        else:
            slope = 0
            trend_direction = '안정'
            trend_strength = '약함'
        
        # 변동성 계산 (안전장치 추가)
        temp_mean = temp_data.mean()
        temp_std = temp_data.std()
        volatility = round(temp_std / temp_mean * 100, 1) if temp_mean != 0 and not np.isnan(temp_mean) else 0
        
        return {
            'mean': round(temp_data.mean(), 1),
            'std': round(temp_data.std(), 1),
            'min': round(temp_data.min(), 1),
            'max': round(temp_data.max(), 1),
            'median': round(temp_data.median(), 1),
            'q25': round(stats['25%'], 1),
            'q75': round(stats['75%'], 1),
            'range': round(temp_data.max() - temp_data.min(), 1),
            'trend_slope': round(slope, 3),
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'volatility': volatility
        }
    
    def _analyze_humidity(self, data: pd.DataFrame) -> Dict:
        """습도 데이터를 분석합니다."""
        humidity_data = data['humidity'].dropna()
        
        if len(humidity_data) == 0:
            return {
                'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0,
                'q25': 0, 'q75': 0, 'range': 0, 'trend_slope': 0,
                'trend_direction': '안정', 'trend_strength': '약함', 'volatility': 0
            }
        
        # 기본 통계
        stats = humidity_data.describe()
        
        # 트렌드 분석
        x_numeric = list(range(len(humidity_data)))
        if len(humidity_data) > 1:
            slope = np.polyfit(x_numeric, humidity_data, 1)[0]
            trend_direction = '상승' if slope > 0.5 else '하락' if slope < -0.5 else '안정'
            trend_strength = '강함' if abs(slope) > 2.0 else '보통' if abs(slope) > 1.0 else '약함'
        else:
            slope = 0
            trend_direction = '안정'
            trend_strength = '약함'
        
        # 변동성 계산 (안전장치 추가)
        humidity_mean = humidity_data.mean()
        humidity_std = humidity_data.std()
        volatility = round(humidity_std / humidity_mean * 100, 1) if humidity_mean != 0 and not np.isnan(humidity_mean) else 0
        
        return {
            'mean': round(humidity_data.mean(), 1),
            'std': round(humidity_data.std(), 1),
            'min': round(humidity_data.min(), 1),
            'max': round(humidity_data.max(), 1),
            'median': round(humidity_data.median(), 1),
            'q25': round(stats['25%'], 1),
            'q75': round(stats['75%'], 1),
            'range': round(humidity_data.max() - humidity_data.min(), 1),
            'trend_slope': round(slope, 3),
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'volatility': volatility
        }
    
    def _analyze_monthly_patterns(self, data: pd.DataFrame) -> Dict:
        """월별 패턴을 분석합니다."""
        month_counts = data['month'].value_counts()
        month_stats = {}
        
        for month in data['month'].unique():
            month_data = data[data['month'] == month]
            month_stats[month] = {
                'count': len(month_data),
                'percentage': round(len(month_data) / len(data) * 100, 1),
                'temp_mean': round(month_data['temperature'].mean(), 1),
                'humidity_mean': round(month_data['humidity'].mean(), 1),
                'temp_std': round(month_data['temperature'].std(), 1),
                'humidity_std': round(month_data['humidity'].std(), 1)
            }
        
        return {
            'primary_month': month_counts.index[0] if len(month_counts) > 0 else '없음',
            'month_distribution': month_counts.to_dict(),
            'month_count': len(month_counts),
            'month_stats': month_stats,
            'most_common_month': month_counts.index[0] if len(month_counts) > 0 else '없음',
            'monthly_variation': round(month_counts.std(), 1) if len(month_counts) > 1 else 0
        }
    
    def _detect_outliers(self, data: pd.DataFrame, threshold: float = 2.0) -> Dict:
        """이상치를 탐지합니다."""
        temp_outliers = self._detect_series_outliers(data['temperature'], threshold)
        humidity_outliers = self._detect_series_outliers(data['humidity'], threshold)
        
        return {
            'temperature_outliers': {
                'count': len(temp_outliers),
                'indices': temp_outliers,
                'values': data.iloc[temp_outliers]['temperature'].tolist() if temp_outliers else [],
                'dates': data.iloc[temp_outliers]['date'].tolist() if temp_outliers else []
            },
            'humidity_outliers': {
                'count': len(humidity_outliers),
                'indices': humidity_outliers,
                'values': data.iloc[humidity_outliers]['humidity'].tolist() if humidity_outliers else [],
                'dates': data.iloc[humidity_outliers]['date'].tolist() if humidity_outliers else []
            },
            'total_outliers': len(temp_outliers) + len(humidity_outliers),
            'outlier_percentage': round((len(temp_outliers) + len(humidity_outliers)) / (len(data) * 2) * 100, 1)
        }
    
    def _detect_series_outliers(self, series: pd.Series, threshold: float = 2.0) -> List[int]:
        """시리즈에서 이상치를 탐지합니다."""
        # NaN 값 제거
        series_clean = series.dropna()
        if len(series_clean) < 2:
            return []
        
        mean = series_clean.mean()
        std = series_clean.std()
        
        # 표준편차가 0이거나 너무 작은 경우 처리
        if std == 0 or np.isnan(std) or std < 1e-10:
            return []
        
        outliers = []
        for i, value in enumerate(series):
            if pd.isna(value):
                continue
            z_score = abs((value - mean) / std)
            if z_score > threshold:
                outliers.append(i)
        
        return outliers
    
    def _analyze_trends(self, data: pd.DataFrame) -> Dict:
        """트렌드 분석을 수행합니다."""
        trends = {}
        
        # 기온 트렌드
        temp_data = data['temperature'].values
        if len(temp_data) > 1:
            temp_slope = np.polyfit(range(len(temp_data)), temp_data, 1)[0]
            temp_r_squared = self._calculate_r_squared(temp_data)
            
            trends['temperature'] = {
                'slope': round(temp_slope, 3),
                'direction': '상승' if temp_slope > 0.1 else '하락' if temp_slope < -0.1 else '안정',
                'strength': '강함' if abs(temp_slope) > 0.5 else '보통' if abs(temp_slope) > 0.2 else '약함',
                'r_squared': round(temp_r_squared, 3),
                'significance': '높음' if temp_r_squared > 0.7 else '보통' if temp_r_squared > 0.3 else '낮음'
            }
        
        # 습도 트렌드
        humidity_data = data['humidity'].values
        if len(humidity_data) > 1:
            humidity_slope = np.polyfit(range(len(humidity_data)), humidity_data, 1)[0]
            humidity_r_squared = self._calculate_r_squared(humidity_data)
            
            trends['humidity'] = {
                'slope': round(humidity_slope, 3),
                'direction': '상승' if humidity_slope > 0.5 else '하락' if humidity_slope < -0.5 else '안정',
                'strength': '강함' if abs(humidity_slope) > 2.0 else '보통' if abs(humidity_slope) > 1.0 else '약함',
                'r_squared': round(humidity_r_squared, 3),
                'significance': '높음' if humidity_r_squared > 0.7 else '보통' if humidity_r_squared > 0.3 else '낮음'
            }
        
        return trends
    
    def _calculate_r_squared(self, data: np.ndarray) -> float:
        """R-squared 값을 계산합니다."""
        if len(data) < 2:
            return 0.0
        
        x = np.arange(len(data))
        slope, intercept = np.polyfit(x, data, 1)
        y_pred = slope * x + intercept
        
        ss_res = np.sum((data - y_pred) ** 2)
        ss_tot = np.sum((data - np.mean(data)) ** 2)
        
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    def _analyze_correlations(self, data: pd.DataFrame) -> Dict:
        """상관관계 분석을 수행합니다."""
        correlations = {}
        
        # 기온-습도 상관관계
        temp_humidity_corr = data['temperature'].corr(data['humidity'])
        correlations['temperature_humidity'] = {
            'correlation': round(temp_humidity_corr, 3),
            'strength': self._interpret_correlation(temp_humidity_corr),
            'direction': '음의 상관관계' if temp_humidity_corr < 0 else '양의 상관관계'
        }
        
        # 시간과의 상관관계
        time_series = list(range(len(data)))
        temp_time_corr = data['temperature'].corr(pd.Series(time_series))
        humidity_time_corr = data['humidity'].corr(pd.Series(time_series))
        
        correlations['time_temperature'] = {
            'correlation': round(temp_time_corr, 3),
            'strength': self._interpret_correlation(temp_time_corr),
            'direction': '음의 상관관계' if temp_time_corr < 0 else '양의 상관관계'
        }
        
        correlations['time_humidity'] = {
            'correlation': round(humidity_time_corr, 3),
            'strength': self._interpret_correlation(humidity_time_corr),
            'direction': '음의 상관관계' if humidity_time_corr < 0 else '양의 상관관계'
        }
        
        return correlations
    
    def _interpret_correlation(self, corr: float) -> str:
        """상관계수를 해석합니다."""
        abs_corr = abs(corr)
        if abs_corr >= 0.7:
            return '강함'
        elif abs_corr >= 0.3:
            return '보통'
        else:
            return '약함'
    
    def _analyze_volatility(self, data: pd.DataFrame) -> Dict:
        """변동성 분석을 수행합니다."""
        volatility = {}
        
        # 기온 변동성
        temp_volatility = data['temperature'].std()
        temp_cv = temp_volatility / data['temperature'].mean() * 100 if data['temperature'].mean() != 0 else 0
        
        volatility['temperature'] = {
            'std': round(temp_volatility, 2),
            'coefficient_of_variation': round(temp_cv, 1),
            'level': '높음' if temp_cv > 30 else '보통' if temp_cv > 15 else '낮음',
            'daily_changes': self._calculate_daily_changes(data['temperature'])
        }
        
        # 습도 변동성
        humidity_volatility = data['humidity'].std()
        humidity_cv = humidity_volatility / data['humidity'].mean() * 100 if data['humidity'].mean() != 0 else 0
        
        volatility['humidity'] = {
            'std': round(humidity_volatility, 2),
            'coefficient_of_variation': round(humidity_cv, 1),
            'level': '높음' if humidity_cv > 25 else '보통' if humidity_cv > 12 else '낮음',
            'daily_changes': self._calculate_daily_changes(data['humidity'])
        }
        
        return volatility
    
    def _calculate_daily_changes(self, series: pd.Series) -> Dict:
        """일별 변화를 계산합니다."""
        changes = series.diff().dropna()
        
        return {
            'mean_change': round(changes.mean(), 2),
            'max_increase': round(changes.max(), 2),
            'max_decrease': round(changes.min(), 2),
            'positive_changes': len(changes[changes > 0]),
            'negative_changes': len(changes[changes < 0]),
            'no_change': len(changes[changes == 0])
        }
    
    def get_summary_statistics(self, data: pd.DataFrame) -> Dict:
        """요약 통계를 계산합니다."""
        if data.empty:
            return {}
        
        return {
            'basic': self._get_basic_info(data),
            'temperature': self._analyze_temperature(data),
            'humidity': self._analyze_humidity(data),
            'months': self._analyze_monthly_patterns(data)
        }
    
    def get_analysis_report(self, data: pd.DataFrame) -> str:
        """분석 리포트를 생성합니다."""
        if data.empty:
            return "분석할 데이터가 없습니다."
        
        analysis = self.analyze_30day_data(data)
        
        report = f"""
        ## 📊 30일 데이터 분석 리포트
        
        ### 📅 기본 정보
        - **분석 기간**: {analysis['basic_info']['date_range']}
        - **총 데이터 수**: {analysis['basic_info']['total_days']}일
        - **데이터 완성도**: {analysis['basic_info']['data_completeness']:.1f}%
        
        ### 🌡️ 기온 분석
        - **평균 기온**: {analysis['temperature_analysis']['mean']}°C
        - **기온 범위**: {analysis['temperature_analysis']['min']}°C ~ {analysis['temperature_analysis']['max']}°C
        - **트렌드**: {analysis['temperature_analysis']['trend_direction']} ({analysis['temperature_analysis']['trend_strength']})
        - **변동성**: {analysis['temperature_analysis']['volatility']}%
        
        ### 💧 습도 분석
        - **평균 습도**: {analysis['humidity_analysis']['mean']}%
        - **습도 범위**: {analysis['humidity_analysis']['min']}% ~ {analysis['humidity_analysis']['max']}%
        - **트렌드**: {analysis['humidity_analysis']['trend_direction']} ({analysis['humidity_analysis']['trend_strength']})
        - **변동성**: {analysis['humidity_analysis']['volatility']}%
        
        ### 📅 월별 분석
        - **주요 월**: {analysis['monthly_analysis']['primary_month']}월
        - **월 수**: {analysis['monthly_analysis']['month_count']}개
        
        ### ⚠️ 이상치 분석
        - **총 이상치 수**: {analysis['outlier_analysis']['total_outliers']}개
        - **이상치 비율**: {analysis['outlier_analysis']['outlier_percentage']}%
        
        ### 📈 상관관계 분석
        - **기온-습도 상관관계**: {analysis['correlation_analysis']['temperature_humidity']['correlation']} ({analysis['correlation_analysis']['temperature_humidity']['strength']})
        """
        
        return report 