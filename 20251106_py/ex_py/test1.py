# -*- coding: utf-8 -*-
# 1. 파일 인코딩 문제를 해결하기 위한 선언입니다.
import requests
import json # JSON 데이터를 다루기 위해 추가합니다.

# --- 설정값 변경: 반드시 YOUR_API_KEY를 발급받은 키로 교체하세요! ---
API_KEY = "599b24c052bb23453a48da3916ae7faf1befd03e"  # <-- 여기에 발급받은 키를 넣으세요!
CORP_CODE = "00126380"    # 삼성전자 고유번호

# --- API 요청 정보 ---
base_url = "https://opendart.fss.or.kr/api/company.json" 
params = {
    'crtfc_key': API_KEY,
    'corp_code': CORP_CODE
}

print(f"[{CORP_CODE}] 회사 개요 정보를 요청합니다...")

# --- 데이터 요청 및 응답 ---
try:
    response = requests.get(base_url, params=params)
    
    # 2. 응답 데이터의 인코딩을 명시적으로 UTF-8로 설정하여 오류를 방지합니다.
    response.encoding = 'utf-8' 
    
    # JSON 형식으로 데이터 파싱
    data = response.json()
    
    # 결과 출력
    if data.get('status') == '000':
        print("✅ Dart API 연결 및 데이터 조회 성공!")
        print("---------------------------------------")
        print(f"회사명: {data.get('corp_name')}")
        print(f"종목코드: {data.get('stock_code')}")
        print(f"CEO: {data.get('ceo_nm')}")
        print(f"주소: {data.get('adres')}")
        print("---------------------------------------")
        
    else:
        # 오류 메시지를 출력합니다.
        print(f"❌ 데이터 조회 오류 (Status: {data.get('status')})")
        print(f"   메시지: {data.get('message', '알 수 없는 오류')}")

except requests.exceptions.RequestException as e:
    print(f"❌ 네트워크 또는 요청 오류가 발생했습니다: {e}")
except json.JSONDecodeError:
    print("❌ 응답 데이터 파싱 오류: Dart 서버에서 올바른 JSON을 받지 못했습니다.")
    print(f"   RAW 응답: {response.text}")