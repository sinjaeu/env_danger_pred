"""
UI 컴포넌트 모듈
Streamlit UI 컴포넌트들을 담당합니다.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class UIComponents:
    """UI 컴포넌트 클래스"""
    
    def __init__(self):
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#17a2b8'
        }
    
    def create_sidebar(self, weather_api):
        """사이드바를 생성합니다."""
        with st.sidebar:
            st.header("⚙️ 설정")
            
            # 도시 선택
            cities = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "제주"]
            selected_city = st.selectbox("🏙️ 도시 선택", cities, index=0)
            
            # 연령대 선택
            age_groups = ["20-29세", "30-39세", "40-49세", "50-59세", "60-69세", "70세 이상"]
            selected_age_group = st.selectbox("👥 연령대 선택", age_groups, index=2)
            
            # 성별 선택
            genders = ["남성", "여성"]
            selected_gender = st.selectbox("👤 성별 선택", genders, index=0)
            
            # 예측 날짜 설정
            st.subheader("📅 예측 설정")
            today = datetime.now().date()
            max_date = today + timedelta(days=30)
            prediction_date = st.date_input(
                "🔮 예측 날짜",
                value=today + timedelta(days=7),
                min_value=today + timedelta(days=1),
                max_value=max_date
            )
            
            return {
                'selected_city': selected_city,
                'selected_age_group': selected_age_group,
                'selected_gender': selected_gender,
                'prediction_date': prediction_date
            }
    
    def display_data_info(self, data_info: Dict):
        """데이터 정보를 표시합니다."""
        if not data_info:
            return
        
        st.subheader("📊 데이터 정보")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("총 데이터 수", data_info.get('total_records', 0))
        
        with col2:
            st.metric("기간", data_info.get('days_covered', 0))
        
        with col3:
            completeness = "완전" if data_info.get('is_complete_30days', False) else "불완전"
            st.metric("30일 완성도", completeness)
        
        with col4:
            missing = data_info.get('missing_days', 0)
            st.metric("누락 일수", missing)
        
        # 상세 정보
        st.info(f"📅 **기간**: {data_info.get('date_range', 'N/A')}")
        st.info(f"🌍 **지역**: {data_info.get('city', 'N/A')}")
        st.info(f"🌡️ **기온 범위**: {data_info.get('temperature_range', 'N/A')}")
        st.info(f"💧 **습도 범위**: {data_info.get('humidity_range', 'N/A')}")
    
    def display_analysis_summary(self, analysis: Dict):
        """분석 요약을 표시합니다."""
        if not analysis:
            return
        
        st.subheader("📈 분석 요약")
        
        # 기본 정보
        basic_info = analysis.get('basic_info', {})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("총 데이터 수", basic_info.get('total_days', 0))
        
        with col2:
            st.metric("데이터 완성도", f"{basic_info.get('data_completeness', 0):.1f}%")
        
        with col3:
            outliers = analysis.get('outlier_analysis', {}).get('total_outliers', 0)
            st.metric("이상치 수", outliers)
        
        # 기온 분석
        temp_analysis = analysis.get('temperature_analysis', {})
        st.subheader("🌡️ 기온 분석")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("평균 기온", f"{temp_analysis.get('mean', 0)}°C")
        
        with col2:
            st.metric("최고 기온", f"{temp_analysis.get('max', 0)}°C")
        
        with col3:
            st.metric("최저 기온", f"{temp_analysis.get('min', 0)}°C")
        
        with col4:
            st.metric("변동성", f"{temp_analysis.get('volatility', 0)}%")
        
        # 습도 분석
        humidity_analysis = analysis.get('humidity_analysis', {})
        st.subheader("💧 습도 분석")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("평균 습도", f"{humidity_analysis.get('mean', 0)}%")
        
        with col2:
            st.metric("최고 습도", f"{humidity_analysis.get('max', 0)}%")
        
        with col3:
            st.metric("최저 습도", f"{humidity_analysis.get('min', 0)}%")
        
        with col4:
            st.metric("변동성", f"{humidity_analysis.get('volatility', 0)}%")
        
        # 트렌드 분석
        trends = analysis.get('trend_analysis', {})
        st.subheader("📈 트렌드 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            temp_trend = trends.get('temperature', {})
            st.metric("기온 트렌드", temp_trend.get('direction', 'N/A'))
            st.caption(f"강도: {temp_trend.get('strength', 'N/A')}")
        
        with col2:
            humidity_trend = trends.get('humidity', {})
            st.metric("습도 트렌드", humidity_trend.get('direction', 'N/A'))
            st.caption(f"강도: {humidity_trend.get('strength', 'N/A')}")
    
    def display_prediction_results(self, weather_predictions, mortality_result, selected_city, target_prediction_date=None):
        """예측 결과를 표시합니다."""
        if weather_predictions.empty:
            return
        
        # 예측 날짜 (사용자가 설정한 날짜 또는 마지막 예측 날짜)
        if target_prediction_date:
            prediction_date = target_prediction_date
        else:
            prediction_date = weather_predictions.iloc[-1]['date']
        
        st.success(f"✅ {prediction_date.strftime('%Y년 %m월 %d일')} 예측 완료 (30일 데이터 기반)")
        
        # 예측 결과 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "예측 기온",
                f"{weather_predictions.iloc[-1]['temperature']:.1f}°C"
            )
        
        with col2:
            st.metric(
                "예측 습도",
                f"{weather_predictions.iloc[-1]['humidity']:.1f}%"
            )
        
        with col3:
            st.metric(
                "예측 날짜",
                prediction_date.strftime('%m월 %d일')
            )
        
        with col4:
            # 날씨별 추천 옷
            temp = weather_predictions.iloc[-1]['temperature']
            humidity = weather_predictions.iloc[-1]['humidity']
            
            if temp >= 28:
                outfit_main = "👕 반팔티"
                outfit_sub = "🩳 반바지"
                outfit_desc = "시원한 여름 복장"
            elif temp >= 23:
                outfit_main = "👔 얇은 셔츠"
                outfit_sub = "👖 얇은 바지"
                outfit_desc = "가벼운 봄/가을 복장"
            elif temp >= 18:
                outfit_main = "🧥 얇은 가디건"
                outfit_sub = "👖 긴바지"
                outfit_desc = "적당한 겉옷 필요"
            elif temp >= 12:
                outfit_main = "🧥 코트"
                outfit_sub = "🧣 목도리"
                outfit_desc = "따뜻한 겨울 복장"
            else:
                outfit_main = "🧥 패딩"
                outfit_sub = "🧤 장갑"
                outfit_desc = "두꺼운 겨울 복장"
            
            # 습도에 따른 추가 조언
            extra_item = ""
            extra_desc = ""
            if humidity >= 80:
                extra_item = "☔ 우산"
                extra_desc = " (비 올 수 있음)"
            elif humidity <= 30:
                extra_item = "💧 보습제"
                extra_desc = " (건조함)"
            
            # 추천 복장 표시 (폰트 크기 통일)
            st.markdown("**추천 복장**", help=f"{outfit_desc}{extra_desc}")
            
            # 메인 복장과 서브 복장을 세로로 배치 (왼쪽 정렬)
            st.markdown(f"<div style='text-align: left; font-size: 20px; margin: 2px 0; line-height: 1.2; padding: 0 2px;'>{outfit_main}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='text-align: left; font-size: 20px; margin: 2px 0; line-height: 1.2; padding: 0 2px;'>{outfit_sub}</div>", unsafe_allow_html=True)
            
            # 추가 아이템이 있으면 표시
            if extra_item:
                st.markdown(f"<div style='text-align: left; font-size: 20px; color: #666; margin: 2px 0; line-height: 1.2; padding: 0 2px;'>{extra_item}</div>", unsafe_allow_html=True)
        
        # 사망률 결과 표시
        if mortality_result:
            st.subheader("💀 사망률 예측 결과")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "예상 사망률",
                    f"{mortality_result['mortality_rate']}",
                    help="10만명당 사망자 수"
                )
            
            with col2:
                st.metric(
                    "위험 수준",
                    mortality_result['risk_level']
                )
            
            with col3:
                st.metric(
                    "하한값",
                    f"{mortality_result['lower_bound']}"
                )
            
            with col4:
                st.metric(
                    "상한값",
                    f"{mortality_result['upper_bound']}"
                )
    
    def create_tabs(self) -> Tuple:
        """탭을 생성합니다."""
        return st.tabs([
            "📈 기상 트렌드",
            "🔍 30일 패턴 분석", 
            "🔮 예측 분석",
            "📊 상세 분석"
        ])
    
    def display_quality_warnings(self, quality_check: Dict):
        """데이터 품질 경고를 표시합니다."""
        if not quality_check or quality_check.get('is_valid', True):
            return
        
        issues = quality_check.get('issues', [])
        if issues:
            st.warning("⚠️ 데이터 품질 문제가 발견되었습니다:")
            for issue in issues:
                st.write(f"• {issue}")
            
            quality_score = quality_check.get('quality_score', 0)
            st.info(f"📊 데이터 품질 점수: {quality_score}/100")
    
    def display_filter_options(self, data: pd.DataFrame) -> Dict:
        """필터 옵션을 표시합니다."""
        st.subheader("🔍 데이터 필터링")
        
        # 기온 범위 필터 (더 유연한 설정)
        temp_min = float(data['temperature'].min())
        temp_max = float(data['temperature'].max())
        default_min = max(temp_min - 10, -30)  # 최소값보다 10도 낮게, 최소 -30도
        
        min_temp = st.slider(
            "🌡️ 최소 기온 (°C)",
            min_value=default_min,
            max_value=temp_max,
            value=default_min,  # 기본값을 더 낮게 설정하여 모든 데이터 포함
            step=0.5,
            help="이 온도 이상의 데이터만 표시됩니다."
        )
        
        # 현재 필터링된 데이터 수 표시
        filtered_count = len(data[data['temperature'] >= min_temp])
        if filtered_count == len(data):
            st.success(f"📊 모든 데이터 표시 중: {filtered_count}개")
        else:
            st.info(f"📊 필터링된 데이터: {filtered_count}개 / {len(data)}개")
        
        return {
            'min_temp': min_temp
        }
    
    def display_loading_message(self, message: str):
        """로딩 메시지를 표시합니다."""
        with st.spinner(message):
            st.info("데이터를 처리하는 중입니다...")
    
    def display_error_message(self, error: str):
        """에러 메시지를 표시합니다."""
        st.error(f"❌ 오류가 발생했습니다: {error}")
    
    def display_success_message(self, message: str):
        """성공 메시지를 표시합니다."""
        st.success(f"✅ {message}")
    
    def display_info_message(self, message: str):
        """정보 메시지를 표시합니다."""
        st.info(f"ℹ️ {message}")
    
    def display_warning_message(self, message: str):
        """경고 메시지를 표시합니다."""
        st.warning(f"⚠️ {message}")
    
    def create_metric_card(self, title: str, value: str, help_text: str = ""):
        """메트릭 카드를 생성합니다."""
        st.metric(title, value, help=help_text)
    
    def create_progress_bar(self, current: int, total: int, label: str = "진행률"):
        """진행률 바를 생성합니다."""
        progress = current / total if total > 0 else 0
        st.progress(progress, text=f"{label}: {current}/{total}")
    
    def create_expander(self, title: str, content: str):
        """확장 가능한 섹션을 생성합니다."""
        with st.expander(title):
            st.markdown(content)
    
    def create_columns(self, num_columns: int):
        """컬럼을 생성합니다."""
        return st.columns(num_columns) 