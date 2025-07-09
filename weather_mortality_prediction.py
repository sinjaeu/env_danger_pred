"""
🌤️ 기상 기반 사망률 예측 시스템

실제 기상청 데이터를 기반으로 기온과 습도를 예측하고, 
논문 데이터를 활용하여 사망률을 계산하는 Streamlit 애플리케이션입니다.

모듈화된 구조:
- weather_api.py: 기상청 API 연동
- weather_prediction.py: 기상 예측
- mortality_calculator.py: 사망률 계산
- visualization.py: 시각화
- utils.py: 유틸리티 함수
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

# 모듈 임포트
from weather_api import WeatherAPI
from weather_prediction import WeatherPredictor
from mortality_calculator import MortalityCalculator
from visualization import WeatherVisualizer
from utils import (
    load_environment_variables, 
    generate_fallback_data, 
    validate_date_range,
    format_date_for_display,
    format_date_for_api,
    calculate_statistics,
    display_statistics,
    create_cache_key,
    clear_cache
)


# 페이지 설정
st.set_page_config(
    page_title="🌤️ 기상 기반 사망률 예측 시스템",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 제목
st.title("🌤️ 기상 기반 사망률 예측 시스템")
st.markdown("실제 기상청 데이터를 기반으로 기온과 습도를 예측하고, 논문 데이터를 활용하여 사망률을 계산합니다.")

# 사이드바 설정
st.sidebar.header("⚙️ 설정")

# API 키 로드
api_key = load_environment_variables()

if not api_key:
    st.error("❌ 유효한 기상청 API 키를 입력해주세요.")
    st.stop()

# 모듈 초기화
weather_api = WeatherAPI(api_key)
weather_predictor = WeatherPredictor()
mortality_calculator = MortalityCalculator()
visualizer = WeatherVisualizer()

# 사이드바 컨트롤
st.sidebar.subheader("📍 위치 및 기간 설정")

# 도시 선택
cities = list(weather_api.station_codes.keys())
selected_city = st.sidebar.selectbox(
    "도시 선택",
    cities,
    index=0
)

# 연도 선택
current_year = datetime.now().year
years = list(range(current_year - 3, current_year))
selected_years = st.sidebar.multiselect(
    "분석할 연도 선택 (최근 3년)",
    years,
    default=years
)

# 예측 설정
st.sidebar.subheader("🔮 예측 설정")

# 예측 날짜
max_prediction_date = datetime.now() + timedelta(days=90)
prediction_date = st.sidebar.date_input(
    "예측 날짜",
    value=datetime.now() + timedelta(days=7),
    min_value=datetime.now(),
    max_value=max_prediction_date
)

# 연령대 선택
age_groups = ["전체", "20세 미만", "20-74세", "75세 이상"]
selected_age_group = st.sidebar.selectbox(
    "연령대",
    age_groups,
    index=0
)

# 성별 선택
genders = ["전체", "남성", "여성"]
selected_gender = st.sidebar.selectbox(
    "성별",
    genders,
    index=0
)

# 달력 기능
st.sidebar.subheader("📅 달력 기능")
calendar_date = st.sidebar.date_input(
    "특정 날짜 확인",
    value=datetime.now(),
    help="과거 날짜는 실제 데이터, 미래 날짜는 예측 데이터를 표시합니다."
)

# 캐시 초기화
if st.sidebar.button("🗑️ 캐시 초기화"):
    clear_cache()

# 메인 컨텐츠
@st.cache_data
def load_historical_data(city: str, years: list):
    """과거 기상 데이터를 로드합니다 (캐시 적용)."""
    
    if not years:
        st.error("분석할 연도를 선택해주세요.")
        return pd.DataFrame()
    
    # API로 실제 데이터 가져오기 시도
    historical_data = weather_api.get_historical_data(city, years)
    
    if historical_data.empty:
        st.warning("⚠️ API에서 데이터를 가져올 수 없어 대체 데이터를 생성합니다.")
        historical_data = generate_fallback_data(city, years)
    
    return historical_data

# 데이터 로드
if selected_years:
    with st.spinner(f"📊 {selected_city}의 과거 {len(selected_years)}년 기상 데이터를 로드하는 중..."):
        historical_data = load_historical_data(selected_city, selected_years)
    
    if not historical_data.empty:
        # 통계 정보 표시
        stats = calculate_statistics(historical_data)
        display_statistics(stats)
        
        # 탭 생성
        tab1, tab2, tab3, tab4 = st.tabs(["📈 기상 트렌드", "🔮 예측 분석", "📅 달력 기능", "📊 상세 분석"])
        
        with tab1:
            st.subheader("📈 기상 트렌드 분석")
            
            # 기상 트렌드 차트
            weather_chart = visualizer.create_weather_trend_chart(
                historical_data, 
                f"{selected_city} 기상 트렌드 ({min(selected_years)}-{max(selected_years)})"
            )
            st.plotly_chart(weather_chart, use_container_width=True)
            
            # 계절별 분석
            seasonal_chart = visualizer.create_seasonal_analysis_chart(
                historical_data,
                f"{selected_city} 계절별 분석"
            )
            st.plotly_chart(seasonal_chart, use_container_width=True)
            
            # 산점도
            scatter_chart = visualizer.create_weather_scatter_plot(
                historical_data,
                f"{selected_city} 기온-습도 산점도"
            )
            st.plotly_chart(scatter_chart, use_container_width=True)
        
        with tab2:
            st.subheader("🔮 기상 및 사망률 예측")
            
            if st.button("🚀 기상 및 사망률 예측 실행"):
                with st.spinner("예측을 수행하는 중..."):
                    # 미래 기상 예측
                    days_ahead = (prediction_date - datetime.now().date()).days
                    weather_predictions = weather_predictor.predict_weather(historical_data, days_ahead)
                    
                    if not weather_predictions.empty:
                        st.success(f"✅ {prediction_date.strftime('%Y년 %m월 %d일')} 예측 완료")
                        
                        # 예측 결과 표시
                        col1, col2, col3 = st.columns(3)
                        
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
                                "계절",
                                weather_predictions.iloc[-1]['season']
                            )
                        
                        # 사망률 계산
                        weather_dict = {
                            'date': weather_predictions.iloc[-1]['date'],
                            'city': selected_city,
                            'temperature': weather_predictions.iloc[-1]['temperature'],
                            'humidity': weather_predictions.iloc[-1]['humidity'],
                            'season': weather_predictions.iloc[-1]['season']
                        }
                        
                        mortality_result = mortality_calculator.calculate_mortality_rate(
                            weather_dict, selected_age_group, selected_gender
                        )
                        
                        if mortality_result:
                            # 사망률 결과 표시
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
                            
                            # 위험도 분석 차트
                            risk_chart = visualizer.create_risk_factors_chart(
                                mortality_result['risk_factors'],
                                "위험도 요인 분석"
                            )
                            st.plotly_chart(risk_chart, use_container_width=True)
                            
                            # 요약 메트릭
                            summary = visualizer.create_summary_metrics(weather_dict, mortality_result)
                            st.markdown(summary)
                        
                        # 예측 트렌드 차트
                        combined_data = pd.concat([historical_data, weather_predictions], ignore_index=True)
                        trend_chart = visualizer.create_weather_trend_chart(
                            combined_data,
                            f"{selected_city} 기상 트렌드 (과거 + 예측)"
                        )
                        st.plotly_chart(trend_chart, use_container_width=True)
                        
                        # 사망률 트렌드
                        mortality_trend = mortality_calculator.calculate_mortality_trend(
                            combined_data, selected_age_group, selected_gender
                        )
                        
                        if not mortality_trend.empty:
                            mortality_chart = visualizer.create_mortality_chart(
                                mortality_trend,
                                f"{selected_city} 사망률 트렌드"
                            )
                            st.plotly_chart(mortality_chart, use_container_width=True)
        
        with tab3:
            st.subheader("📅 달력 기능")
            st.info(f"📅 {format_date_for_display(calendar_date)}의 데이터를 확인합니다.")
            
            # 해당 날짜의 기상 데이터 가져오기
            weather_data = weather_predictor.get_weather_for_date(historical_data, calendar_date)
            
            if weather_data:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("기온", f"{weather_data['temperature']:.1f}°C")
                
                with col2:
                    st.metric("습도", f"{weather_data['humidity']:.1f}%")
                
                with col3:
                    st.metric("계절", weather_data['season'])
                
                with col4:
                    data_type = "예측" if weather_data['is_prediction'] else "실제"
                    st.metric("데이터 유형", data_type)
                
                # 사망률 계산
                mortality_result = mortality_calculator.calculate_mortality_rate(
                    weather_data, selected_age_group, selected_gender
                )
                
                if mortality_result:
                    st.subheader("💀 사망률 분석")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "사망률",
                            f"{mortality_result['mortality_rate']}",
                            help="10만명당 사망자 수"
                        )
                    
                    with col2:
                        st.metric("위험 수준", mortality_result['risk_level'])
                    
                    with col3:
                        st.metric(
                            "신뢰구간",
                            f"{mortality_result['lower_bound']}~{mortality_result['upper_bound']}"
                        )
                    
                    # 위험도 분석
                    risk_chart = visualizer.create_risk_factors_chart(
                        mortality_result['risk_factors'],
                        "위험도 요인 분석"
                    )
                    st.plotly_chart(risk_chart, use_container_width=True)
            else:
                st.warning("해당 날짜의 데이터를 찾을 수 없습니다.")
        
        with tab4:
            st.subheader("📊 상세 분석")
            
            # 데이터 필터링 옵션
            st.subheader("🔍 데이터 필터")
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_season = st.selectbox(
                    "계절 선택",
                    ["전체"] + list(historical_data['season'].unique()),
                    index=0
                )
            
            with col2:
                min_temp = st.slider(
                    "최소 기온",
                    float(historical_data['temperature'].min()),
                    float(historical_data['temperature'].max()),
                    float(historical_data['temperature'].min())
                )
            
            # 필터링된 데이터
            filtered_data = historical_data.copy()
            
            if selected_season != "전체":
                filtered_data = filtered_data[filtered_data['season'] == selected_season]
            
            filtered_data = filtered_data[filtered_data['temperature'] >= min_temp]
            
            if not filtered_data.empty:
                st.success(f"✅ 필터링된 데이터: {len(filtered_data)}개")
                
                # 필터링된 데이터 통계
                filtered_stats = calculate_statistics(filtered_data)
                display_statistics(filtered_stats)
                
                # 필터링된 데이터 차트
                filtered_chart = visualizer.create_weather_trend_chart(
                    filtered_data,
                    f"필터링된 데이터 - {selected_city}"
                )
                st.plotly_chart(filtered_chart, use_container_width=True)
            else:
                st.warning("필터 조건에 맞는 데이터가 없습니다.")
    
    else:
        st.error("❌ 데이터를 로드할 수 없습니다.")
else:
    st.info("👈 사이드바에서 분석할 연도를 선택해주세요.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        🌤️ 기상 기반 사망률 예측 시스템 | 
        <a href='https://github.com/sinjaeu/env_danger_pred' target='_blank'>GitHub</a> |
        기상청 API Hub 연동
    </div>
    """,
    unsafe_allow_html=True
)