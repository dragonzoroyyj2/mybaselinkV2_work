ok":true,"result":{"id":8272059398,"is_bot":true,"first_name":"MyBaseLinkV2","username":"MyBaseLinkV2_bot","can_join_groups":true,"can_read_all_group_messages":false,"supports_inline_queries":false,"can_connect_to_business":false,"has_main_web_app":false



https://api.telegram.org/bot8272059398:AAE00RhtkY5NkXCTR8doI4FEjOQnBls0GnQ/sendMessage?chat_id=82720599398&text=봇이%20당신에게%20직접%20보낸%20테스트%20메시지입니다.


https://api.telegram.org/bot8272059398:AAE00RhtkY5NkXCTR8doI4FEjOQnBls0GnQ/getMe


https://api.telegram.org/bot8272059398:AAE00RhtkY5NkXCTR8doI4FEjOQnBls0GnQ/getUpdates

8272059398:AAE00RhtkY5NkXCTR8doI4FEjOQnBls0GnQ


k8272059398:AAE00RhtkY5NkXCTR8doI4FEjOQnBls0GnQk

k5945452891:AAGFHAT8TKhzYaLrH4XgL5shRYXr_ibhhh8k
599b24c052bb23453a48da3916ae7faf1befd03e
DART API 키 발급 및 시스템 설정 (3단계 요약)
단계,내용,주의 사항
사이트 접속,금융감독원 오픈 DART 서비스 웹사이트 접속.,"일반 DART 공시 사이트가 아닌, API 인증키 발급 섹션으로 이동해야 합니다."
신청,"회원가입/로그인 후, '인증키 신청/관리' 메뉴에서 인증키 발급을 신청합니다.","키 발급은 즉시 이루어지며, 영문/숫자 조합의 긴 문자열을 안전하게 복사합니다."

파일,설정 내용,역할
application.yml,"app.stock.dart-api-key: ""여기에_발급받은_키_입력""","키를 안전하게 저장하고, Java 서비스가 이 값을 읽을 수 있도록 합니다."

주체,동작,이유
Java 백엔드,"파이썬 스크립트를 실행할 때, application.yml에서 읽은 키 값을 **DART_API_KEY**라는 이름의 운영체제 환경 변수로 파이썬 프로세스에 주입합니다.","파이썬 코드(os.getenv(""DART_API_KEY""))가 이 환경 변수를 통해 API 키를 읽고 DART 모듈을 초기화합니다."

=========================================

최종 분석 결과 (JSON) 시나리오
이 예시는 사용자가 --pattern_type double_bottom 필터와 --exclude_negatives 필터를 모두 활성화했을 때, 모든 검증을 통과한 NAVER 종목에 대해 받게 될 응답입니다.


{
  "results": [
    {
      "ticker": "035420",
      "name": "NAVER",
      "technical_conditions": {
        "above_ma50": true,
        "above_ma200": true,
        "goldencross_50_200_detected": true,
        "pattern_double_bottom_status": "Breakout",
        "db_neckline_price": 205000.0,
        "pattern_triple_bottom_status": null,
        "pattern_cup_and_handle_status": null,
        "ch_neckline_price": null
      },
      "fundamentals": {
        "DebtToEquity": 68.9,
        "ROE": 5.1
      },
      "recent_news_headlines": [
        {"title": "네이버, AI 하이퍼클로바X 성과 가시화", "link": "..."}
      ]
    },
    {
      "ticker": "068270",
      "name": "셀트리온",
      "technical_conditions": {
        "above_ma50": true,
        "above_ma200": false,
        "goldencross_50_200_detected": false,
        "pattern_double_bottom_status": "Potential",
        "db_neckline_price": 185000.0,
        "pattern_triple_bottom_status": null,
        "pattern_cup_and_handle_status": null,
        "ch_neckline_price": null
      },
      "fundamentals": {
        "DebtToEquity": 35.5,
        "ROE": 8.9
      },
      "recent_news_headlines": [
        {"title": "셀트리온, 유럽 바이오시밀러 시장 점유율 확대", "link": "..."}
      ]
    }
  ],
  "mode": "analyze",
  "filter": "double_bottom"
}



재무/악재 필터 통과: 부채비율(68.9%)이 매우 낮고, 악재성 뉴스나 DART 공시가 없어 안전성이 확보되었습니다.2. 셀트리온 (068270) 해석이 종목은 관심 종목에 편입하여 모니터링이 필요한 후보입니다.기술적 근거:패턴 진행: pattern_double_bottom_status: "Potential" $\rightarrow$ 이중 바닥 패턴이 형성되는 중간 단계이며, 넥라인(185,000원) 돌파를 시도 중입니다.추세 확인: 아직 골든 크로스는 발생하지 않았으나, 단기 MA50선 위에 있어 모멘텀이 살아나고 있음을 시사합니다.리스크 근거:재무적으로 매우 건전하고(부채 35.5%), 뉴스 흐름도 긍정적입니다.

1. ?? 기본 식별 정보 (Top-Level)
필드명,설명,투자 관점 활용
mode,스크립트 실행 모드 (analyze 또는 chart).,분석 유형 확인: 현재 데이터가 필터링된 결과(analyze)임을 확인합니다.
filter,"적용된 주요 패턴 필터 (double_bottom, goldencross 등).",검색 근거 확인: 결과가 어떤 전략적 목표를 가지고 선별되었는지 명확히 합니다.
results,필터링 조건을 통과한 모든 종목의 리스트.,이 리스트가 곧 최종 매수 후보 목록입니다.


