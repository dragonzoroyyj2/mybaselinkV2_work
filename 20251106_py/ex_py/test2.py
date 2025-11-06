# -*- coding: utf-8 -*-
import requests
import json

# --- 설정값: YOUR_API_KEY를 실제 키로 교체하세요! ---
API_KEY = "599b24c052bb23453a48da3916ae7faf1befd03e"  # <-- 여기에 발급받은 키를 넣으세요!
CORP_CODE = "00126380"    # 삼성전자 고유번호
BSNS_YEAR = "2024"        # 조회할 사업 연도
OPE_SE_CODE = "11013"     # 보고서 구분: 11013 (사업보고서)

# --- API 요청 정보 ---
base_url = "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json"
params = {
    'crtfc_key': API_KEY,
    'corp_code': CORP_CODE,
    'bsns_year': BSNS_YEAR,
    'reprt_code': OPE_SE_CODE
}

print(f"[{CORP_CODE}] {BSNS_YEAR}년 사업보고서의 재무제표를 요청합니다...")

# --- 데이터 요청 및 처리 ---
try:
    response = requests.get(base_url, params=params)
    response.encoding = 'utf-8' 
    data = response.json()
    
    if data.get('status') == '000':
        print("✅ 재무제표 데이터 조회 성공!")
        print("--------------------------------------------------")
        
        # 실제 데이터는 'list' 안에 배열 형태로 담겨 있습니다.
        if 'list' in data and data['list']:
            # 간단하게 데이터의 첫 5개 항목만 출력 (너무 길어지는 것 방지)
            print(f"총 {len(data['list'])}개 항목 중 상위 5개 항목:")
            
            for item in data['list'][:5]:
                print(f" - 계정명: {item['account_nm']}, 금액: {item['thstrm_amount']} (당기), {item['frmtrm_amount']} (전기)")
                
            print("--------------------------------------------------")
            
        else:
            print(f"⚠️ {BSNS_YEAR}년 삼성전자 사업보고서에 대한 재무 데이터가 없습니다.")

    else:
        print(f"❌ 데이터 조회 오류 (Status: {data.get('status')})")
        print(f"   메시지: {data.get('message', '알 수 없는 오류')}")

except Exception as e:
    print(f"❌ 예기치 않은 오류가 발생했습니다: {e}")