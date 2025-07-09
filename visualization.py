"""
시각화 모듈
Plotly를 사용한 차트와 그래프 생성 기능을 담당합니다.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import streamlit as st


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
    
    def create_seasonal_analysis_chart(self, data: pd.DataFrame, title: str = "계절별 분석") -> go.Figure:
        """계절별 기상 데이터 분석 차트를 생성합니다."""
        
        if data.empty:
            return go.Figure()
        
        # 계절별 평균 계산
        seasonal_avg = data.groupby('season').agg({
            'temperature': 'mean',
            'humidity': 'mean'
        }).reset_index()
        
        # 서브플롯 생성
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('계절별 평균 기온', '계절별 평균 습도'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # 계절별 색상
        season_colors = [self.colors[season] for season in seasonal_avg['season']]
        
        # 기온 차트
        fig.add_trace(
            go.Bar(
                x=seasonal_avg['season'],
                y=seasonal_avg['temperature'],
                name='평균 기온',
                marker_color=season_colors,
                hovertemplate='<b>계절:</b> %{x}<br>' +
                            '<b>평균 기온:</b> %{y:.1f}°C<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 습도 차트
        fig.add_trace(
            go.Bar(
                x=seasonal_avg['season'],
                y=seasonal_avg['humidity'],
                name='평균 습도',
                marker_color=season_colors,
                hovertemplate='<b>계절:</b> %{x}<br>' +
                            '<b>평균 습도:</b> %{y:.1f}%<extra></extra>'
            ),
            row=1, col=2
        )
        
        # 레이아웃 설정
        fig.update_layout(
            title=title,
            height=400,
            showlegend=False
        )
        
        # Y축 설정
        fig.update_yaxes(title_text="기온 (°C)", row=1, col=1)
        fig.update_yaxes(title_text="습도 (%)", row=1, col=2)
        
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
    
    def create_weather_scatter_plot(self, data: pd.DataFrame, title: str = "기온-습도 산점도") -> go.Figure:
        """기온과 습도의 산점도를 생성합니다."""
        
        if data.empty:
            return go.Figure()
        
        # 계절별 색상 매핑
        season_colors = {
            "봄": self.colors['spring'],
            "여름": self.colors['summer'],
            "가을": self.colors['autumn'],
            "겨울": self.colors['winter']
        }
        
        fig = go.Figure()
        
        # 계절별로 산점도 추가
        for season in data['season'].unique():
            season_data = data[data['season'] == season]
            
            fig.add_trace(
                go.Scatter(
                    x=season_data['temperature'],
                    y=season_data['humidity'],
                    mode='markers',
                    name=season,
                    marker=dict(
                        size=6,
                        color=season_colors[season],
                        opacity=0.7
                    ),
                    hovertemplate='<b>계절:</b> ' + season + '<br>' +
                                '<b>기온:</b> %{x:.1f}°C<br>' +
                                '<b>습도:</b> %{y:.1f}%<extra></extra>'
                )
            )
        
        # 레이아웃 설정
        fig.update_layout(
            title=title,
            xaxis_title="기온 (°C)",
            yaxis_title="습도 (%)",
            height=500,
            hovermode='closest'
        )
        
        return fig
    
    def create_summary_metrics(self, weather_data: dict, mortality_result: dict) -> str:
        """요약 메트릭을 생성합니다."""
        
        if not weather_data or not mortality_result:
            return "데이터가 없습니다."
        
        summary = f"""
        ## 📊 분석 결과 요약
        
        ### 🌡️ 기상 정보
        - **지역**: {weather_data['city']}
        - **날짜**: {weather_data['date'].strftime('%Y년 %m월 %d일')}
        - **기온**: {weather_data['temperature']:.1f}°C
        - **습도**: {weather_data['humidity']:.1f}%
        - **계절**: {weather_data['season']}
        - **데이터 유형**: {'예측' if weather_data.get('is_prediction', False) else '실제'}
        
        ### 💀 사망률 예측
        - **예상 사망률**: {mortality_result['mortality_rate']} (10만명당)
        - **95% 신뢰구간**: {mortality_result['lower_bound']} ~ {mortality_result['upper_bound']}
        - **위험 수준**: {mortality_result['risk_level']}
        
        ### ⚠️ 주요 위험 요인
        - **온도 위험도**: {mortality_result['risk_factors']['temperature_risk']}
        - **습도 위험도**: {mortality_result['risk_factors']['humidity_risk']}
        - **계절 위험도**: {mortality_result['risk_factors']['seasonal_risk']}
        - **지역 위험도**: {mortality_result['risk_factors']['regional_risk']}
        """
        
        return summary 