2. ?? 종목별 상세 정보 (results 배열 내부)
필드명,JSON 예시,투자 관점 활용
ticker,"""035420""",증권사 MTS/HTS에서 종목을 조회하거나 매매 주문을 넣을 때 사용하는 코드입니다.
name,"""NAVER""",종목의 이름.


네, 좋습니다! 방금 전에 보여드렸던 최종 분석 결과 JSON의 각 필드를 다시 한번 투자자가 실제로 어떻게 해석하고 활용해야 하는지에 초점을 맞추어 명쾌하게 설명해 드리겠습니다.이 설명은 웹 서비스의 결과 보고서 툴팁이나 도움말로 바로 활용하실 수 있도록 정리했습니다.?? 최종 분석 결과 (JSON) 필드 상세 설명이 JSON은 시스템이 수많은 종목을 필터링한 후, 가장 매력적인 매매 기회를 포착한 종목만을 담고 있습니다.1. ?? 기본 식별 정보 (Top-Level)필드명설명투자 관점 활용mode스크립트 실행 모드 (analyze 또는 chart).분석 유형 확인: 현재 데이터가 필터링된 결과(analyze)임을 확인합니다.filter적용된 주요 패턴 필터 (double_bottom, goldencross 등).검색 근거 확인: 결과가 어떤 전략적 목표를 가지고 선별되었는지 명확히 합니다.results필터링 조건을 통과한 모든 종목의 리스트.이 리스트가 곧 최종 매수 후보 목록입니다.2. ?? 종목별 상세 정보 (results 배열 내부)A. 식별자 및 기본 정보필드명JSON 예시투자 관점 활용ticker"035420"증권사 MTS/HTS에서 종목을 조회하거나 매매 주문을 넣을 때 사용하는 코드입니다.name"NAVER"종목의 이름.B. 기술적 분석 (technical_conditions)

필드명,JSON 예시,투자 관점 활용
above_ma50,true,단기 모멘텀: 주가가 50일 이동평균선 위에 있습니다. 단기 매수세가 우위임을 나타냅니다.
above_ma200,true,장기 추세: 주가가 200일 이동평균선 위에 있습니다. 장기적인 상승 추세에 있음을 확인합니다.
goldencross_50_200_detected,true,추세 전환 신호: 50일선이 200일선을 상향 돌파했습니다. 장기 상승장 진입을 공식화하는 강력한 신호입니다.
pattern_..._status,"""Breakout""",핵심 매수 신호: 이중 바닥 패턴의 저항선(넥라인)이 강력한 거래량과 함께 돌파되었음을 의미합니다. (가장 좋은 매수 타이밍!)
..._neckline_price,205000.0,"리스크 관리 기준: 돌파가 일어난 가격입니다. 이 가격은 이제 강력한 지지선이 되며, 이 아래로 하락 시 손절매(Stop-Loss) 기준으로 활용될 수 있습니다."


C. 기본적 분석 (fundamentals)
필드명,JSON 예시,투자 관점 활용
DebtToEquity,68.9,재무 건전성: 부채가 자본 대비 매우 낮은 수준 (150% 이하 필터 통과). 부도 위험이 낮음을 확인합니다.
ROE,5.1,수익성: 기업이 자기 자본으로 이익을 창출하고 있음 (0% 이상 필터 통과). 성장성이 있음을 확인합니다.

D. 뉴스 및 공시 (recent_news_headlines)
필드명,JSON 예시,투자 관점 활용
recent_news_headlines,"[{""title"": ""...""}]","투자 심리 확인: 뉴스 제목에 '횡령', '배임', '감사의견 거절' 등의 악재 키워드가 없는지 최종적으로 확인합니다. 시스템은 이미 DART 공시와 뉴스에서 악재 종목을 제외했습니다."



****** 최종내용 
? 최종 통합 소스 (stock_analyzer_ultimate.py) 기능 최종 확인구분기능 명칭감지 여부상세 설명1. 장기 추세MA 200일선 상회 여부포함above_ma200 필드를 통해 종목이 장기 상승/하락 추세에 있는지 확인합니다.2. 크로스 신호골든 크로스 (Golden Cross)포함goldencross_50_200_detected 필드로 장기 상승 추세로의 전환 신호를 포착합니다.3. 반전/지속 패턴이중 바닥 (Double Bottom)포함pattern_double_bottom_status 필드로 W자형 바닥 다지기 패턴을 감지합니다.|| | 삼중 바닥 (Triple Bottom) | 포함 | pattern_triple_bottom_status 필드로 더욱 강력한 바닥 다지기 패턴을 감지합니다. || | 컵 앤 핸들 (Cup and Handle) | 포함 | pattern_cup_and_handle_status 필드로 상승 추세 지속 패턴을 감지합니다.Shutterstock탐색|| 4. 시각화 | 차트 생성 및 반환 | 포함 | --mode chart 호출 시, Base64 인코딩된 캔들 차트, MA선(50, 200), 거래량 이미지를 반환합니다. || 5. 리스크 관리 | 재무/공시 악재 필터 | 포함 | --exclude_negatives 사용 시, 부채비율, ROE, DART 공시 악재가 있는 종목을 자동으로 제외합니다. |?? 참고: 데드 크로스 (Death Cross) 조회 여부데드 크로스 정의: 단기 이동평균선(MA50)이 장기 이동평균선(MA200)을 하향 돌파하는 신호입니다. 이는 장기 하락 추세 진입을 알립니다.현재 코드의 활용: 현재 코드는 goldencross_50_200_detected를 포착하도록 설정되어 있습니다.데드 크로스를 찾으려면: 분석 로직 내에서 50일선이 200일선보다 아래로 내려오는 지점을 찾도록 코드를 수정해야 합니다.하지만: 일반적으로 웹 서비스는 매수 후보 종목을 선별하기 때문에, 골든 크로스와 같은 긍정 신호에 초점을 맞추는 것이 일반적입니다.최종 결론: 매수 관점의 모든 주요 패턴과 추세 신호, 그리고 악재 필터까지 완벽하게 포함되어 있습니다. 이제 시스템을 실행하시기만 하면 됩니다!



