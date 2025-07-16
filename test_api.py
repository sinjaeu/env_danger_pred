import requests
import json
from datetime import datetime

def test_weather_api():
    """기상청 API 호출을 테스트합니다."""
    
    api_key = "bwpOEu3kR9-KThLt5FffxA"
    url = "https://apihub.kma.go.kr/api/typ01/url/kma_sfcdd3.php"
    
    params = {
        'authKey': api_key,
        'stn': '108',  # 서울
        'tm1': '20250611',
        'tm2': '20250615',  # 5일치 테스트
        'help': '0'
    }
    
    print("🌤️ 기상청 API 테스트 시작...")
    print(f"📡 URL: {url}")
    print(f"🔑 API Key: {api_key[:10]}...")
    print(f"📍 지점: 서울 (108)")
    print(f"📅 날짜: 2025-06-11 ~ 2025-06-15")
    print("-" * 50)
    
    try:
        print("📡 API 요청 중...")
        response = requests.get(url, params=params, timeout=30)
        response.encoding = 'euc-kr'  # 한글 인코딩 설정
        
        print(f"📊 응답 상태 코드: {response.status_code}")
        print(f"📏 응답 길이: {len(response.text)} 문자")
        print("-" * 50)
        
        if response.status_code == 200:
            print("✅ API 호출 성공!")
            
            # 전체 응답 출력
            print("📄 전체 응답 내용:")
            print(response.text)
            print("-" * 50)
            
            # 응답 분석
            data = response.text.strip()
            lines = data.split('\n')
            
            print(f"📄 총 {len(lines)}줄")
            print("-" * 50)
            
            # 각 줄별 분석
            print("📋 줄별 분석:")
            for i, line in enumerate(lines):
                print(f"  {i+1:2d}: {line}")
            
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"📄 오류 응답: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    test_weather_api() 