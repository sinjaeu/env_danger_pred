"""
시각화 모듈
Plotly를 사용한 차트와 그래프 생성 기능을 담당합니다.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st
import numpy as np


class WeatherVisualizer:
    """기상 데이터 시각화 클래스"""
    
    def __init__(self):
        # 색상 팔레트
        self.colors = {
            'temperature': '#FF6B6B',
            'humidity': '#4ECDC4',
            'mortality': '#45B7D1',
            'spring': '#FFD93D',
            'summer': '#6BCF7F',
            'autumn': '#FF8C42',
            'winter': '#4A90E2'
        }
    
    def create_weather_trend_chart(self, data: pd.DataFrame, title: str = "기상 트렌드") -> go.Figure:
        """기온과 습도 트렌드 차트를 생성합니다."""
        
        if data.empty:
            return go.Figure()
        
        # 서브플롯 생성
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('기온 (°C)', '습도 (%)'),
            vertical_spacing=0.1,
            shared_xaxes=True
        )
        
        # 기온 차트
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['temperature'],
                mode='lines+markers',
                name='기온',
                line=dict(color=self.colors['temperature'], width=2),
                marker=dict(size=4)
            ),
            row=1, col=1
        )
        
        # 습도 차트
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['humidity'],
                mode='lines+markers',
                name='습도',
                line=dict(color=self.colors['humidity'], width=2),
                marker=dict(size=4)
            ),
            row=2, col=1
        )
        
        # 레이아웃 설정
        fig.update_layout(
            title=title,
            height=600,
            showlegend=False,
            hovermode='x unified'
        )
        
        # Y축 설정
        fig.update_yaxes(title_text="기온 (°C)", row=1, col=1)
        fig.update_yaxes(title_text="습도 (%)", row=2, col=1)
        
        # X축 설정
        fig.update_xaxes(title_text="날짜", row=2, col=1)
        
        return fig
    
    def create_mortality_chart(self, data: pd.DataFrame, title: str = "사망률 예측") -> go.Figure:
        """사망률 예측 차트를 생성합니다."""
        
        if data.empty:
            return go.Figure()
        
        # 위험 수준별 색상 매핑
        risk_colors = {
            "낮음": "#2ECC71",
            "보통": "#F39C12",
            "높음": "#E67E22",
            "매우 높음": "#E74C3C"
        }
        
        # 색상 배열 생성
        colors = [risk_colors.get(level, "#95A5A6") for level in data['risk_level']]
        
        fig = go.Figure()
        
        # 사망률 선 차트
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['mortality_rate'],
                mode='lines+markers',
                name='사망률',
                line=dict(color=self.colors['mortality'], width=3),
                marker=dict(
                    size=8,
                    color=colors,
                    line=dict(width=1, color='white')
                ),
                hovertemplate='<b>날짜:</b> %{x}<br>' +
                            '<b>사망률:</b> %{y:.2f} (10만명당)<br>' +
                            '<b>위험수준:</b> %{customdata}<br>' +
                            '<extra></extra>',
                customdata=data['risk_level']
            )
        )
        
        # 레이아웃 설정
        fig.update_layout(
            title=title,
            xaxis_title="날짜",
            yaxis_title="사망률 (10만명당)",
            height=500,
            hovermode='x unified',
            yaxis=dict(
                gridcolor='lightgray',
                zeroline=False
            ),
            xaxis=dict(
                gridcolor='lightgray',
                zeroline=False
            )
        )
        
        return fig
    
    def create_risk_factors_chart(self, risk_factors: dict, title: str = "위험도 분석") -> go.Figure:
        """위험도 요인 분석 차트를 생성합니다."""
        
        # 위험도 요인 데이터 준비
        factors = list(risk_factors.keys())
        values = list(risk_factors.values())
        
        # 색상 설정 (1.0 기준으로 색상 구분)
        colors = ['#E74C3C' if v > 1.0 else '#2ECC71' if v < 1.0 else '#F39C12' for v in values]
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Bar(
                x=factors,
                y=values,
                marker_color=colors,
                hovertemplate='<b>요인:</b> %{x}<br>' +
                            '<b>위험도:</b> %{y:.3f}<extra></extra>'
            )
        )
        
        # 기준선 추가
        fig.add_hline(
            y=1.0,
            line_dash="dash",
            line_color="gray",
            annotation_text="기준선 (1.0)",
            annotation_position="top right"
        )
        
        # 레이아웃 설정
        fig.update_layout(
            title=title,
            xaxis_title="위험도 요인",
            yaxis_title="위험도 배수",
            height=400,
            yaxis=dict(
                gridcolor='lightgray',
                zeroline=False
            ),
            xaxis=dict(
                gridcolor='lightgray',
                zeroline=False
            )
        )
        
        return fig
    
    def create_weather_scatter_plot(self, data: pd.DataFrame, title: str) -> go.Figure:
        """기온-습도 산점도를 생성합니다."""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['temperature'],
            y=data['humidity'],
                    mode='markers',
            name='기상 데이터',
                    marker=dict(
                color='#636EFA',
                size=8,
                        opacity=0.7
                    ),
            hovertemplate='<b>%{text}</b><br>' +
                        '기온: %{x:.1f}°C<br>' +
                        '습도: %{y:.1f}%<br>' +
                        '<extra></extra>',
            text=data['date'].dt.strftime('%m-%d')
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="기온 (°C)",
            yaxis_title="습도 (%)",
            hovermode='closest',
            showlegend=True,
            height=500
        )
        
        return fig
    
    def create_summary_metrics(self, weather_data: dict, mortality_result: dict) -> str:
        """요약 메트릭을 생성합니다."""
        
        summary = f"""
        ## 📋 예측 결과 요약
        
        ### 🌤️ 기상 정보
        - **날짜**: {weather_data['date'].strftime('%Y년 %m월 %d일')}
        - **지역**: {weather_data['city']}
        - **예측 기온**: {weather_data['temperature']:.1f}°C
        - **예측 습도**: {weather_data['humidity']:.1f}%
        - **월**: {weather_data['date'].month}월
        
        ### 💀 사망률 예측
        - **예상 사망률**: {mortality_result['mortality_rate']} (10만명당)
        - **위험 수준**: {mortality_result['risk_level']}
        - **신뢰구간**: {mortality_result['lower_bound']} ~ {mortality_result['upper_bound']}
        
        ### ⚠️ 주요 위험 요인
        """
        
        # 위험 요인 추가
        risk_factors = mortality_result.get('risk_factors', {})
        for factor, value in risk_factors.items():
            summary += f"- **{factor}**: {value:.1f}%\n"
        
        return summary 

    def create_30day_pattern_chart(self, data: pd.DataFrame, title: str = "30일 패턴 분석") -> go.Figure:
        """30일 데이터 패턴 분석 차트를 생성합니다."""
        
        if data.empty:
            return go.Figure()
        
        # 서브플롯 생성 (계절별 분포 제거하여 5개로 변경)
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=('기온 트렌드', '습도 트렌드', '기온 변동성', '습도 변동성', '기온-습도 관계'),
            vertical_spacing=0.1,
            horizontal_spacing=0.1,
            specs=[[{"type": "scatter"}, {"type": "scatter"}],
                   [{"type": "scatter"}, {"type": "scatter"}],
                   [{"type": "scatter"}, {"type": "scatter"}]]
        )
        
        # 1. 기온 트렌드
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['temperature'],
                mode='lines+markers',
                name='기온',
                line=dict(color=self.colors['temperature'], width=2),
                marker=dict(size=6),
                hovertemplate='<b>날짜:</b> %{x}<br><b>기온:</b> %{y:.1f}°C<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. 습도 트렌드
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['humidity'],
                mode='lines+markers',
                name='습도',
                line=dict(color=self.colors['humidity'], width=2),
                marker=dict(size=6),
                hovertemplate='<b>날짜:</b> %{x}<br><b>습도:</b> %{y:.1f}%<extra></extra>'
            ),
            row=1, col=2
        )
        
        # 3. 기온 변동성 (이동 표준편차)
        temp_std = data['temperature'].rolling(window=3, center=True).std()
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=temp_std,
                mode='lines',
                name='기온 변동성',
                line=dict(color='orange', width=2),
                hovertemplate='<b>날짜:</b> %{x}<br><b>변동성:</b> %{y:.2f}°C<extra></extra>'
            ),
            row=2, col=1
        )
        
        # 4. 습도 변동성 (이동 표준편차)
        humidity_std = data['humidity'].rolling(window=3, center=True).std()
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=humidity_std,
                mode='lines',
                name='습도 변동성',
                line=dict(color='purple', width=2),
                hovertemplate='<b>날짜:</b> %{x}<br><b>변동성:</b> %{y:.2f}%<extra></extra>'
            ),
            row=2, col=2
        )
        
        # 5. 기온-습도 산점도
        fig.add_trace(
            go.Scatter(
                x=data['temperature'],
                y=data['humidity'],
                mode='markers',
                name='기온-습도 관계',
                marker=dict(
                    size=8,
                    color=data['date'].dt.day,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="일")
                ),
                hovertemplate='<b>기온:</b> %{x:.1f}°C<br><b>습도:</b> %{y:.1f}%<extra></extra>'
            ),
            row=3, col=1
        )
        
        # 6. 일별 변화율
        temp_change = data['temperature'].pct_change() * 100
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=temp_change,
                mode='lines+markers',
                name='기온 변화율',
                line=dict(color='red', width=2),
                marker=dict(size=4),
                hovertemplate='<b>날짜:</b> %{x}<br><b>변화율:</b> %{y:.1f}%<extra></extra>'
            ),
            row=3, col=2
        )
        
        # 레이아웃 설정
        fig.update_layout(
            title=title,
            height=800,
            showlegend=False,
            hovermode='x unified'
        )
        
        # Y축 제목 설정
        fig.update_yaxes(title_text="기온 (°C)", row=1, col=1)
        fig.update_yaxes(title_text="습도 (%)", row=1, col=2)
        fig.update_yaxes(title_text="변동성 (°C)", row=2, col=1)
        fig.update_yaxes(title_text="변동성 (%)", row=2, col=2)
        fig.update_yaxes(title_text="습도 (%)", row=3, col=1)
        fig.update_yaxes(title_text="변화율 (%)", row=3, col=2)
        
        # X축 제목 설정
        fig.update_xaxes(title_text="기온 (°C)", row=3, col=1)
        
        return fig

    def create_outlier_analysis_chart(self, data: pd.DataFrame, title: str = "이상치 분석") -> go.Figure:
        """이상치 분석 차트를 생성합니다."""
        
        if data.empty:
            return go.Figure()
        
        # 서브플롯 생성
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('기온 이상치', '습도 이상치', '기온 박스플롯', '습도 박스플롯'),
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 이상치 탐지 함수
        def detect_outliers(series, threshold=2.0):
            mean = series.mean()
            std = series.std()
            z_scores = abs((series - mean) / std)
            return z_scores > threshold
        
        # 기온 이상치
        temp_outliers = detect_outliers(data['temperature'])
        temp_normal = ~temp_outliers
        
        # 정상 데이터
        fig.add_trace(
            go.Scatter(
                x=data[temp_normal]['date'],
                y=data[temp_normal]['temperature'],
                mode='markers',
                name='정상 기온',
                marker=dict(color='blue', size=6),
                hovertemplate='<b>날짜:</b> %{x}<br><b>기온:</b> %{y:.1f}°C<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 이상치
        if temp_outliers.any():
            fig.add_trace(
                go.Scatter(
                    x=data[temp_outliers]['date'],
                    y=data[temp_outliers]['temperature'],
                    mode='markers',
                    name='기온 이상치',
                    marker=dict(color='red', size=10, symbol='x'),
                    hovertemplate='<b>날짜:</b> %{x}<br><b>기온:</b> %{y:.1f}°C (이상치)<extra></extra>'
                ),
                row=1, col=1
            )
        
        # 습도 이상치
        humidity_outliers = detect_outliers(data['humidity'])
        humidity_normal = ~humidity_outliers
        
        # 정상 데이터
        fig.add_trace(
            go.Scatter(
                x=data[humidity_normal]['date'],
                y=data[humidity_normal]['humidity'],
                mode='markers',
                name='정상 습도',
                marker=dict(color='green', size=6),
                hovertemplate='<b>날짜:</b> %{x}<br><b>습도:</b> %{y:.1f}%<extra></extra>'
            ),
            row=1, col=2
        )
        
        # 이상치
        if humidity_outliers.any():
            fig.add_trace(
                go.Scatter(
                    x=data[humidity_outliers]['date'],
                    y=data[humidity_outliers]['humidity'],
                    mode='markers',
                    name='습도 이상치',
                    marker=dict(color='red', size=10, symbol='x'),
                    hovertemplate='<b>날짜:</b> %{x}<br><b>습도:</b> %{y:.1f}% (이상치)<extra></extra>'
                ),
                row=1, col=2
            )
        
        # 기온 박스플롯
        fig.add_trace(
            go.Box(
                y=data['temperature'],
                name='기온',
                marker_color=self.colors['temperature'],
                hovertemplate='<b>기온:</b> %{y:.1f}°C<extra></extra>'
            ),
            row=2, col=1
        )
        
        # 습도 박스플롯
        fig.add_trace(
            go.Box(
                y=data['humidity'],
                name='습도',
                marker_color=self.colors['humidity'],
                hovertemplate='<b>습도:</b> %{y:.1f}%<extra></extra>'
            ),
            row=2, col=2
        )
        
        # 레이아웃 설정
        fig.update_layout(
            title=title,
            height=600,
            showlegend=False,
            hovermode='x unified'
        )
        
        # Y축 제목 설정
        fig.update_yaxes(title_text="기온 (°C)", row=1, col=1)
        fig.update_yaxes(title_text="습도 (%)", row=1, col=2)
        fig.update_yaxes(title_text="기온 (°C)", row=2, col=1)
        fig.update_yaxes(title_text="습도 (%)", row=2, col=2)
        
        return fig

    def create_trend_analysis_chart(self, data: pd.DataFrame, title: str = "트렌드 분석") -> go.Figure:
        """트렌드 분석 차트를 생성합니다."""
        
        if data.empty:
            return go.Figure()
        
        # 서브플롯 생성
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('기온 트렌드', '습도 트렌드', '기온 변화율', '습도 변화율'),
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 1. 기온 트렌드 (선형 회귀)
        x_numeric = list(range(len(data)))
        z_temp = np.polyfit(x_numeric, data['temperature'], 1)
        p_temp = np.poly1d(z_temp)
        
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['temperature'],
                mode='markers',
                name='실제 기온',
                marker=dict(color=self.colors['temperature'], size=6),
                hovertemplate='<b>날짜:</b> %{x}<br><b>기온:</b> %{y:.1f}°C<extra></extra>'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=p_temp(x_numeric),
                mode='lines',
                name='트렌드선',
                line=dict(color='red', width=3),
                hovertemplate='<b>날짜:</b> %{x}<br><b>트렌드:</b> %{y:.1f}°C<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. 습도 트렌드
        z_humidity = np.polyfit(x_numeric, data['humidity'], 1)
        p_humidity = np.poly1d(z_humidity)
        
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['humidity'],
                mode='markers',
                name='실제 습도',
                marker=dict(color=self.colors['humidity'], size=6),
                hovertemplate='<b>날짜:</b> %{x}<br><b>습도:</b> %{y:.1f}%<extra></extra>'
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=p_humidity(x_numeric),
                mode='lines',
                name='트렌드선',
                line=dict(color='blue', width=3),
                hovertemplate='<b>날짜:</b> %{x}<br><b>트렌드:</b> %{y:.1f}%<extra></extra>'
            ),
            row=1, col=2
        )
        
        # 3. 기온 변화율
        temp_change = data['temperature'].pct_change() * 100
        fig.add_trace(
            go.Bar(
                x=data['date'],
                y=temp_change,
                name='기온 변화율',
                marker_color='orange',
                hovertemplate='<b>날짜:</b> %{x}<br><b>변화율:</b> %{y:.1f}%<extra></extra>'
            ),
            row=2, col=1
        )
        
        # 4. 습도 변화율
        humidity_change = data['humidity'].pct_change() * 100
        fig.add_trace(
            go.Bar(
                x=data['date'],
                y=humidity_change,
                name='습도 변화율',
                marker_color='purple',
                hovertemplate='<b>날짜:</b> %{x}<br><b>변화율:</b> %{y:.1f}%<extra></extra>'
            ),
            row=2, col=2
        )
        
        # 레이아웃 설정
        fig.update_layout(
            title=title,
            height=600,
            showlegend=False,
            hovermode='x unified'
        )
        
        # Y축 제목 설정
        fig.update_yaxes(title_text="기온 (°C)", row=1, col=1)
        fig.update_yaxes(title_text="습도 (%)", row=1, col=2)
        fig.update_yaxes(title_text="변화율 (%)", row=2, col=1)
        fig.update_yaxes(title_text="변화율 (%)", row=2, col=2)
        
        return fig 