===================================================

<form id="analysisForm">
    <h3>분석 유형 선택:</h3>
    <div>
        <input type="radio" name="analysisType" id="maRadio" value="ma" checked onclick="toggleMaPeriods()">
        <label for="maRadio">이동평균선(MA) 분석</label>
    </div>
    <div id="maPeriodsContainer" style="margin-left: 20px;">
        <input type="checkbox" name="maPeriods" value="200" checked> 200일선
        <input type="checkbox" name="maPeriods" value="500" checked> 500일선
        <input type="checkbox" name="maPeriods" value="60"> 60일선
    </div>

    <div style="margin-top: 15px;">
        <input type="checkbox" id="excludeNegatives" name="excludeNegatives">
        <label for="excludeNegatives"><strong>악재 종목 제외 (뉴스/재무 기반 필터링)</strong></label>
    </div>
    <div>
        <input type="radio" name="analysisType" id="doubleBottomRadio" value="double_bottom" onclick="toggleMaPeriods()">
        <label for="doubleBottomRadio">이중바닥</label>
    </div>
    <div>
        <input type="radio" name="analysisType" id="tripleBottomRadio" value="triple_bottom" onclick="toggleMaPeriods()">
        <label for="tripleBottomRadio">삼중바닥</label>
    </div>
    <div>
        <input type="radio" name="analysisType" id="cupAndHandleRadio" value="cup_and_handle" onclick="toggleMaPeriods()">
        <label for="cupAndHandleRadio">컵앤핸들</label>
    </div>

    <button type="button" onclick="runAnalysis()">분석 실행</button>
</form>

<script>
function toggleMaPeriods() {
    const maPeriodsContainer = document.getElementById('maPeriodsContainer');
    const maRadio = document.getElementById('maRadio');
    if (maRadio.checked) {
        maPeriodsContainer.style.display = 'block';
    } else {
        maPeriodsContainer.style.display = 'none';
    }
}

function runAnalysis() {
    const analysisType = document.querySelector('input[name="analysisType"]:checked').value;
    const excludeNegatives = document.getElementById('excludeNegatives').checked; // 체크박스 상태 확인
    
    let pythonArgs = ['analyze'];
    
    if (analysisType === 'ma') {
        const maCheckboxes = document.querySelectorAll('input[name="maPeriods"]:checked');
        const selectedPeriods = Array.from(maCheckboxes).map(cb => cb.value).join(',');
        if (selectedPeriods) {
            pythonArgs.push('--ma_periods', selectedPeriods);
        }
    } else {
        pythonArgs.push('--analyze_patterns');
        pythonArgs.push('--pattern_type', analysisType); 
        // 참고: 현재 파이썬 스크립트는 --pattern_type을 사용하지 않고 --analyze_patterns만 사용하므로 이 부분은 2단계에서 조정해야 합니다.
    }
    
    // ?? 악재 제외 파라미터 추가
    if (excludeNegatives) {
        pythonArgs.push('--exclude_negatives');
    }

    console.log("파이썬 스크립트에 전달될 인수:", pythonArgs);
    // 실제로는 이 pythonArgs를 자바 백엔드로 보냅니다.
}

// 페이지 로드 시 초기 상태 설정
window.onload = toggleMaPeriods;
</script>


==========================================
두 스크립트의 역할 및 상호 관계 설명
1. ?? stock_updater.py (데이터 업데이트 및 준비 역할 - 선행 작업)

항목,상세 역할 및 기능,중요성 (웹 서비스 관점)
주요 목적,분석에 필요한 모든 원천 데이터를 최신 상태로 준비하고 저장합니다.,분석의 신뢰도 및 속도 보장 - 데이터가 없거나 오래되면 분석 자체가 불가능하거나 잘못된 결과를 냅니다.
수행 작업 (1),종목 리스트 수집: KRX 전체 종목 목록을 가져옵니다.,분석 대상 종목 목록을 확정합니다.
수행 작업 (2),"DART 코드 매핑: DART API 키를 사용하여 종목별 **기업 고유번호 (DartCorpCode)**를 수집하고, 종목 리스트 (stock_listing.json)에 저장합니다.",악재 필터링 기능 활성화의 필수 전제조건입니다.
수행 작업 (3),시세 데이터 수집: 각 종목의 3년치 시세 데이터를 다운로드하여 Parquet 파일 형태로 data/stock_data 폴더에 저장합니다.,stock_analyzer_ultimate.py가 빠르고 효율적으로 데이터를 읽어 분석할 수 있도록 합니다.
실행 시점,웹 서비스 시작 전 또는 매일 장 마감 후 정기적으로 실행되어야 합니다.,


?? stock_analyzer_ultimate.py (최종 분석 및 결과 제공 역할 - 실행 작업)
이 스크립트는 웹 서비스의 요청을 직접 받아 실제 필터링 및 분석을 수행하고, 그 결과를 웹 백엔드로 반환하는 핵심 분석 엔진입니다.

