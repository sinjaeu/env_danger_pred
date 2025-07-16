"""
🌤️ 기상 기반 사망률 예측 시스템 (30일 데이터 특화)

실제 기상청 데이터를 기반으로 최근 30일 기상 데이터를 분석하고, 
논문 데이터를 활용하여 사망률을 계산하는 Streamlit 애플리케이션입니다.

모듈화된 구조:
- weather_api.py: 기상청 API 연동
- weather_prediction.py: 기상 예측
- mortality_calculator.py: 사망률 계산
- visualization.py: 시각화
- data_loader.py: 데이터 로딩
- data_analyzer.py: 데이터 분석
- ui_components.py: UI 컴포넌트
- utils.py: 유틸리티 함수
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 모듈 임포트
from weather_api import WeatherAPI
from data_loader import DataLoader
from data_analyzer import DataAnalyzer
from weather_prediction import WeatherPredictor
from mortality_calculator import MortalityCalculator
from visualization import WeatherVisualizer
from ui_components import UIComponents
from utils import calculate_statistics, display_statistics, load_environment_variables

# 페이지 설정
st.set_page_config(
    page_title="기상 기반 사망률 예측 시스템",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 제목
st.title("🌤️ 기상 기반 사망률 예측 시스템")
st.markdown("### 📊 30일 데이터 특화 분석 및 예측")

# API 키 로드
api_key = load_environment_variables()

if not api_key:
    st.error("❌ 유효한 기상청 API 키를 입력해주세요.")
    st.stop()

# 모듈 초기화
weather_api = WeatherAPI(api_key)
data_loader = DataLoader(weather_api)
data_analyzer = DataAnalyzer()
weather_predictor = WeatherPredictor()
mortality_calculator = MortalityCalculator()
visualizer = WeatherVisualizer()
ui_components = UIComponents()

# 세션 상태 초기화
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = None
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'prediction_executed' not in st.session_state:
    st.session_state.prediction_executed = False
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 0
if 'run_prediction' not in st.session_state:
    st.session_state.run_prediction = False
if 'prediction_data_id' not in st.session_state:
    st.session_state.prediction_data_id = None
if 'weather_predictions' not in st.session_state:
    st.session_state.weather_predictions = None
if 'mortality_result' not in st.session_state:
    st.session_state.mortality_result = None

# 사이드바 설정
settings = ui_components.create_sidebar(weather_api)

# 데이터 로드 버튼
st.subheader("🚀 데이터 분석 시작")
st.info("📋 위의 사이드바에서 설정을 완료한 후 아래 버튼을 클릭하여 데이터 분석을 시작하세요.")

if st.button("📊 30일 기상 데이터 분석 시작", type="primary", use_container_width=True):
    with st.spinner(f"📊 {settings['selected_city']}의 최근 30일 기상 데이터를 로드하는 중..."):
        historical_data = data_loader.load_30day_data(settings['selected_city'])
    
    if not historical_data.empty:
        # 데이터 정리
        historical_data = data_loader.clean_data(historical_data)
        
        # 세션 상태에 데이터 저장
        st.session_state.historical_data = historical_data
        st.session_state.data_loaded = True
        st.session_state.prediction_executed = False
        
        # 데이터 품질 검증
        quality_check = data_loader.validate_data_quality(historical_data)
        ui_components.display_quality_warnings(quality_check)
        
        # 데이터 정보 표시
        data_info = data_loader.get_data_info(historical_data)
        ui_components.display_data_info(data_info)
        
        # 30일 데이터 분석
        analysis = data_analyzer.analyze_30day_data(historical_data)
        ui_components.display_analysis_summary(analysis)
        
        # 기본 통계 정보 표시
        stats = calculate_statistics(historical_data)
        display_statistics(stats)
        
        # 예측 완료 상태 확인하여 결과 요약 표시
        if st.session_state.get('prediction_executed', False) and st.session_state.get('weather_predictions') is not None:
            st.markdown("---")
            st.subheader("🎉 예측 완료! 결과 요약")
            
            # 간단한 결과 요약 표시
            weather_pred = st.session_state.weather_predictions.iloc[-1]
            mortality_result = st.session_state.mortality_result
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("예측 기온", f"{weather_pred['temperature']:.1f}°C")
            with col2:
                st.metric("예측 습도", f"{weather_pred['humidity']:.1f}%")
            with col3:
                if mortality_result:
                    st.metric("사망률", f"{mortality_result['mortality_rate']:.2f}%")
                else:
                    st.metric("사망률", "계산 중")
            with col4:
                if mortality_result:
                    risk_level = "높음" if mortality_result['mortality_rate'] > 0.5 else "보통" if mortality_result['mortality_rate'] > 0.3 else "낮음"
                    st.metric("위험도", risk_level)
                else:
                    st.metric("위험도", "분석 중")
            
            # 예측 탭으로 이동 안내
            st.info("💡 자세한 예측 결과는 아래 '🔮 예측 분석' 탭에서 확인하세요!")
            st.markdown("---")
        
        # 예측 완료 상태에 따른 탭 제목 설정
        if st.session_state.get('prediction_executed', False):
            tab_titles = [
                "📈 기상 트렌드", 
                "🔍 30일 패턴 분석", 
                "🔮 예측 결과 ✅", 
                "📊 상세 분석"
            ]
        else:
            tab_titles = [
            "📈 기상 트렌드", 
            "🔍 30일 패턴 분석", 
            "🔮 예측 분석", 
            "📊 상세 분석"
            ]
        
        # Streamlit 탭 시스템 사용
        tab1, tab2, tab3, tab4 = st.tabs(tab_titles)
        
        # 기상 트렌드 탭
        with tab1:
            st.subheader("📈 최근 30일 기상 트렌드 분석")
            
            # 기상 트렌드 차트
            chart_title = f"{settings['selected_city']} 기상 트렌드 (최근 30일, 오늘 제외)"
            
            weather_chart = visualizer.create_weather_trend_chart(
                historical_data, 
                chart_title
            )
            st.plotly_chart(weather_chart, use_container_width=True, key="weather_trend_chart")
            
            # 산점도
            scatter_chart = visualizer.create_weather_scatter_plot(
                historical_data,
                f"{settings['selected_city']} 30일 기온-습도 산점도"
            )
            st.plotly_chart(scatter_chart, use_container_width=True, key="weather_scatter_chart")
        
        # 30일 패턴 분석 탭
        with tab2:
            st.subheader("🔍 30일 데이터 패턴 분석")
            
            # 30일 패턴 분석 차트
            pattern_chart = visualizer.create_30day_pattern_chart(
                historical_data,
                f"{settings['selected_city']} 30일 패턴 분석"
            )
            st.plotly_chart(pattern_chart, use_container_width=True, key="pattern_analysis_chart")
            
            # 이상치 분석 차트
            outlier_chart = visualizer.create_outlier_analysis_chart(
                historical_data,
                f"{settings['selected_city']} 30일 이상치 분석"
            )
            st.plotly_chart(outlier_chart, use_container_width=True, key="outlier_analysis_chart")
            
            # 트렌드 분석 차트
            trend_chart = visualizer.create_trend_analysis_chart(
                historical_data,
                f"{settings['selected_city']} 30일 트렌드 분석"
            )
            st.plotly_chart(trend_chart, use_container_width=True, key="tab2_trend_analysis_chart")
            
            # 분석 리포트 표시
            analysis_report = data_analyzer.get_analysis_report(historical_data)
            with st.expander("📊 상세 분석 리포트"):
                st.markdown(analysis_report)
        
        # 예측 분석 탭
        with tab3:
            if st.session_state.get('prediction_executed', False):
                st.subheader("🎉 예측 결과")
                st.success("✅ 예측이 완료되었습니다!")
            else:
                st.subheader("🔮 기상 및 사망률 예측")
                
                # 30일 데이터 기반 예측 정보 표시
                st.info(f"📊 최근 30일 데이터 기반 예측 ({len(historical_data)}개 데이터 포인트)")
            
            # 예측 실행 버튼
            if st.session_state.get('prediction_executed', False):
                col1, col2 = st.columns([1, 1])
                with col1:
                    # 재예측 버튼
                    button_key = f"repredict_button_{id(historical_data)}"
                    if st.button("🔄 재예측", key=button_key, type="primary"):
                        # 재예측 시 상태 초기화 (리로딩 방지)
                        st.session_state.update({
                            'prediction_executed': False,
                            'run_prediction': True,
                            'prediction_data_id': id(historical_data),
                            'weather_predictions': None,
                            'mortality_result': None
                        })
                with col2:
                    # 예측 결과 초기화 버튼
                    clear_key = f"clear_button_{id(historical_data)}"
                    if st.button("🗑️ 결과 초기화", key=clear_key):
                        # 상태 초기화 (st.rerun() 제거하여 리로딩 방지)
                        st.session_state.update({
                            'prediction_executed': False,
                            'weather_predictions': None,
                            'mortality_result': None
                        })
            else:
                col1, col2 = st.columns([1, 3])
                with col1:
                    # 고유한 key로 버튼 생성
                    button_key = f"predict_button_{id(historical_data)}"
                    if st.button("🚀 예측 실행", key=button_key, type="primary"):
                        st.session_state.run_prediction = True
                        st.session_state.prediction_data_id = id(historical_data)
            
            # 예측 실행 상태 확인 (데이터 ID도 확인)
            if (st.session_state.get('run_prediction', False) and 
                st.session_state.get('prediction_data_id') == id(historical_data)):
                
                with st.spinner("30일 데이터 기반 예측을 수행하는 중..."):
                    # 예측 데이터 준비
                    prediction_data = historical_data.copy()
                    
                    # 시간 가중치 기반 미래 기상 예측
                    days_ahead = (settings['prediction_date'] - datetime.now().date()).days
                    st.info(f"🔮 시간 가중치 기반 예측 모델로 {days_ahead}일 후까지 예측합니다...")
                    
                    try:
                        weather_predictions = weather_predictor.predict_weather(prediction_data, days_ahead)
                        
                        if not weather_predictions.empty:
                            # 사망률 계산
                            weather_dict = {
                                'date': weather_predictions.iloc[-1]['date'],
                                'city': settings['selected_city'],
                                'temperature': weather_predictions.iloc[-1]['temperature'],
                                'humidity': weather_predictions.iloc[-1]['humidity']
                            }
                            
                            mortality_result = mortality_calculator.calculate_mortality_rate(
                                weather_dict, settings['selected_age_group'], settings['selected_gender']
                            )
                            
                            # 예측 결과를 한 번에 저장 (리로딩 방지)
                            st.session_state.weather_predictions = weather_predictions
                            st.session_state.mortality_result = mortality_result
                            st.session_state.prediction_executed = True
                            # 예측 실행 상태 초기화 (탭 이동 방지를 위해 st.rerun() 제거)
                            st.session_state.run_prediction = False
                            st.session_state.prediction_data_id = None
                            
                            # 예측 완료 알림 (즉시 표시)
                            st.success("🎉 예측이 완료되었습니다! 아래에서 결과를 확인하세요!")
                            st.balloons()  # 성공 효과
                            
                        else:
                            st.error("❌ 예측 데이터 생성에 실패했습니다.")
                            # 실패 시 상태 초기화
                            st.session_state.run_prediction = False
                            st.session_state.prediction_data_id = None
                    except Exception as e:
                        st.error(f"❌ 예측 중 오류가 발생했습니다: {str(e)}")
                        # 오류 시 상태 초기화
                        st.session_state.run_prediction = False
                        st.session_state.prediction_data_id = None
            
            # 예측 결과가 있으면 표시 (버튼 클릭 여부와 관계없이)
            if st.session_state.prediction_executed and st.session_state.weather_predictions is not None:
                weather_predictions = st.session_state.weather_predictions
                mortality_result = st.session_state.mortality_result
                
                # 예측 결과 하이라이트
                st.markdown("### 📊 예측 결과 대시보드")
                st.markdown("---")
                
                # 예측 결과 표시
                ui_components.display_prediction_results(weather_predictions, mortality_result, settings['selected_city'], settings['prediction_date'])
                
                # 중복된 상태 변경 제거 (리로딩 방지)
                
                if mortality_result:
                    # 위험도 분석 차트
                    risk_chart = visualizer.create_risk_factors_chart(
                        mortality_result['risk_factors'],
                        "위험도 요인 분석"
                    )
                    st.plotly_chart(risk_chart, use_container_width=True, key="risk_factors_chart")
                    
                    # 요약 메트릭
                    weather_dict = {
                        'date': weather_predictions.iloc[-1]['date'],
                        'city': settings['selected_city'],
                        'temperature': weather_predictions.iloc[-1]['temperature'],
                        'humidity': weather_predictions.iloc[-1]['humidity']
                    }
                    summary = visualizer.create_summary_metrics(weather_dict, mortality_result)
                    st.markdown(summary)
                
                # 예측 트렌드 차트
                combined_data = pd.concat([historical_data, weather_predictions], ignore_index=True)
                trend_chart = visualizer.create_weather_trend_chart(
                    combined_data,
                    f"{settings['selected_city']} 기상 트렌드 (30일 과거 + 예측)"
                )
                st.plotly_chart(trend_chart, use_container_width=True, key="prediction_trend_chart")
                
                # 사망률 트렌드
                mortality_trend = mortality_calculator.calculate_mortality_trend(
                    combined_data, settings['selected_age_group'], settings['selected_gender']
                )
                
                if not mortality_trend.empty:
                    mortality_chart = visualizer.create_mortality_chart(
                        mortality_trend,
                        f"{settings['selected_city']} 사망률 트렌드 (30일 기반)"
                    )
                    st.plotly_chart(mortality_chart, use_container_width=True, key="mortality_trend_chart")
        
        # 상세 분석 탭
        with tab4:
            st.subheader("📊 30일 데이터 상세 분석")
            
            # 필터 옵션
            filter_options = ui_components.display_filter_options(historical_data)
            
            # 필터링된 데이터
            filtered_data = historical_data.copy()
            filtered_data = filtered_data[filtered_data['temperature'] >= filter_options['min_temp']]
            
            if not filtered_data.empty:
                st.success(f"✅ 필터링된 데이터: {len(filtered_data)}개 (30일 중)")
                
                # 필터링된 데이터 통계
                filtered_stats = calculate_statistics(filtered_data)
                display_statistics(filtered_stats)
                
                # 필터링된 데이터 차트
                filtered_chart = visualizer.create_weather_trend_chart(
                    filtered_data,
                    f"필터링된 데이터 - {settings['selected_city']} (30일)"
                )
                st.plotly_chart(filtered_chart, use_container_width=True, key="filtered_data_chart_1")
                
                # 필터링된 데이터 분석
                filtered_analysis = data_analyzer.analyze_30day_data(filtered_data)
                with st.expander("🔍 필터링된 데이터 분석"):
                    ui_components.display_analysis_summary(filtered_analysis)
            else:
                st.warning("⚠️ 필터 조건에 맞는 데이터가 없습니다.")
                st.info("💡 팁: 슬라이더를 더 낮은 값으로 조정해보세요.")
                
                # 전체 데이터 통계 표시
                st.subheader("📊 전체 데이터 통계")
                full_stats = calculate_statistics(historical_data)
                display_statistics(full_stats)
                
                # 전체 데이터 차트 표시
                st.subheader("📈 전체 데이터 차트")
                full_chart = visualizer.create_weather_trend_chart(
                    historical_data,
                    f"전체 데이터 - {settings['selected_city']} (30일)"
                )
                st.plotly_chart(full_chart, use_container_width=True, key="full_data_chart_1")
    else:
        st.error("❌ 30일 데이터를 로드할 수 없습니다.")

# 세션 상태에 저장된 데이터가 있으면 탭 표시
elif st.session_state.data_loaded and st.session_state.historical_data is not None:
    historical_data = st.session_state.historical_data
    
    # 데이터 정보 표시
    data_info = data_loader.get_data_info(historical_data)
    ui_components.display_data_info(data_info)
    
    # 30일 데이터 분석
    analysis = data_analyzer.analyze_30day_data(historical_data)
    ui_components.display_analysis_summary(analysis)
    
    # 기본 통계 정보 표시
    stats = calculate_statistics(historical_data)
    display_statistics(stats)
    
    # Streamlit 탭 시스템 사용
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 기상 트렌드", 
        "🔍 30일 패턴 분석", 
        "🔮 예측 분석", 
        "📊 상세 분석"
    ])
    
    # 기상 트렌드 탭
    with tab1:
        st.subheader("📈 최근 30일 기상 트렌드 분석")
        
        # 기상 트렌드 차트
        chart_title = f"{settings['selected_city']} 기상 트렌드 (최근 30일, 오늘 제외)"
        
        weather_chart = visualizer.create_weather_trend_chart(
            historical_data, 
            chart_title
        )
        st.plotly_chart(weather_chart, use_container_width=True, key="weather_trend_chart_2")
        
        # 산점도
        scatter_chart = visualizer.create_weather_scatter_plot(
            historical_data,
            f"{settings['selected_city']} 30일 기온-습도 산점도"
        )
        st.plotly_chart(scatter_chart, use_container_width=True, key="weather_scatter_chart_2")
    
    # 30일 패턴 분석 탭
    with tab2:
        st.subheader("🔍 30일 데이터 패턴 분석")
        
        # 30일 패턴 분석 차트
        pattern_chart = visualizer.create_30day_pattern_chart(
            historical_data,
            f"{settings['selected_city']} 30일 패턴 분석"
        )
        st.plotly_chart(pattern_chart, use_container_width=True, key="pattern_analysis_chart_2")
        
        # 이상치 분석 차트
        outlier_chart = visualizer.create_outlier_analysis_chart(
            historical_data,
            f"{settings['selected_city']} 30일 이상치 분석"
        )
        st.plotly_chart(outlier_chart, use_container_width=True, key="outlier_analysis_chart_2")
        
        # 트렌드 분석 차트
        trend_chart = visualizer.create_trend_analysis_chart(
            historical_data,
            f"{settings['selected_city']} 30일 트렌드 분석"
        )
        st.plotly_chart(trend_chart, use_container_width=True, key="tab2_trend_analysis_chart_2")
        
        # 분석 리포트 표시
        analysis_report = data_analyzer.get_analysis_report(historical_data)
        with st.expander("📊 상세 분석 리포트"):
            st.markdown(analysis_report)
    
    # 예측 분석 탭
    with tab3:
        st.subheader("🔮 기상 및 사망률 예측")
        
        # 30일 데이터 기반 예측 정보 표시
        st.info(f"📊 최근 30일 데이터 기반 예측 ({len(historical_data)}개 데이터 포인트)")
        
        # 예측 실행 버튼
        col1, col2 = st.columns([1, 3])
        with col1:
            # 고유한 key로 버튼 생성
            button_key = f"predict_button_secondary_{id(historical_data)}"
            if st.button("🚀 예측 실행", key=button_key, type="primary"):
                st.session_state.run_prediction = True
                st.session_state.prediction_data_id = id(historical_data)
        
        # 예측 실행 상태 확인 (데이터 ID도 확인)
        if (st.session_state.get('run_prediction', False) and 
            st.session_state.get('prediction_data_id') == id(historical_data)):
            with st.spinner("30일 데이터 기반 예측을 수행하는 중..."):
                # 예측 데이터 준비
                prediction_data = historical_data.copy()
                
                # 시간 가중치 기반 미래 기상 예측
                days_ahead = (settings['prediction_date'] - datetime.now().date()).days
                st.info(f"🔮 시간 가중치 기반 예측 모델로 {days_ahead}일 후까지 예측합니다...")
                weather_predictions = weather_predictor.predict_weather(prediction_data, days_ahead)
                
                if not weather_predictions.empty:
                    # 사망률 계산
                    weather_dict = {
                        'date': weather_predictions.iloc[-1]['date'],
                        'city': settings['selected_city'],
                        'temperature': weather_predictions.iloc[-1]['temperature'],
                        'humidity': weather_predictions.iloc[-1]['humidity']
                    }
                    
                    mortality_result = mortality_calculator.calculate_mortality_rate(
                        weather_dict, settings['selected_age_group'], settings['selected_gender']
                    )
                    
                    # 예측 결과를 세션 상태에 저장
                    st.session_state.weather_predictions = weather_predictions
                    st.session_state.mortality_result = mortality_result
                    st.session_state.prediction_executed = True
                    
                    # 예측 완료 메시지
                    st.success("✅ 예측이 완료되었습니다!")
                    
                    # 예측 실행 상태는 결과 표시 후에 초기화
                    st.session_state.run_prediction = False
                    st.session_state.prediction_data_id = None
        
        # 예측 결과가 있으면 표시 (버튼 클릭 여부와 관계없이)
        if st.session_state.prediction_executed and st.session_state.weather_predictions is not None:
            weather_predictions = st.session_state.weather_predictions
            mortality_result = st.session_state.mortality_result
            
            st.success("✅ 예측 결과가 있습니다.")
            
            # 예측 결과 표시
            ui_components.display_prediction_results(weather_predictions, mortality_result, settings['selected_city'], settings['prediction_date'])
            
            # 예측 결과 표시 후 실행 상태 초기화 (리로딩 방지)
            if st.session_state.get('run_prediction', False):
                st.session_state.run_prediction = False
                st.session_state.prediction_data_id = None
            
            if mortality_result:
                # 위험도 분석 차트
                risk_chart = visualizer.create_risk_factors_chart(
                    mortality_result['risk_factors'],
                    "위험도 요인 분석"
                )
                st.plotly_chart(risk_chart, use_container_width=True, key="risk_factors_chart_2")
                
                # 요약 메트릭
                weather_dict = {
                    'date': weather_predictions.iloc[-1]['date'],
                    'city': settings['selected_city'],
                    'temperature': weather_predictions.iloc[-1]['temperature'],
                    'humidity': weather_predictions.iloc[-1]['humidity']
                }
                summary = visualizer.create_summary_metrics(weather_dict, mortality_result)
                st.markdown(summary)
            
            # 예측 트렌드 차트
            combined_data = pd.concat([historical_data, weather_predictions], ignore_index=True)
            trend_chart = visualizer.create_weather_trend_chart(
                combined_data,
                f"{settings['selected_city']} 기상 트렌드 (30일 과거 + 예측)"
            )
            st.plotly_chart(trend_chart, use_container_width=True, key="prediction_trend_chart_2")
            
            # 사망률 트렌드
            mortality_trend = mortality_calculator.calculate_mortality_trend(
                combined_data, settings['selected_age_group'], settings['selected_gender']
            )
            
            if not mortality_trend.empty:
                mortality_chart = visualizer.create_mortality_chart(
                    mortality_trend,
                    f"{settings['selected_city']} 사망률 트렌드 (30일 기반)"
                )
                st.plotly_chart(mortality_chart, use_container_width=True, key="mortality_trend_chart_2")
    
    # 상세 분석 탭
    with tab4:
        st.subheader("📊 30일 데이터 상세 분석")
        
        # 필터 옵션
        filter_options = ui_components.display_filter_options(historical_data)
        
        # 필터링된 데이터
        filtered_data = historical_data.copy()
        filtered_data = filtered_data[filtered_data['temperature'] >= filter_options['min_temp']]
        
        if not filtered_data.empty:
            st.success(f"✅ 필터링된 데이터: {len(filtered_data)}개 (30일 중)")
            
            # 필터링된 데이터 통계
            filtered_stats = calculate_statistics(filtered_data)
            display_statistics(filtered_stats)
            
            # 필터링된 데이터 차트
            filtered_chart = visualizer.create_weather_trend_chart(
                filtered_data,
                f"필터링된 데이터 - {settings['selected_city']} (30일)"
            )
            st.plotly_chart(filtered_chart, use_container_width=True, key="filtered_data_chart_2")
            
            # 필터링된 데이터 분석
            filtered_analysis = data_analyzer.analyze_30day_data(filtered_data)
            with st.expander("🔍 필터링된 데이터 분석"):
                ui_components.display_analysis_summary(filtered_analysis)
        else:
            st.warning("필터 조건에 맞는 데이터가 없습니다.")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        🌤️ 기상 기반 사망률 예측 시스템 (30일 데이터 특화) | 
        <a href='https://github.com/sinjaeu/env_danger_pred' target='_blank'>GitHub</a> |
        기상청 API Hub 연동
    </div>
    """,
    unsafe_allow_html=True
)