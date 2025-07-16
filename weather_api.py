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
            response.encoding = 'euc-kr'  # 한글 인코딩 설정
            response.raise_for_status()
            
            # 응답 데이터 파싱
            data = response.text.strip()
            
            # 디버깅을 위한 응답 정보 표시
            st.info(f"📡 API 응답 상태: {response.status_code}")
            st.info(f"📄 응답 길이: {len(data)} 문자")
            
            if not data or data.startswith('error'):
                st.warning(f"⚠️ {city}의 데이터를 가져올 수 없습니다.")
                st.info(f"📄 응답 내용: {data[:200]}...")
                return pd.DataFrame()
            
            # 응답 형식 확인 및 파싱
            weather_data = []
            
            # JSON 형식인지 확인
            if data.startswith('{') or data.startswith('['):
                try:
                    json_data = json.loads(data)
                    weather_data = self._parse_json_response(json_data, city)
                except json.JSONDecodeError:
                    st.warning("JSON 파싱 실패, 텍스트 형식으로 시도합니다.")
                    weather_data = self._parse_text_response(data, city)
            else:
                # 텍스트 형식으로 파싱
                weather_data = self._parse_text_response(data, city)
            
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
                st.info(f"📄 응답 내용 미리보기: {data[:500]}...")
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
        from datetime import datetime
        lines = text_data.split('\n')
        
        # 헤더 정보 추출 (실제 API 응답 구조에 맞춤)
        header_line = None
        for line in lines:
            if line.strip().startswith('# YYMMDD'):
                header_line = line.replace('#', '').strip()
                break
        
        if not header_line:
            st.warning("헤더 라인을 찾을 수 없습니다.")
            return []
        
        # 헤더에서 컬럼 위치 찾기
        header_cols = header_line.split()
        
        try:
            # 컬럼 인덱스 찾기
            idx_ymd = header_cols.index('YYMMDD')
            
            # TA (기온) 컬럼들 찾기
            ta_indices = [i for i, col in enumerate(header_cols) if col == 'TA']
            # HM (습도) 컬럼들 찾기  
            hm_indices = [i for i, col in enumerate(header_cols) if col == 'HM']
            
            # 첫 번째 TA는 일 평균기온, 첫 번째 HM은 일 평균습도로 사용
            if not ta_indices or not hm_indices:
                st.warning("TA 또는 HM 컬럼을 찾을 수 없습니다.")
                return []
            
            idx_ta = ta_indices[0]
            idx_hm = hm_indices[0]
            
            st.info(f"📊 컬럼 위치 - YYMMDD: {idx_ymd}, TA: {idx_ta}, HM: {idx_hm}")
            
        except (ValueError, IndexError) as e:
            st.warning(f"헤더 인덱스 추출 오류: {e}")
            st.info(f"헤더 컬럼: {header_cols}")
            return []

        # 데이터 파싱
        weather_data = []
        for line in lines:
            # 헤더나 구분자 라인은 제외
            if (not line.strip() or 
                line.startswith('#') or 
                line.startswith('7777') or
                not line[0].isdigit()):
                continue
            
            fields = line.split()
            
            # 필드 수 확인
            if len(fields) <= max(idx_ymd, idx_ta, idx_hm):
                continue
            
            try:
                # 날짜 파싱
                date_str = fields[idx_ymd]
                if len(date_str) == 8:  # YYYYMMDD
                    date = datetime.strptime(date_str, "%Y%m%d")
                else:
                    continue
                
                # 기온 파싱
                ta_str = fields[idx_ta]
                if ta_str == '-9.0' or ta_str == '-9':
                    continue  # 결측값
                ta = float(ta_str)
                
                # 습도 파싱
                hm_str = fields[idx_hm]
                if hm_str == '-9.0' or hm_str == '-9':
                    continue  # 결측값
                hm = float(hm_str)
                
                weather_data.append({
                    'date': date,
                    'city': city,
                    'temperature': ta,
                    'humidity': hm,
                    'month': date.month,
                    'year': date.year
                })
                
            except (ValueError, IndexError) as e:
                continue
        
        st.info(f"📊 파싱된 데이터: {len(weather_data)}개")
        return weather_data
    
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