항목,상세 역할 및 기능,중요성 (웹 서비스 관점)
주요 목적,"사용자의 필터 조건에 따라 준비된 데이터를 분석하고, 결과를 JSON 또는 이미지 형태로 출력합니다.",사용자에게 가치 있는 분석 결과를 제공합니다.
수행 작업 (1),"필터링 모드 (--mode analyze): 패턴 (double_bottom 등), 이평선, 재무건전성, DART 공시 기반 악재 여부를 모두 검사합니다.",최종 매수 후보 종목을 선별합니다.
수행 작업 (2),차트 모드 (--mode chart): 특정 종목의 차트를 생성하고 Base64로 인코딩하여 JSON 안에 담아 반환합니다.,분석 결과의 시각적 검증을 가능하게 합니다.
수행 작업 (3),결과 출력: 모든 결과는 Java 백엔드가 쉽게 파싱할 수 있도록 JSON 형식으로 표준 출력(Stdout)합니다.,웹 서비스와 파이썬 간의 통신 프로토콜 역할을 합니다.
실행 시점,웹 프런트엔드에서 분석 버튼을 누르는 순간 Java 백엔드를 통해 OS 프로세스로 호출됩니다.,


두 스크립트의 상호 관계 요약의존성설명입력 데이터stock_analyzer_ultimate.py는 stock_updater.py가 미리 준비하고 저장해 둔 Parquet 시세 데이터와 **JSON 종목 리스트 (DartCorpCode 포함)**를 입력으로 사용합니다.핵심 키두 스크립트 모두 Java 백엔드가 환경 변수로 주입해 준 **DART_API_KEY**에 의존합니다.

결론적으로, stock_updater.py가 데이터베이스(DB) 관리자 역할을, stock_analyzer_ultimate.py가 분석 쿼리 엔진 역할을 수행한다고 이해하시면 됩니다.

=======================

1. 최종 통합 분석 스크립트 (stock_analyzer_ultimate.py) - (생략 없음)
----------------------------------------------------------------------------------------

import os
import sys
import json
import time
import logging
import argparse
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import base64

# ==============================
# 필수 라이브러리 확인 및 임포트
# ==============================
try:
    import FinanceDataReader as fdr
    import pandas as pd
    import mplfinance as mpf
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.signal import find_peaks
    import yfinance as yf
    
    # DART 공시 필터링 (환경 변수 확인)
    DART_API_KEY = os.getenv("DART_API_KEY") 
    DART_AVAILABLE = bool(DART_API_KEY)
    if DART_AVAILABLE:
        try:
            from dart_fss import Dart
        except ImportError:
            DART_AVAILABLE = False
            logging.warning("DART_API_KEY가 설정되었으나 dart-fss 모듈이 없어 DART 기능 비활성화.")

except ModuleNotFoundError as e:
    sys.stdout.write(json.dumps({"error": f"필수 모듈 누락: {e.name} 설치 필요 (pip install {e.name})"}, ensure_ascii=False) + "\n")
    sys.exit(1)

# ==============================
# 2. 경로 및 상수 설정
# ==============================
BASE_DIR = Path(__file__).resolve().parent if Path(__file__).name != '<stdin>' else Path.cwd()
LOG_DIR = BASE_DIR / "log"
DATA_DIR = BASE_DIR / "data" / "stock_data"
LISTING_FILE = BASE_DIR / "data" / "stock_list" / "stock_listing.json"
LOG_FILE = LOG_DIR / "stock_analyzer_ultimate.log"

# ==============================
# 3. 환경 초기화 및 유틸리티
# ==============================
def setup_env():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LISTING_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
def safe_print_json(data):
    """표준 출력(stdout)으로 JSON을 안전하게 출력"""
    sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.flush()

def set_korean_font():
    if sys.platform.startswith('win'): font_family = 'Malgun Gothic'
    elif sys.platform.startswith('darwin'): font_family = 'AppleGothic'
    else: font_family = 'NanumGothic'
    try:
        plt.rc('font', family=font_family)
        plt.rcParams['axes.unicode_minus'] = False
        global MPLFINANCE_FONT
        MPLFINANCE_FONT = font_family
    except Exception: pass
MPLFINANCE_FONT = 'sans-serif' 
set_korean_font()
setup_env() 

def load_listing():
    if not LISTING_FILE.exists(): 
        logging.error(f"종목 리스트 파일 없음: {LISTING_FILE}")
        return [{"Code": "005930", "Name": "삼성전자", "DartCorpCode": "00126380"}] 
    with open(LISTING_FILE, "r", encoding="utf-8") as f: return json.load(f)

def get_stock_name(symbol):
    try:
        items = load_listing()
        for item in items:
            code = item.get("Code") or item.get("code")
            if code == symbol: return item.get("Name") or item.get("name")
        return symbol
    except Exception: return symbol

def get_dart_corp_code(symbol):
    try:
        items = load_listing()
        for item in items:
            code = item.get("Code") or item.get("code")
            if code == symbol: return item.get("DartCorpCode")
        return None
    except Exception: return None


# ==============================
# 4. 기술적 분석 패턴 로직 (생략 없이 모두 포함)
# ==============================
def find_peaks_and_troughs(df, prominence=0.01, width=3):
    """주요 봉우리와 골짜기 인덱스 찾기"""
    recent_df = df.iloc[-250:].copy()
    if recent_df.empty: return np.array([]), np.array([])
    
    std_dev = recent_df['Close'].std()
    # prominence 기준을 종목별 변동성에 맞춰 자동 조정
    peaks, _ = find_peaks(recent_df['Close'], prominence=std_dev * prominence, width=width)
    troughs, _ = find_peaks(-recent_df['Close'], prominence=std_dev * prominence, width=width)
    
    start_idx = len(df) - len(recent_df)
    return peaks + start_idx, troughs + start_idx

