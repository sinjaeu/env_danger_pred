"""
기상청 API Hub 연동 모듈
실제 기상 데이터를 가져오는 기능을 담당합니다.
"""

import requests
import json
import pandas as pd
from datetime import datetime
import streamlit as st


class WeatherAPI:
    """기상청 API Hub 연동 클래스"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # 기상청 API Hub의 정확한 URL
        self.base_url = "https://apihub.kma.go.kr/api/json"
        
        # 주요 도시별 기상관측소 코드
        self.station_codes = {
            "서울": "108",      # 서울
            "부산": "159",      # 부산
            "대구": "143",      # 대구
            "인천": "112",      # 인천
            "광주": "156",      # 광주
            "대전": "133",      # 대전
            "울산": "152",      # 울산
            "제주": "184"       # 제주
        }
    
    def validate_api_key(self) -> bool:
        """API 키 유효성을 검증합니다."""
        if not self.api_key or self.api_key.strip() == "":
            return False
        
        # 간단한 API 요청으로 키 검증
        try:
            params = {
                'authKey': self.api_key,
                'stn': '108',  # 서울
                'tm': '20240101',
                'help': '0'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def get_weather_data(self, city: str, start_date: str, end_date: str) -> pd.DataFrame:
        """기상청 API Hub에서 특정 도시의 기상 데이터를 가져옵니다."""
        
        if city not in self.station_codes:
            st.error(f"지원하지 않는 도시입니다: {city}")
            return pd.DataFrame()
        
        station_code = self.station_codes[city]
        
        try:
            # 기본 API 파라미터 (기상청 API Hub 문서에 따른 형식)
            params = {
                'authKey': self.api_key,
                'stn': station_code,
                'tm': start_date,
                'help': '0'
            }
            
            # 헤더 설정
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            # API 요청 URL과 파라미터 디버깅
            st.info(f"API 요청 URL: {self.base_url}")
            st.info(f"API 파라미터: {params}")
            
            # GET 요청 (파라미터가 URL에 포함됨)
            response = requests.get(self.base_url, params=params, headers=headers, timeout=30)
            
            # 응답 상태 확인 (이미 위에서 200 체크했지만 추가 확인)
            if response.status_code != 200:
                st.error(f"API 요청 실패: HTTP {response.status_code}")
                st.error(f"응답 내용: {response.text}")
                st.error(f"요청 URL: {response.url}")
                return pd.DataFrame()
            
            # JSON 파싱 시도
            try:
                data = response.json()
            except json.JSONDecodeError:
                st.error("API 응답이 JSON 형식이 아닙니다.")
                st.error(f"응답 내용: {response.text[:500]}")
                return pd.DataFrame()
            
            # API 응답 구조 확인 (새로운 API Hub 형식)
            st.info(f"API 응답 구조: {list(data.keys()) if isinstance(data, dict) else 'List response'}")
            
            # 응답 구조에 따라 데이터 추출
            if isinstance(data, list):
                # 새로운 API Hub 형식 (직접 JSON 배열 응답)
                items = data
            elif 'response' in data:
                # 기존 공공데이터 포털 형식
                if 'body' in data['response'] and 'items' in data['response']['body']:
                    items = data['response']['body']['items']['item']
                else:
                    st.error("API 응답 구조가 예상과 다릅니다.")
                    return pd.DataFrame()
            else:
                # 단일 객체 응답
                items = [data]
            
            if not items:
                st.warning(f"{city}의 {start_date}~{end_date} 기간 데이터가 없습니다.")
                return pd.DataFrame()
            
            # 데이터프레임으로 변환
            weather_data = []
            for item in items:
                try:
                    # 새로운 API 문서에 따른 필드명 사용
                    temp = None
                    humidity = None
                    
                    # 기온 필드 (TA: 기온 °C)
                    if 'TA' in item and item['TA'] not in [-999, None, '', '']:
                        temp = float(item['TA'])
                    
                    # 습도 필드 (HM: 상대습도 %)
                    if 'HM' in item and item['HM'] not in [-999, None, '', '']:
                        humidity = float(item['HM'])
                    
                    # 시간 필드 (TM: 관측시각 KST)
                    time_str = None
                    if 'TM' in item and item['TM']:
                        time_str = str(item['TM'])
                    
                    if temp is not None and humidity is not None and time_str:
                        try:
                            # 새로운 API 문서에 따른 시간 형식 처리
                            # TM: 관측시각 (KST) - 년월일시분 형식
                            if len(time_str) == 12:  # YYYYMMDDHHMM 형식
                                date_obj = datetime.strptime(time_str, "%Y%m%d%H%M")
                            elif len(time_str) == 8:  # YYYYMMDD 형식
                                date_obj = datetime.strptime(time_str, "%Y%m%d")
                            elif 'T' in time_str:  # ISO 형식
                                date_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                            elif len(time_str) == 14:  # YYYYMMDDHHMMSS 형식
                                date_obj = datetime.strptime(time_str, "%Y%m%d%H%M%S")
                            elif len(time_str) == 19:  # YYYY-MM-DD HH:MM:SS 형식
                                date_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                            else:
                                date_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                            
                            weather_data.append({
                                'date': date_obj,
                                'city': city,
                                'temperature': temp,
                                'humidity': humidity
                            })
                        except ValueError as e:
                            continue
                            
                except (ValueError, KeyError) as e:
                    continue
            
            if not weather_data:
                st.warning(f"{city}의 유효한 기상 데이터가 없습니다.")
                st.info(f"첫 번째 아이템 구조: {items[0] if items else 'No items'}")
                return pd.DataFrame()
            
            df = pd.DataFrame(weather_data)
            
            # 계절 정보 추가
            df['month'] = df['date'].dt.month
            df['year'] = df['date'].dt.year
            
            def get_season(month):
                if month in [3, 4, 5]:
                    return "봄"
                elif month in [6, 7, 8]:
                    return "여름"
                elif month in [9, 10, 11]:
                    return "가을"
                else:
                    return "겨울"
            
            df['season'] = df['month'].apply(get_season)
            
            return df
            
        except requests.exceptions.RequestException as e:
            st.error(f"API 요청 중 오류가 발생했습니다: {e}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"데이터 처리 중 오류가 발생했습니다: {e}")
            st.error(f"오류 상세: {str(e)}")
            return pd.DataFrame()
    
    def get_historical_data(self, city: str, years: list) -> pd.DataFrame:
        """과거 여러 년도의 기상 데이터를 가져옵니다."""
        all_data = []
        
        for year in years:
            st.info(f"{city}의 {year}년 기상 데이터를 가져오는 중...")
            
            # 해당 년도의 1월 1일부터 12월 31일까지
            start_date = f"{year}0101"
            end_date = f"{year}1231"
            
            df = self.get_weather_data(city, start_date, end_date)
            
            if not df.empty:
                all_data.append(df)
            else:
                st.warning(f"{year}년 데이터를 가져올 수 없습니다.")
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame() 