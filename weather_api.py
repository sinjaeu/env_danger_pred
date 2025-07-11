"""
기상청 API Hub 연동 모듈
실제 기상 데이터를 가져오는 기능을 담당합니다.
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st


class WeatherAPI:
    """기상청 API Hub 연동 클래스"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        # 기상청 API Hub의 정확한 URL (일자료 기간 조회)
        self.base_url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php"
        
        # 주요 도시별 기상관측소 코드 (기상청 ASOS 공식 지점번호)
        self.station_codes = {
            "서울": "108",      # 서울 (종로구 송월동)
            "부산": "159",      # 부산 (기장군 기장읍)
            "대구": "143",      # 대구 (동구 신천동)
            "인천": "112",      # 인천 (중구 신포동)
            "광주": "156",      # 광주 (북구 운암동)
            "대전": "133",      # 대전 (유성구 구암동)
            "울산": "152",      # 울산 (남구 삼산동)
            "제주": "184",      # 제주 (제주시 아라동)
            "춘천": "101",      # 춘천
            "강릉": "105",      # 강릉
            "청주": "131",      # 청주
            "전주": "146",      # 전주
            "목포": "165",      # 목포
            "여수": "168",      # 여수
            "포항": "138",      # 포항
            "창원": "155",      # 창원
            "거제": "185",      # 거제
            "통영": "162",      # 통영
            "진주": "192",      # 진주
            "밀양": "288",      # 밀양
            "구미": "279",      # 구미
            "상주": "137",      # 상주
            "안동": "136",      # 안동
            "영주": "272",      # 영주
            "영덕": "277",      # 영덕
            "울진": "130",      # 울진
            "동해": "106",      # 동해
            "태백": "216",      # 태백
            "정선": "217",      # 정선
            "서산": "129",      # 서산
            "천안": "232",      # 천안
            "보령": "235",      # 보령
            "부여": "236",      # 부여
            "금산": "238",      # 금산
            "홍천": "212",      # 홍천
            "원주": "114",      # 원주
            "영월": "121",      # 영월
            "충주": "127",      # 충주
            "제천": "221",      # 제천
            "보은": "226",      # 보은
            "옥천": "232",      # 옥천
            "영동": "243",      # 영동
            "추풍령": "135",    # 추풍령
            "철원": "95",       # 철원
            "동두천": "98",     # 동두천
            "파주": "99",       # 파주
            "양평": "202",      # 양평
            "이천": "203",      # 이천
            "인제": "211",      # 인제
            "고성": "184",      # 고성
            "속초": "90",       # 속초
            "양양": "104",      # 양양
            "강화": "201",      # 강화
            "백령도": "102",    # 백령도
            "울릉도": "115",    # 울릉도
            "독도": "188",      # 독도
            "서귀포": "189",    # 서귀포
            "고산": "185",      # 고산
            "성산": "188",      # 성산
            "흑산도": "169",    # 흑산도
            "완도": "170",      # 완도
            "진도": "175",      # 진도
            "흥해": "277",      # 흥해
            "울릉도": "115",    # 울릉도
            "추자도": "184",    # 추자도
            "제주": "184",      # 제주
            "고산": "185",      # 고산
            "성산": "188",      # 성산
            "서귀포": "189"     # 서귀포
        }
    
    def validate_api_key(self) -> bool:
        """API 키 유효성을 검증합니다."""
        if not self.api_key or self.api_key.strip() == "":
            return False
        
        # 간단한 API 요청으로 키 검증
        try:
            url = f"{self.base_url}?authKey={self.api_key}&stn=108&tm1=20240101&tm2=20240101&help=0"
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def get_weather_data(self, city: str, start_date: str, end_date: str) -> pd.DataFrame:
        """기상청 API에서 기상 데이터를 가져옵니다."""
        
        if not self.api_key:
            st.error("❌ API 키가 설정되지 않았습니다.")
            return pd.DataFrame()
        
        try:
            # 지점 코드 가져오기
            station_code = self.station_codes.get(city)
            if not station_code:
                st.error(f"❌ {city}의 지점 코드를 찾을 수 없습니다.")
                return pd.DataFrame()
            
            # API 요청 URL 및 파라미터
            url = 'https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php'
            params = {
                'authKey': self.api_key,
                'stn': station_code,
                'tm1': start_date,
                'tm2': end_date,
                'help': '0'
            }
            
            st.info(f"🌤️ {city}의 {start_date} ~ {end_date} 기상 데이터를 가져오는 중...")
            
            # API 요청
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # 응답 데이터 파싱
            data = response.text.strip()
            
            if not data or data.startswith('error'):
                st.warning(f"⚠️ {city}의 데이터를 가져올 수 없습니다.")
                return pd.DataFrame()
            
            # 데이터 파싱
            weather_data = []
            lines = data.split('\n')
            
            for line in lines[1:]:  # 헤더 제외
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 15:  # 충분한 컬럼이 있는지 확인
                        try:
                            # 날짜 파싱
                            date_str = parts[0]  # TM: 관측시각
                            if len(date_str) >= 8:
                                date = datetime.strptime(date_str[:8], '%Y%m%d')
                                
                                # 필요한 기상 데이터만 추출
                                # TA_AVG: 일 평균기온, TA_MAX: 최고기온, TA_MIN: 최저기온
                                # HM_AVG: 일 평균 상대습도
                                temp_avg = float(parts[10]) if parts[10] != '' else None  # TA_AVG
                                temp_max = float(parts[11]) if parts[11] != '' else None  # TA_MAX
                                temp_min = float(parts[12]) if parts[12] != '' else None  # TA_MIN
                                humidity_avg = float(parts[13]) if parts[13] != '' else None  # HM_AVG
                                
                                # 기본값 설정 (평균 기온과 평균 습도)
                                temperature = temp_avg if temp_avg is not None else 20.0
                                humidity = humidity_avg if humidity_avg is not None else 60.0
                                
                                weather_data.append({
                                    'date': date,
                                    'city': city,
                                    'temperature': round(temperature, 1),  # 평균 기온
                                    'temp_max': round(temp_max, 1) if temp_max is not None else None,  # 최고 기온
                                    'temp_min': round(temp_min, 1) if temp_min is not None else None,  # 최저 기온
                                    'humidity': round(humidity, 1),  # 평균 습도
                                    'month': date.month,
                                    'year': date.year
                                })
                                
                        except (ValueError, IndexError) as e:
                            continue  # 잘못된 데이터는 건너뛰기
            
            if weather_data:
                df = pd.DataFrame(weather_data)
                st.success(f"✅ {city}의 기상 데이터 {len(df)}개를 성공적으로 가져왔습니다.")
                
                # 데이터 요약 정보 표시
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("평균 기온", f"{df['temperature'].mean():.1f}°C")
                with col2:
                    st.metric("평균 습도", f"{df['humidity'].mean():.1f}%")
                with col3:
                    st.metric("데이터 수", len(df))
                
                return df
            else:
                st.warning(f"⚠️ {city}의 유효한 기상 데이터를 찾을 수 없습니다.")
                return pd.DataFrame()
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ API 요청 오류: {e}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"❌ 데이터 처리 오류: {e}")
            return pd.DataFrame()
    
    def get_historical_data(self, city: str, years: list) -> pd.DataFrame:
        """과거 여러 년도의 기상 데이터를 가져옵니다."""
        all_data = []
        
        for year in years:
            # st.info(f"{city}의 {year}년 기상 데이터를 가져오는 중...")
            
            # 해당 년도의 1월 1일부터 12월 31일까지
            start_date = f"{year}0101"
            end_date = f"{year}1231"
            
            df = self.get_weather_data(city, start_date, end_date)
            
            if not df.empty:
                all_data.append(df)
            else:
                # st.warning(f"{year}년 데이터를 가져올 수 없습니다.")
                pass
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def _parse_text_response(self, text_data: str, city: str) -> list:
        """기상청 API의 텍스트 형식 응답을 파싱합니다."""
        try:
            lines = text_data.split('\n')
            weather_data = []
            
            # #START7777 헤더를 찾아서 실제 데이터 시작 위치 확인
            data_start_index = -1
            for i, line in enumerate(lines):
                if '#START7777' in line:
                    data_start_index = i + 1
                    break
            
            if data_start_index == -1:
                st.error("데이터 시작 마커(#START7777)를 찾을 수 없습니다.")
                return []
            
            # 데이터 라인 찾기 (CSV 형식)
            for i in range(data_start_index, len(lines)):
                line = lines[i].strip()
                if not line or line.startswith('#') or line.startswith('7777'):
                    continue
                
                # CSV 형식 파싱 (쉼표로 구분)
                if len(line) > 10:  # 최소 길이 확인
                    try:
                        # 공백으로 분리하여 필드 찾기 (실제 응답은 공백으로 구분됨)
                        fields = line.split()
                        if len(fields) < 20:  # 최소 필드 수 확인
                            continue
                        
                        # 날짜 파싱 (첫 번째 필드: YYYYMMDD)
                        date_str = fields[0].strip()
                        if len(date_str) == 8 and date_str.isdigit():
                            date_obj = datetime.strptime(date_str, "%Y%m%d")
                        else:
                            continue
                        
                        # 지점번호 확인 (두 번째 필드)
                        station_code = fields[1].strip()
                        
                        # 기온 필드 찾기 (TA: 기온)
                        # 실제 데이터 분석: 11번째 필드(인덱스 10)가 기온 값
                        temp = None
                        if len(fields) > 10:
                            temp_str = fields[10].strip()
                            if temp_str and temp_str not in ['-9.0', '-99.0', '-9', '-99', '']:
                                try:
                                    temp = float(temp_str)
                                    # 현실적인 기온 범위 확인 (-50 ~ 50도)
                                    if not (-50 <= temp <= 50):
                                        temp = None
                                except ValueError:
                                    temp = None
                        
                        # 습도 필드 찾기 (HM: 상대습도)
                        # 실제 데이터 분석: 19번째 필드(인덱스 18)가 현실적인 습도 값
                        humidity = None
                        if len(fields) > 18:
                            humidity_str = fields[18].strip()
                            if humidity_str and humidity_str not in ['-9.0', '-99.0', '-9', '-99', '']:
                                try:
                                    humidity = float(humidity_str)
                                    # 현실적인 습도 범위 확인 (20 ~ 100%)
                                    if not (20 <= humidity <= 100):
                                        humidity = None
                                except ValueError:
                                    humidity = None
                        
                        # 기온과 습도가 모두 유효한 경우만 추가
                        if temp is not None and humidity is not None:
                            weather_data.append({
                                'date': date_obj,
                                'city': city,
                                'temperature': temp,
                                'humidity': humidity,
                                'month': date_obj.month,
                                'year': date_obj.year
                            })
                        
                    except (ValueError, IndexError) as e:
                        continue
            
            return weather_data
            
        except Exception as e:
            st.error(f"텍스트 파싱 중 오류: {e}")
            return []
    
    def _parse_json_response(self, data: dict, city: str) -> list:
        """기상청 API의 JSON 형식 응답을 파싱합니다."""
        try:
            weather_data = []
            
            # API 응답 구조 확인
            if isinstance(data, list):
                # 새로운 API Hub 형식 (직접 JSON 배열 응답)
                items = data
            elif 'response' in data:
                # 기존 공공데이터 포털 형식
                if 'body' in data['response'] and 'items' in data['response']['body']:
                    items = data['response']['body']['items']['item']
                else:
                    st.error("API 응답 구조가 예상과 다릅니다.")
                    return []
            else:
                # 단일 객체 응답
                items = [data]
            
            if not items:
                return []
            
            # 데이터프레임으로 변환
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
                            elif len(time_str) == 10: # YYYYMMDD 형식 (기존 형식)
                                date_obj = datetime.strptime(time_str, "%Y%m%d")
                            else:
                                date_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                            
                            weather_data.append({
                                'date': date_obj,
                                'city': city,
                                'temperature': temp,
                                'humidity': humidity,
                                'month': date_obj.month,
                                'year': date_obj.year
                            })
                        except ValueError as e:
                            continue
                            
                except (ValueError, KeyError) as e:
                    continue
            
            return weather_data
            
        except Exception as e:
            st.error(f"JSON 파싱 중 오류: {e}")
            return [] 