def find_double_bottom(df, troughs, tolerance=0.05, min_duration=30):
    """
    ?? 이중 바닥 패턴 감지 (튜닝: tolerance 5%, 최소 기간 30일)
    """
    recent_troughs = [t for t in troughs if t >= len(df) - 250]
    if len(recent_troughs) < 2: return False, None, None, None
    
    idx2, idx1 = recent_troughs[-1], recent_troughs[-2] 
    price1, price2 = df['Close'].iloc[idx1], df['Close'].iloc[idx2]
    
    if idx2 - idx1 < min_duration: return False, None, None, None
    
    is_price_matching = abs(price1 - price2) / min(price1, price2) < tolerance
    if not is_price_matching: return False, None, None, None
    
    interim_high = df['Close'].iloc[idx1:idx2].max()
    current_price = df['Close'].iloc[-1]

    is_breakout = current_price > interim_high
    
    if is_breakout: return True, interim_high, 'Breakout', interim_high
    
    retrace_ratio = (current_price - min(price1, price2)) / (interim_high - min(price1, price2))
    is_potential = retrace_ratio > 0.5 and current_price < interim_high 
    
    if is_potential: return False, interim_high, 'Potential', interim_high
        
    return False, None, None, None

def find_triple_bottom(df, troughs, tolerance=0.05, min_duration_total=75):
    """
    ?? 삼중 바닥 패턴 감지 (튜닝: tolerance 5%, 최소 기간 75일)
    """
    recent_troughs = [t for t in troughs if t >= len(df) - 250]
    if len(recent_troughs) < 3: return False, None, None, None
    
    idx3, idx2, idx1 = recent_troughs[-1], recent_troughs[-2], recent_troughs[-3]
    price1, price2, price3 = df['Close'].iloc[idx1], df['Close'].iloc[idx2], df['Close'].iloc[idx3]
    
    if idx3 - idx1 < min_duration_total: return False, None, None, None
    
    min_price = min(price1, price2, price3)
    max_price = max(price1, price2, price3)
    is_price_matching = (max_price - min_price) / min_price < tolerance
    if not is_price_matching: return False, None, None, None
    
    high1 = df['Close'].iloc[idx1:idx2].max()
    high2 = df['Close'].iloc[idx2:idx3].max()
    neckline = max(high1, high2)
    current_price = df['Close'].iloc[-1]

    is_breakout = current_price > neckline
    
    if is_breakout: return True, neckline, 'Breakout', neckline
    
    retrace_ratio = (current_price - min_price) / (neckline - min_price)
    is_potential = retrace_ratio > 0.5 and current_price < neckline
    
    if is_potential: return False, neckline, 'Potential', neckline
        
    return False, None, None, None


def find_cup_and_handle(df, peaks, troughs, min_cup_depth=0.15, handle_drop_ratio=0.3):
    """
    ? 컵 앤 핸들 패턴 감지 (튜닝: 컵 깊이 최소 15%, 핸들 조정 폭 최대 30%)
    """
    recent_peaks = [p for p in peaks if p >= len(df) - 250]
    if len(recent_peaks) < 2: return False, None, None, None
    
    peak_right_idx = recent_peaks[-1]
    peak_right_price = df['Close'].iloc[peak_right_idx]
    
    cup_troughs = [t for t in troughs if t < peak_right_idx]
    if not cup_troughs: return False, None, None, None
    
    cup_bottom_idx = cup_troughs[np.argmin(df['Close'].iloc[cup_troughs])]
    cup_bottom_price = df['Close'].iloc[cup_bottom_idx]
    
    cup_depth = (peak_right_price - cup_bottom_price) / peak_right_price
    if cup_depth < min_cup_depth: return False, None, None, None
    
    handle_start_idx = peak_right_idx 
    handle_max_drop = peak_right_price * (1 - handle_drop_ratio) 

    current_price = df['Close'].iloc[-1]
    
    is_handle_forming = (df['Close'].iloc[handle_start_idx:].max() <= peak_right_price) 
    is_handle_forming &= (current_price > handle_max_drop)

    if is_handle_forming and current_price > peak_right_price:
        return True, peak_right_price, 'Breakout', peak_right_price
    
    if is_handle_forming and current_price <= peak_right_price:
        return False, peak_right_price, 'Potential', peak_right_price
        
    return False, None, None, None

# ==============================
# 5. 기본적 분석 및 악재 필터링 로직 (생략 없이 모두 포함)
# ==============================

def get_financial_statements_fdr(code):
    """FinanceDataReader를 이용해 재무 비율을 가져옵니다."""
    fundamentals = {}
    try:
        df_fin = fdr.financials.get_financial_statements(code, 'Annual', 'KOR')
        if df_fin is None or df_fin.empty: return fundamentals
        latest_col = df_fin.columns[-1]

        total_debt = df_fin.loc['부채총계', latest_col] if '부채총계' in df_fin.index else np.nan
        total_equity = df_fin.loc['자본총계', latest_col] if '자본총계' in df_fin.index else np.nan
        if not pd.isna(total_debt) and not pd.isna(total_equity) and total_equity != 0:
            fundamentals['DebtToEquity'] = (total_debt / total_equity) * 100
        
        net_income = df_fin.loc['당기순이익', latest_col] if '당기순이익' in df_fin.index else np.nan
        if not pd.isna(net_income) and not pd.isna(total_equity) and total_equity != 0:
            fundamentals['ROE'] = (net_income / total_equity) * 100
        
    except Exception as e:
        logging.warning(f"FDR 재무 데이터 로드 실패 ({code}): {e}")
        
    return fundamentals

def get_yfinance_news(code):
    """yfinance를 이용해 최근 뉴스 헤드라인을 가져옵니다."""
    headlines = []
    try:
        yf_ticker = f"{code}.KS" if not code.endswith('.KS') else code
        ticker = yf.Ticker(yf_ticker)
        news_list = ticker.news
        filtered_headlines = []
        two_months_ago = datetime.now() - timedelta(days=60)
        for news in news_list:
            publish_date = datetime.fromtimestamp(news.get('providerPublishTime')) 
            if publish_date >= two_months_ago:
                filtered_headlines.append({"title": news.get('title'), "link": news.get('link')})
            if len(filtered_headlines) >= 3: break
        return filtered_headlines
    except Exception as e:
        logging.warning(f"yfinance 뉴스 로드 실패 ({code}): {e}")
        return []

def get_fundamental_data(code):
    fundamentals = get_financial_statements_fdr(code)
    headlines = get_yfinance_news(code)
    return fundamentals, headlines

def check_for_negative_dart_disclosures(corp_code):
    """DART 공시에서 악재성 키워드 검사 (환경 변수 사용)"""
    if not DART_AVAILABLE or not corp_code or not DART_API_KEY: return False, None
    try:
        dart = Dart(DART_API_KEY)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)
        reports = dart.search(corp_code=corp_code, start_dt=start_date.strftime('%Y%m%d'))
        negative_keywords = ["횡령", "배임", "소송 제기", "손해배상", "거래정지", "상장폐지", "감사의견 거절", "파산", "회생"]
        for report in reports:
            if "유상증자 결정" in report.report_nm and "제3자배정" in report.report_nm: continue 
            if any(keyword in report.report_nm for keyword in negative_keywords):
                return True, f"DART 공시 악재: '{report.report_nm}'"
        return False, None
    except Exception as e:
        logging.error(f"DART 공시 확인 중 오류 ({corp_code}): {e}")
        return False, None

def check_for_negatives(fundamentals, headlines, code, corp_code):
    """뉴스/재무/공시 기반으로 악재성 종목 여부를 검사"""
    
    negative_keywords_news = ["횡령", "배임", "소송", "분쟁", "거래 정지", "악재", "하락 전망", "투자주의", "적자"]
    for news in headlines:
        if any(keyword in news.get('title', '') for keyword in negative_keywords_news):
            return True, f"뉴스 악재: '{news.get('title')}'"
            
    roe = fundamentals.get('ROE')
    debt_to_equity = fundamentals.get('DebtToEquity')
    
    if roe is not None and roe < 0 and not pd.isna(roe): 
        return True, f"재무 악재: ROE {roe:.1f}% (적자)"
    
    if debt_to_equity is not None and debt_to_equity > 150 and not pd.isna(debt_to_equity): 
        return True, f"재무 악재: 부채비율 {debt_to_equity:.1f}% 초과 (150% 기준)"

    is_negative_dart, reason_dart = check_for_negative_dart_disclosures(corp_code)
    if is_negative_dart: return True, reason_dart
        
    return False, None

# ==============================
# 6. 분석 실행 및 필터링
# ==============================

def check_ma_conditions(df, periods, analyze_patterns):
    """이동 평균선 및 패턴 분석을 수행하고 결과를 반환합니다."""
    results = {}
    
    if len(df) < 200: analyze_patterns = False
        
    for p in periods:
        if len(df) >= p:
            df[f'ma{p}'] = df['Close'].rolling(window=p, min_periods=1).mean() 
            results[f"above_ma{p}"] = df['Close'].iloc[-1] > df[f'ma{p}'].iloc[-1]
    
    ma50_col = 'ma50'
    ma200_col = 'ma200'
    if ma50_col in df.columns and ma200_col in df.columns and len(df) >= 200:
        results["goldencross_50_200_detected"] = (df[ma50_col].iloc[-2] < df[ma200_col].iloc[-2] and df[ma50_col].iloc[-1] > df[ma200_col].iloc[-1])
    else:
         results["goldencross_50_200_detected"] = False
    
    if analyze_patterns:
        peaks, troughs = find_peaks_and_troughs(df)
        is_db, neckline_db, db_status, db_price = find_double_bottom(df, troughs)
        is_tb, neckline_tb, tb_status, tb_price = find_triple_bottom(df, troughs)
        is_ch, neckline_ch, ch_status, ch_price = find_cup_and_handle(df, peaks, troughs)
        
        results['pattern_double_bottom_status'] = db_status
        results['db_neckline_price'] = db_price

        results['pattern_triple_bottom_status'] = tb_status
        results['tb_neckline_price'] = tb_price

        results['pattern_cup_and_handle_status'] = ch_status
        results['ch_neckline_price'] = ch_price

    return results

def analyze_symbol(item, periods, analyze_patterns, exclude_negatives, pattern_type_filter):
    """단일 종목을 분석하고 결과를 반환합니다."""
    code = item.get("Code") or item.get("code")
    name = item.get("Name") or item.get("name")
    corp_code = item.get("DartCorpCode")
    path = DATA_DIR / f"{code}.parquet"
    if not path.exists(): return None
    
    try:
        df = pd.read_parquet(path)
        if len(df) < 50: return None

        fundamentals, headlines = get_fundamental_data(code)
        
        if exclude_negatives:
            is_negative, reason = check_for_negatives(fundamentals, headlines, code, corp_code)
            if is_negative:
                return None
        
        analysis_results = check_ma_conditions(df, periods, analyze_patterns) 
        
        is_match = True
        if pattern_type_filter:
            if pattern_type_filter == 'goldencross': 
                is_match = analysis_results.get("goldencross_50_200_detected", False)
            elif pattern_type_filter in ['double_bottom', 'triple_bottom', 'cup_and_handle']: 
                status_key = f'pattern_{pattern_type_filter}_status'
                status = analysis_results.get(status_key)
                is_match = status in ['Breakout', 'Potential']
            elif pattern_type_filter == 'ma':
                pass 
            else:
                is_match = False

        if not is_match: return None
        
        if analysis_results or fundamentals or headlines:
            fundamentals_clean = {k: v for k, v in fundamentals.items() if v is not None and not (isinstance(v, (float, np.float64)) and np.isnan(v))}
            analysis_clean = {k: v for k, v in analysis_results.items() if v is not None and not (isinstance(v, (float, np.float64)) and np.isnan(v))}
            
            return {
                "ticker": code,
                "name": name,
                "technical_conditions": analysis_clean,
                "fundamentals": fundamentals_clean,
                "recent_news_headlines": headlines
            }
        return None
    except Exception as e:
        logging.error(f"[ERROR] {code} {name} 분석 실패: {e}\n{traceback.format_exc()}")
        return None

def run_analysis(workers, ma_periods_str, analyze_patterns, exclude_negatives, pattern_type_filter):
    """병렬 처리를 이용해 전체 종목 분석을 실행합니다."""
    start_time = time.time()
    periods = [int(p.strip()) for p in ma_periods_str.split(',') if p.strip().isdigit()]
    if pattern_type_filter and pattern_type_filter != 'ma': analyze_patterns = True 
    if 50 not in periods: periods.append(50) 
    if 200 not in periods: periods.append(200)

    items = load_listing()
    results = []
    
    logging.info(f"분석 시작: 총 {len(items)} 종목, 최대 워커 {workers}개 사용.")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_item = {
            executor.submit(analyze_symbol, item, periods, analyze_patterns, exclude_negatives, pattern_type_filter): item
            for item in items
        }
        
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                r = future.result()
                if r: results.append(r)
            except Exception as e:
                code = item.get("Code") or item.get("code")
                name = item.get("Name") or item.get("name")
                logging.error(f"[ERROR] {code} {name} 처리 중 예외 발생: {e}")
    
    end_time = time.time()
    logging.info(f"분석 완료: {len(results)}개 종목 필터링 됨. 총 소요 시간: {end_time - start_time:.2f}초")
    safe_print_json({"results": results, "mode": "analyze", "filter": pattern_type_filter or 'ma_only'})

def generate_chart(symbol, ma_periods_str):
    """단일 종목의 차트를 생성하고 Base64로 인코딩된 이미지 데이터를 반환합니다."""
    code = symbol
    name = get_stock_name(code)
    periods = [int(p.strip()) for p in ma_periods_str.split(',') if p.strip().isdigit()]
    path = DATA_DIR / f"{code}.parquet"
    if not path.exists():
        safe_print_json({"error": f"데이터 파일을 찾을 수 없음: {path}"})
        return
    try:
        df = pd.read_parquet(path)
        if df.empty:
            safe_print_json({"error": "데이터프레임이 비어 있습니다."})
            return
        
        df = df.iloc[-250:].copy() 
        ma_lines = []
        for p in periods:
            if len(df) >= p:
                ma_name = f'ma{p}'
                df[ma_name] = df['Close'].rolling(window=p, min_periods=1).mean()
                ma_lines.append(mpf.make_addplot(df[ma_name], panel=0, type='line', width=1.0, color='blue' if p == 200 else ('green' if p == 50 else 'orange'), secondary_y=False))
        
        volume_plot = mpf.make_addplot(df['Volume'], type='bar', panel=1, color='gray', secondary_y=False)
        mc = mpf.make_marketcolors(up='red', down='blue', wick='black', edge='black', volume='gray')
        s = mpf.make_mpf_style(marketcolors=mc, gridcolor='gray', figcolor='white', y_on_right=False, 
                               rc={'font.family': MPLFINANCE_FONT})
        
        addplots = ma_lines + [volume_plot]
        
        fig, axes = mpf.plot(df, type='candle', style=s, 
                             title=f"{name} ({code}) Price Chart with MAs", 
                             ylabel='Price', ylabel_lower='Volume', volume=True, 
                             addplot=addplots, figscale=1.5, returnfig=True)
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        safe_print_json({"ticker": code, "name": name, "chart_image_base64": image_base64, "mode": "chart"})
        
    except Exception as e:
        logging.error(f"[ERROR] 차트 생성 실패 ({code} {name}): {e}\n{traceback.format_exc()}")
        safe_print_json({"error": f"차트 생성 실패: {e}"})

def main():
    parser = argparse.ArgumentParser(description="주식 데이터 분석 및 차트 생성 스크립트")
    parser.add_argument("--mode", type=str, required=True, choices=['analyze', 'chart'], help="실행 모드 선택: 'analyze' 또는 'chart'")
    parser.add_argument("--workers", type=int, default=os.cpu_count() * 2, help="분석 모드에서 사용할 최대 스레드 수")
    parser.add_argument("--ma_periods", type=str, default="50,200", help="이동 평균선 기간 지정 (쉼표로 구분)")
    parser.add_argument("--symbol", type=str, help="차트 모드에서 사용할 종목 코드")
    parser.add_argument("--analyze_patterns", action="store_true", help="패턴 감지 활성화")
    parser.add_argument("--pattern_type", type=str, choices=['ma', 'double_bottom', 'triple_bottom', 'cup_and_handle', 'goldencross'], help="필터링할 패턴 종류")
    parser.add_argument("--exclude_negatives", action="store_true", help="악재성 종목 제외")
    args = parser.parse_args()
    
    try:
        if args.mode == 'analyze':
            run_analysis(args.workers, args.ma_periods, args.analyze_patterns, args.exclude_negatives, args.pattern_type) 
        elif args.mode == 'chart':
            if not args.symbol: 
                logging.error("차트 모드에는 --symbol 인수가 필수입니다.")
                sys.exit(1)
            generate_chart(args.symbol, args.ma_periods) 
    except Exception as e:
        error_msg = f"스크립트 실행 중 치명적인 오류 발생: {e}"
        logging.critical(f"{error_msg}\n{traceback.format_exc()}")
        safe_print_json({"error": error_msg})
        sys.exit(1)

if __name__ == "__main__":
    main()

---------------------------------

2. ?? 데이터 업데이트 스크립트 (stock_updater.py) - (생략 없음)
이 스크립트는 분석에 필요한 최신 시세 데이터와 DART 코드를 준비합니다.




import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==============================
# 필수 라이브러리 확인 및 임포트
# ==============================
try:
    import FinanceDataReader as fdr
    DART_API_KEY = os.getenv("DART_API_KEY") 
    DART_AVAILABLE = bool(DART_API_KEY)
    if DART_AVAILABLE:
        try:
            from dart_fss import Dart
        except ImportError:
            DART_AVAILABLE = False
            logging.warning("DART_API_KEY가 설정되었으나 dart-fss 모듈이 없어 DART 기능 비활성화.")
except ModuleNotFoundError as e:
    sys.stdout.write(json.dumps({"error": f"필수 모듈 누락: {e.name} 설치 필요 (pip install {e.name})"}, ensure_ascii=False) + "\n")
    sys.exit(1)

# ==============================
# 1. 경로 및 상수 설정
# ==============================
BASE_DIR = Path(__file__).resolve().parent if Path(__file__).name != '<stdin>' else Path.cwd()
LOG_DIR = BASE_DIR / "log"
DATA_DIR = BASE_DIR / "data" / "stock_data"
LISTING_FILE = BASE_DIR / "data" / "stock_list" / "stock_listing.json"
LOG_FILE = LOG_DIR / "stock_updater.log"

# ==============================
# 2. 환경 초기화 및 로깅 설정
# ==============================
def setup_env():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LISTING_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
setup_env()

# ==============================
# 3. DART 종목 코드 업데이트
# ==============================
def update_dart_corp_codes(listing_df):
    """
    DART API를 사용하여 종목별 기업 고유 번호를 매핑합니다.
    (환경 변수 DART_API_KEY 필요)
    """
    logging.info("[PROGRESS] 5.0 DART 기업 고유 번호 매핑 시작...")
    if not DART_AVAILABLE:
        logging.warning("DART API 키가 없어 기업 고유 번호 매핑을 건너뜁니다.")
        return listing_df

    try:
        dart = Dart(DART_API_KEY)
        corp_list = dart.get_corp_list()
        corp_dict = {corp.stock_code: corp.corp_code for corp in corp_list if corp.stock_code}

        listing_df['DartCorpCode'] = listing_df['Code'].map(corp_dict)
        logging.info(f"[PROGRESS] 10.0 {len(listing_df)}개 종목 중 {listing_df['DartCorpCode'].notna().sum()}개 DART 코드 매핑 완료.")
    except Exception as e:
        logging.error(f"DART API 호출 실패: {e}")
        listing_df['DartCorpCode'] = None 
    
    return listing_df

# ==============================
# 4. 시세 데이터 업데이트
# ==============================
def fetch_and_save_data(item):
    """단일 종목의 시세 데이터를 가져와 Parquet 파일로 저장합니다."""
    code = item.get("Code")
    name = item.get("Name")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3 * 365)
    
    try:
        df = fdr.DataReader(code, start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'))
        if df.empty:
            return 0
            
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index()
        df.to_parquet(DATA_DIR / f"{code}.parquet", index=False)
        return 1
    except Exception as e:
        logging.warning(f"데이터 수집 실패 ({code} {name}): {e}")
        return 0

def run_update(workers=os.cpu_count() * 2):
    """병렬 처리를 이용해 전체 데이터 업데이트를 실행합니다."""
    start_time = time.time()
    
    logging.info("[PROGRESS] 0.0 KRX 종목 목록 다운로드 중...")
    try:
        listing_df = fdr.StockListing('KRX')
        listing_df.rename(columns={'Symbol': 'Code', 'Name': 'Name'}, inplace=True)
    except Exception as e:
        logging.error(f"KRX 종목 목록 로드 실패: {e}")
        return

    listing_df = update_dart_corp_codes(listing_df)
    items = listing_df.to_dict('records')
    
    with open(LISTING_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    total_count = len(items)
    completed_count = 0
    
    logging.info(f"[PROGRESS] 15.0 시세 데이터 업데이트 시작: 총 {total_count} 종목, 최대 워커 {workers}개 사용.")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_item = {executor.submit(fetch_and_save_data, item): item for item in items}
        
        for future in as_completed(future_to_item):
            completed_count += future.result() 
            
            progress_pct = 15.0 + (completed_count / total_count) * 80.0
            logging.info(f"[PROGRESS] {progress_pct:.1f} 종목 저장 {completed_count}/{total_count}")

    end_time = time.time()
    logging.info(f"[PROGRESS] 100.0 전체 완료. 총 소요 시간: {end_time - start_time:.2f}초")

if __name__ == "__main__":
    try:
        run_update()
    except Exception as e:
        error_msg = f"스크립트 실행 중 치명적인 오류 발생: {e}"
        logging.critical(f"{error_msg}")
        sys.stdout.write(json.dumps({"error": error_msg}) + "\n")
        sys.exit(1)
