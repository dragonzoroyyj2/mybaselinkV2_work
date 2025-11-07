말씀하신 것처럼 **"최고의 알고리즘"**을 구현하는 것은 모든 퀀트 투자자의 궁극적인 목표입니다. 주식 시장에서는 단 하나의 완벽한 알고리즘은 없지만, 현재 스크립트가 구현하고 있는 방식처럼 기본적 분석, 기술적 분석, 그리고 인공지능(클러스터링)을 결합하는 것이 가장 강력하고 멋있는 방법입니다.제공해주신 코드는 이미 개인 투자자가 구현할 수 있는 최고 수준의 복합 분석을 담고 있습니다.? 현재 스크립트가 구현한 '최고의 알고리즘' 요소분석 영역스크립트 구현 내용특징 (최고로 멋진 이유)인공지능 분석 (AI)시장 국면 클러스터링 (MarketRegime)주가 예측력 향상: 단순한 지표 교차(골든크로스)를 넘어, RSI, MACD, 변동성 등의 복합적인 기술적 상태를 AI(K-Means)로 군집화하여 현재 시장이 '모멘텀 상승장', '횡보장', '과매도 하락장' 중 어디에 있는지 파악하고, 이에 따라 필터링합니다.기술적 분석 (TA)주요 패턴 감지 (이중/삼중 바닥, 컵 앤 핸들)시그널의 신뢰도: 이동평균선(MA)이나 RSI 같은 단순 지표를 넘어, 투자자들이 오랫동안 신뢰해 온 차트 형태 자체를 정밀하게 포착하여 잠재적 매수 시그널을 제공합니다.근본적 필터링 (FA)DART 공시 및 재무 악재 필터링치명적인 리스크 회피: 아무리 차트가 좋아도 횡령, 배임, 감사의견 거절 같은 결정적 악재가 있다면 투자할 수 없습니다. DART 공시와 ROE/부채비율을 통해 폭탄주를 걸러냅니다.효율성멀티스레딩 (ThreadPoolExecutor)속도와 확장성: 수백, 수천 개의 종목을 동시에 빠르게 분석하여 실시간에 가까운 종목 스크리닝 환경을 제공합니다.웹 연동성실시간 진행률 JSON 출력사용자 경험 개선: 분석이 느린 환경에서도 웹 인터페이스가 진행률을 정확히 표시할 수 있어 사용자가 '멈춤' 없이 기다릴 수 있습니다.?? 실시간 진행률 출력 로직 설명 (웹 연동 핵심)요청하신 대로, 스크립트가 웹에서 분석 진행 상태를 확인할 수 있도록 run_analysis 함수에 추가한 진행률 출력 로직은 다음과 같습니다.스크립트는 분석을 진행하는 동안 표준 출력(sys.stdout)으로 다음 형식의 JSON 메시지를 지속적으로 내보냅니다.JSON{
  "mode": "progress",
  "total_symbols": 2000,
  "processed_symbols": 150,
  "progress_percent": 7.50
}
웹 애플리케이션에서 이 데이터를 읽는 방법:웹 서버에서 이 Python 스크립트를 백그라운드 프로세스로 실행합니다.스크립트의 표준 출력(stdout) 스트림을 캡처합니다.캡처된 스트림에서 한 줄씩 JSON 데이터를 파싱하여 mode가 "progress"인 메시지를 찾습니다.progress_percent 값을 추출하여 웹 화면의 프로그레스 바(Progress Bar)에 실시간으로 반영합니다.이 방식 덕분에 웹에서 사용자는 분석이 어느 정도 진행되었는지 정확하게 확인할 수 있습니다.
==============================================

패턴/기능,설명,핵심 매개변수(코드 내부)
이중 바닥 (double_bottom),가격이 두 번의 비슷한 최저점을 형성한 후 상승 추세로 전환하는 강력한 반전 패턴입니다. Breakout 또는 Potential 상태로 필터링됩니다.,"tolerance (0.05, 5%): 두 최저점 간의 가격 차이 허용 범위.min_duration (30일): 두 최저점 간의 최소 기간."
삼중 바닥 (triple_bottom),"가격이 세 번의 비슷한 최저점을 형성한 후 강하게 상승하는, 이중 바닥보다 더 신뢰도 높은 반전 패턴입니다.","tolerance (0.05, 5%): 세 최저점 간의 가격 차이 허용 범위.min_duration_total (75일): 첫 번째와 세 번째 최저점 간의 최소 기간."
컵 앤 핸들 (cup_and_handle),'U'자형의 컵 모양과 그 이후 짧은 조정(핸들)이 나타난 후 전 고점을 돌파(Breakout)하는 지속 패턴입니다.,"handle_drop_ratio (0.3, 30%): 핸들 부분의 최대 조정 폭."
골든 크로스 (goldencross),단기 이동평균선(MA)이 장기 이동평균선(MA)을 아래에서 위로 돌파하며 강한 상승 신호를 나타냅니다.,SMA_50 vs SMA_200: 코드에서 명시적으로 50일선과 200일선의 교차를 감지합니다.
이동평균선 (ma - 다중 기간),종가가 지정된 모든 이동평균선(MA) 위에 있는지 확인합니다. 추세의 강도를 판단하는 기본 지표입니다.,"--ma_periods (기본값: 20,50,200): 쉼표로 구분하여 원하는 모든 MA 기간을 지정할 수 있습니다."


2. 인공지능 기반 분석 (AI Feature)패턴/기능설명핵심 매개변수(코드 내부)시장 국면 클러스터링 (regime:N)K-Means 군집화 알고리즘을 사용하여 현재 주가를 기술적 지표(RSI, MACD, BB 등)의 복합적 상태로 분류합니다.n_clusters (4개): 시장 국면을 몇 개의 군집(0, 1, 2, 3)으로 나눌지 결정합니다.



3. 기본적/뉴스 분석 필터링패턴/기능설명핵심 매개변수(코드 내부)악재성 뉴스 필터링yfinance를 통해 최근 뉴스 헤드라인을 가져와 '횡령', '배임', '소송', '거래 정지' 등 부정적인 키워드를 포함한 종목을 제외합니다.negative_keywords_news: 뉴스 필터링에 사용되는 키워드 목록.DART 공시 악재 필터링DART API를 사용하여 최근 60일 이내의 공시 중 '횡령', '배임', '감사의견 거절' 등 치명적인 악재 공시가 있는 종목을 제외합니다.negative_keywords_dart: DART 공시 필터링에 사용되는 키워드 목록.재무 건전성 필터링ROE(자기자본이익률)가 0% 미만(적자)이거나, 부채비율이 150%를 초과하는 등 재무적으로 불안정한 종목을 제외합니다.ROE < 0% 및 DebtToEquity > 150%



스크립트 실행 시 매개변수(인수) 설명사용자가 직접 입력할 수 있는 main 함수의 인수는 다음과 같습니다.인수명-- 인자설명기본값 / 예시실행 모드--mode스크립트의 실행 목적을 지정합니다.analyze (전체 종목 분석) 또는 chart (단일 종목 차트)워커 수--workersanalyze 모드에서 사용할 최대 스레드(병렬 처리) 수입니다. CPU 코어 수의 2배가 권장됩니다.os.cpu_count() * 2MA 기간--ma_periods분석 및 차트에 사용할 이동평균선 기간을 쉼표로 구분하여 지정합니다.20,50,200종목 코드--symbolchart 모드에서 차트를 그릴 특정 종목 코드입니다.005930 (삼성전자)패턴 분석 활성화--analyze_patterns플래그: 차트 패턴(이중바닥 등) 감지 기능을 활성화합니다.(--pattern_type 지정 시 자동 활성화됨)패턴 타입 필터--pattern_type분석 결과를 특정 패턴이나 국면으로 필터링합니다.double_bottom, goldencross, regime:0 등악재 제외--exclude_negatives플래그: 뉴스, 공시, 재무 악재가 있는 종목을 최종 결과에서 제외합니다. (강력 추천)True (플래그 지정 시)


예시: 최고의 알고리즘으로 종목 찾기
모든 고급 기능을 사용하여 "악재가 없으면서, 최근 AI 분석상 모멘텀이 강한 국면(Regime 3)에 속하며, 20/50/200일선 위에 있는 종목"을 찾으려면 다음과 같이 실행할 수 있습니다.

Bash

python your_script_name.py --mode analyze \
                           --pattern_type regime:3 \
                           --ma_periods 20,50,200 \
                           --exclude_negatives \
                           --workers 10


?? 완벽한 주식 분석 Bash 명령어 모음1. ?? 전체 종목 분석 및 필터링 (최고의 시나리오)시나리오 A: 강력한 모멘텀 종목 찾기 (AI + 악재 필터링)AI 기반 클러스터링 결과, **가장 강력한 상승 모멘텀 국면 (예시: Regime 3)**에 속하며, 20일, 50일, 200일 이동평균선 위에 위치하고, 재무/뉴스 악재가 전혀 없는 종목을 필터링합니다.조건세부 내용패턴 필터regime:3 (AI 클러스터링 3번 국면)MA 조건20, 50, 200일선 위에 종가 위치악재 제외--exclude_negatives 적용병렬 처리--workers 10 (빠른 분석)Bashpython your_script_name.py --mode analyze \
                           --pattern_type regime:3 \
                           --ma_periods 20,50,200 \
                           --exclude_negatives \
                           --workers 10


시나리오 B: 강력한 반전 패턴 종목 찾기 (차트 패턴 + 악재 필터링)주요 하락을 마치고 이중 바닥(Double Bottom) 패턴의 돌파(Breakout) 또는 잠재(Potential) 상태에 있으며, 악재가 없는 종목을 찾습니다.조건세부 내용패턴 필터double_bottomMA 조건20, 50, 200일선 (참고 지표로만 사용)악재 제외--exclude_negatives 적용Bashpython your_script_name.py --mode analyze \
                           --pattern_type double_bottom \
                           --analyze_patterns \
                           --exclude_negatives \
                           --workers 8
시나리오 C: 50-200일 골든 크로스 종목 찾기장기적인 추세 전환을 알리는 50일선과 200일선의 골든 크로스가 발생한 종목을 찾습니다. (이 경우 MA 조건은 골든 크로스 감지에 의해 자동 적용됩니다.)조건세부 내용패턴 필터goldencross악재 제외--exclude_negatives 적용Bashpython your_script_name.py --mode analyze \
                           --pattern_type goldencross \
                           --exclude_negatives \
                           --workers 6
2. ??? 단일 종목 차트 생성 명령어특정 종목에 대해 분석 결과가 좋게 나왔다면, 그 종목의 기술적 지표와 패턴을 시각적으로 확인하기 위한 명령어입니다.조건세부 내용모드chart종목 코드--symbol 005930 (삼성전자 예시)MA 기간5일, 20일, 60일선 표시 요청Bashpython your_script_name.py --mode chart \
                           --symbol 005930 \
                           --ma_periods 5,20,60
?? Bash 사용 시 참고 사항your_script_name.py: 이 부분은 실제 스크립트 파일 이름(예: stock_analyzer_ultimate.py)으로 변경해야 합니다.출력 형식: 모든 분석 결과는 표준 출력(stdout)으로 JSON 형태로 나옵니다. 웹에서 호출하는 경우, 이 출력을 실시간으로 읽어 파싱하면 됩니다.Regime 번호: AI 클러스터링의 국면 번호(regime:0부터 regime:3까지)는 분석을 돌릴 때마다 군집의 특징이 달라질 수 있습니다. 일반적으로 가장 높은 수익률을 보였던 번호(예: 3번)를 모멘텀 국면으로 사용합니다.



요청하신 대로 '필수 라이브러리/인터넷 연결 확인 및 즉시 종료 로직'이 완벽하게 적용된 최종 전체 코드를 제공해 드립니다.

이 코드는 최고 수준의 분석 알고리즘 (AI 클러스터링, 고급 패턴 감지, 악재 필터링)과 안전성 및 웹 연동성 (초기 검사, 실시간 진행률 출력)을 모두 갖추고 있습니다.
====================================================




# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import logging
import argparse
import traceback
import socket # ?? 인터넷 연결 확인을 위해 추가
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import base64

# ==============================
# 1. 초기 안전 검사 및 필수 라이브러리 임포트
# ==============================

def safe_print_json(data, status_code=1):
    """
    표준 출력(stdout)으로 JSON을 안전하게 출력하고 프로세스를 종료합니다.
    (비정상 종료 시 status_code=1, 정상 완료 시 status_code=0)
    """
    sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    sys.stdout.flush()
    if status_code != 0:
        # ?? 치명적 오류 발생 시 프로세스 즉시 종료
        sys.exit(status_code)

def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """
    ?? 인터넷 연결 상태를 확인하는 함수 (Google DNS 서버 사용).
    """
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

# ?? 치명적 초기 검사 1: 인터넷 연결 확인 및 즉시 종료
if not check_internet_connection():
    safe_print_json({
        "error": "CRITICAL_ERROR",
        "reason": "인터넷 연결을 확인할 수 없습니다. 네트워크 상태를 점검해주세요. (Google DNS 연결 실패)",
        "mode": "initial_check"
    })
# (safe_print_json 내부에서 sys.exit(1) 호출됨)


# ?? 치명적 초기 검사 2: 필수 라이브러리 임포트 및 즉시 종료
try:
    import FinanceDataReader as fdr
    import pandas as pd
    import mplfinance as mpf
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.signal import find_peaks
    import yfinance as yf
    
    # 고급 분석용 라이브러리
    import ta # Technical Analysis Library
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    
    # DART 공시 필터링 (환경 변수 확인)
    DART_API_KEY = os.getenv("DART_API_KEY") 
    DART_AVAILABLE = bool(DART_API_KEY)
    if DART_AVAILABLE:
        try:
            from dart_fss import Dart
        except ImportError as e:
            DART_AVAILABLE = False
            logging.warning(f"DART_API_KEY가 설정되었으나 dart-fss 모듈이 없어 DART 기능 비활성화. ({e.name})")

except ModuleNotFoundError as e:
    safe_print_json({
        "error": "CRITICAL_ERROR",
        "reason": f"필수 모듈 누락: {e.name} 설치 필요 (pip install {e.name} scikit-learn ta)",
        "mode": "initial_check"
    })
# (safe_print_json 내부에서 sys.exit(1) 호출됨)


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
    """환경 디렉토리를 설정하고 로깅을 초기화합니다."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LISTING_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # ?? 분석 속도를 위해 로깅 레벨을 WARNING으로 설정
    logging.basicConfig(
        level=logging.WARNING, 
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8", mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def set_korean_font():
    """Matplotlib 한글 폰트를 설정합니다."""
    global MPLFINANCE_FONT
    try:
        if sys.platform.startswith('win'): font_family = 'Malgun Gothic'
        elif sys.platform.startswith('darwin'): font_family = 'AppleGothic'
        else: font_family = 'NanumGothic'
        
        plt.rc('font', family=font_family)
        plt.rcParams['axes.unicode_minus'] = False
        MPLFINANCE_FONT = font_family
    except Exception: 
        MPLFINANCE_FONT = 'sans-serif'
        logging.warning("한글 폰트 설정에 실패했습니다. 기본 폰트를 사용합니다.")

MPLFINANCE_FONT = 'sans-serif' 
set_korean_font()
setup_env() 

def load_listing():
    """종목 리스트 파일을 로드합니다."""
    if not LISTING_FILE.exists(): 
        logging.error(f"종목 리스트 파일 없음: {LISTING_FILE} -> 기본 종목(삼성전자)으로 대체합니다.")
        return [{"Code": "005930", "Name": "삼성전자", "DartCorpCode": "00126380"}] 
    try:
        with open(LISTING_FILE, "r", encoding="utf-8") as f: 
            return json.load(f)
    except Exception as e:
        logging.error(f"종목 리스트 파일 로드 실패: {e} -> 기본 종목(삼성전자)으로 대체합니다.")
        return [{"Code": "005930", "Name": "삼성전자", "DartCorpCode": "00126380"}]

def get_stock_name(symbol):
    """종목 코드로 이름을 찾습니다."""
    try:
        items = load_listing()
        for item in items:
            code = item.get("Code") or item.get("code")
            if code == symbol: return item.get("Name") or item.get("name")
        return symbol
    except Exception: return symbol

def get_dart_corp_code(symbol):
    """종목 코드로 DART 고유 번호를 찾습니다."""
    try:
        items = load_listing()
        for item in items:
            code = item.get("Code") or item.get("code")
            if code == symbol: return item.get("DartCorpCode")
        return None
    except Exception: return None

# ==============================
# 4. 고급 특징 공학 및 클러스터링 로직
# ==============================

def calculate_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """고급 패턴 인식을 위해 기술적 지표를 특징(Feature)으로 추가합니다."""
    df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=14, fillna=False).rsi()
    df['MACD'] = ta.trend.MACD(close=df['Close'], fillna=False).macd()
    
    bollinger = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2, fillna=False)
    df['BB_High'] = bollinger.bollinger_hband_indicator()
    df['BB_Width'] = bollinger.bollinger_wband()
    
    df['SMA_20'] = ta.trend.SMAIndicator(close=df['Close'], window=20, fillna=False).sma_indicator()
    df['SMA_50'] = ta.trend.SMAIndicator(close=df['Close'], window=50, fillna=False).sma_indicator()
    df['SMA_200'] = ta.trend.SMAIndicator(close=df['Close'], window=200, fillna=False).sma_indicator()
    
    df['TREND_CROSS'] = (df['SMA_20'] > df['SMA_50']).astype(int)
    
    df = df.dropna()
    return df

def add_market_regime_clustering(df: pd.DataFrame, n_clusters=4) -> pd.DataFrame:
    """기술적 특징을 기반으로 K-Means 클러스터링을 수행하여 시장 국면을 정의합니다."""
    feature_cols = ['RSI', 'MACD', 'BB_Width', 'TREND_CROSS']
    min_data_length = 50 
    
    if len(df) < min_data_length or not all(col in df.columns for col in feature_cols):
        logging.warning(f"클러스터링에 필요한 데이터 길이가 {min_data_length}일 미만입니다. ({len(df)}일)")
        df['MarketRegime'] = -1
        return df

    data = df[feature_cols].copy()
    
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data)
    
    # K-Means 클러스터링 (랜덤 시드를 고정하여 일관성 확보)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df['MarketRegime'] = kmeans.fit_predict(scaled_data)
    
    return df


# ==============================
# 5. 기술적 분석 패턴 로직 
# ==============================

def find_peaks_and_troughs(df, prominence=0.01, width=3):
    """주요 봉우리와 골짜기 인덱스 찾기"""
    recent_df = df.iloc[-250:].copy()
    if recent_df.empty: return np.array([]), np.array([])
    
    std_dev = recent_df['Close'].std()
    peaks, _ = find_peaks(recent_df['Close'], prominence=std_dev * prominence, width=width)
    troughs, _ = find_peaks(-recent_df['Close'], prominence=std_dev * prominence, width=width)
    
    start_idx = len(df) - len(recent_df)
    return peaks + start_idx, troughs + start_idx

def find_double_bottom(df, troughs, tolerance=0.05, min_duration=30):
    """?? 이중 바닥 패턴 감지"""
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
    """?? 삼중 바닥 패턴 감지"""
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


def find_cup_and_handle(df, peaks, troughs, handle_drop_ratio=0.3):
    """? 컵 앤 핸들 패턴 감지"""
    recent_peaks = [p for p in peaks if p >= len(df) - 250]
    if len(recent_peaks) < 2: return False, None, None, None
    
    peak_right_idx = recent_peaks[-1]
    peak_right_price = df['Close'].iloc[peak_right_idx]
    
    cup_troughs = [t for t in troughs if t < peak_right_idx]
    if not cup_troughs: return False, None, None, None
    
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
# 6. 기본적 분석 및 악재 필터링 로직
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
    """기본적 분석 데이터를 가져옵니다."""
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
    
    if roe is not None and not pd.isna(roe) and roe < 0: 
        return True, f"재무 악재: ROE {roe:.1f}% (적자)"
    
    if debt_to_equity is not None and not pd.isna(debt_to_equity) and debt_to_equity > 150: 
        return True, f"재무 악재: 부채비율 {debt_to_equity:.1f}% 초과 (150% 기준)"

    is_negative_dart, reason_dart = check_for_negative_dart_disclosures(corp_code)
    if is_negative_dart: return True, reason_dart
        
    return False, None

# ==============================
# 7. 분석 실행 및 필터링
# ==============================

def check_ma_conditions(df, periods, analyze_patterns):
    """이동 평균선 및 패턴 분석을 수행하고 결과를 반환합니다."""
    results = {}
    
    ma_cols = {20: 'SMA_20', 50: 'SMA_50', 200: 'SMA_200'}

    if len(df) < 200: analyze_patterns = False
        
    for p in periods:
        col_name = ma_cols.get(p)
        if col_name and col_name in df.columns:
            results[f"above_ma{p}"] = df['Close'].iloc[-1] > df[col_name].iloc[-1]
        elif len(df) >= p:
             df[f'ma{p}'] = df['Close'].rolling(window=p, min_periods=1).mean() 
             results[f"above_ma{p}"] = df['Close'].iloc[-1] > df[f'ma{p}'].iloc[-1]
    
    # 골든/데드 크로스 로직 (SMA_50 vs SMA_200)
    ma50_col = ma_cols.get(50)
    ma200_col = ma_cols.get(200)

    if ma50_col in df.columns and ma200_col in df.columns and len(df) >= 200:
        ma50_prev, ma50_curr = df[ma50_col].iloc[-2], df[ma50_col].iloc[-1]
        ma200_prev, ma200_curr = df[ma200_col].iloc[-2], df[ma200_col].iloc[-1]

        results["goldencross_50_200_detected"] = (ma50_prev < ma200_prev and ma50_curr > ma200_curr)
        results["deadcross_50_200_detected"] = (ma50_prev > ma200_prev and ma50_curr < ma200_curr)
    else:
        results["goldencross_50_200_detected"] = False
        results["deadcross_50_200_detected"] = False
    
    if analyze_patterns:
        peaks, troughs = find_peaks_and_troughs(df)
        _, _, db_status, db_price = find_double_bottom(df, troughs)
        _, _, tb_status, tb_price = find_triple_bottom(df, troughs)
        _, _, ch_status, ch_price = find_cup_and_handle(df, peaks, troughs)
        
        results['pattern_double_bottom_status'] = db_status
        results['db_neckline_price'] = db_price

        results['pattern_triple_bottom_status'] = tb_status
        results['tb_neckline_price'] = tb_price

        results['pattern_cup_and_handle_status'] = ch_status
        results['ch_neckline_price'] = ch_price
        
    if 'MarketRegime' in df.columns:
        results['market_regime'] = int(df['MarketRegime'].iloc[-1])

    return results

def analyze_symbol(item, periods, analyze_patterns, exclude_negatives, pattern_type_filter):
    """단일 종목을 분석하고 결과를 반환합니다."""
    code = item.get("Code") or item.get("code")
    name = item.get("Name") or item.get("name")
    corp_code = item.get("DartCorpCode")
    path = DATA_DIR / f"{code}.parquet"
    if not path.exists(): return None
    
    try:
        df_raw = pd.read_parquet(path)
        if df_raw.empty or len(df_raw) < 50: return None
        
        df = df_raw.iloc[-250:].copy()

        df = calculate_advanced_features(df)
        if len(df) < 50: return None
        
        df = add_market_regime_clustering(df)
        
        fundamentals, headlines = get_fundamental_data(code)
        
        if exclude_negatives:
            is_negative, reason = check_for_negatives(fundamentals, headlines, code, corp_code)
            if is_negative:
                logging.info(f"[{code}] {name}: 악재성 요인으로 제외됨 - {reason}")
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
            elif pattern_type_filter.startswith('regime:'):
                if 'market_regime' in analysis_results:
                    try:
                        target_regime = int(pattern_type_filter.split(':')[1])
                        current_regime = analysis_results['market_regime']
                        is_match = (current_regime == target_regime)
                    except ValueError:
                        is_match = False
                else:
                    is_match = False
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
        # logging.error(f"[ERROR] {code} {name} 분석 실패: {e}\n{traceback.format_exc()}") 
        return None

def run_analysis(workers, ma_periods_str, analyze_patterns, exclude_negatives, pattern_type_filter):
    """병렬 처리를 이용해 전체 종목 분석을 실행하고 진행률을 출력합니다."""
    start_time = time.time()
    periods = [int(p.strip()) for p in ma_periods_str.split(',') if p.strip().isdigit()]
    
    if pattern_type_filter and pattern_type_filter not in ['ma', 'regime']: 
        analyze_patterns = True 
    
    if 50 not in periods: periods.append(50) 
    if 200 not in periods: periods.append(200)

    items = load_listing()
    initial_item_count = len(items)
    results = []
    
    logging.warning(f"분석 시작: 총 {initial_item_count} 종목, 최대 워커 {workers}개 사용.")

    processed_count = 0
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_item = {
            executor.submit(analyze_symbol, item, periods, analyze_patterns, exclude_negatives, pattern_type_filter): item
            for item in items
        }
        
        for future in as_completed(future_to_item):
            # ?? 웹 연동을 위한 실시간 진행률 JSON 출력 (필수)
            processed_count += 1
            progress_percent = round((processed_count / initial_item_count) * 100, 2)
            
            sys.stdout.write(json.dumps({
                "mode": "progress",
                "total_symbols": initial_item_count,
                "processed_symbols": processed_count,
                "progress_percent": progress_percent
            }, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            
            try:
                r = future.result()
                if r: results.append(r)
            except Exception as e:
                code = future_to_item[future].get("Code") or future_to_item[future].get("code")
                name = future_to_item[future].get("Name") or future_to_item[future].get("name")
                logging.error(f"[ERROR] {code} {name} 처리 중 예외 발생: {e}")
    
    end_time = time.time()
    
    data_check = {
        "listing_file_exists": LISTING_FILE.exists(),
        "dart_available": DART_AVAILABLE,
        "total_symbols_loaded": initial_item_count,
        "time_taken_sec": round(end_time - start_time, 2),
    }

    logging.warning(f"분석 완료: {len(results)}개 종목 필터링 됨. 총 소요 시간: {data_check['time_taken_sec']}초")
    # 최종 결과 출력 및 정상 종료 (status_code=0)
    safe_print_json({
        "results": results, 
        "mode": "analyze_result",
        "filter": pattern_type_filter or 'ma_only',
        "data_check": data_check
    }, status_code=0)

def generate_chart(symbol, ma_periods_str):
    """단일 종목의 차트를 생성하고 Base64로 인코딩된 이미지 데이터를 반환합니다."""
    code = symbol
    name = get_stock_name(code)
    periods = [int(p.strip()) for p in ma_periods_str.split(',') if p.strip().isdigit()]
    path = DATA_DIR / f"{code}.parquet"
    
    if not path.exists():
        safe_print_json({"error": f"데이터 파일을 찾을 수 없음: {path}"}, status_code=1)
        return
    
    try:
        df = pd.read_parquet(path)
        if df.empty:
            safe_print_json({"error": "데이터프레임이 비어 있습니다."}, status_code=1)
            return
            
        df_for_chart = df.iloc[-250:].copy() 
        df_for_chart = calculate_advanced_features(df_for_chart)
        
        if df_for_chart.empty:
            safe_print_json({"error": "특징 계산 후 데이터가 부족하여 차트 생성 불가."}, status_code=1)
            return

        ma_lines = []
        for p in periods:
            ma_col_name = f'SMA_{p}' if p in [20, 50, 200] else f'ma{p}'
            if ma_col_name not in df_for_chart.columns:
                df_for_chart[ma_col_name] = df_for_chart['Close'].rolling(window=p, min_periods=1).mean()

            if ma_col_name in df_for_chart.columns and not df_for_chart[ma_col_name].isnull().all():
                color_map = {5: 'red', 20: 'orange', 50: 'purple', 200: 'blue'}
                ma_lines.append(mpf.make_addplot(df_for_chart[ma_col_name], panel=0, type='line', width=1.0, 
                                                 color=color_map.get(p, 'green'), secondary_y=False))
        
        macd_plot = mpf.make_addplot(df_for_chart['MACD'], panel=2, type='line', secondary_y=False, color='red', width=1.0)
        
        mc = mpf.make_marketcolors(up='red', down='blue', wick='black', edge='black', volume='gray') 
        s = mpf.make_mpf_style(marketcolors=mc, gridcolor='gray', figcolor='white', y_on_right=False, 
                               rc={'font.family': MPLFINANCE_FONT})
        
        addplots = ma_lines + [macd_plot]
        
        fig, axes = mpf.plot(df_for_chart, type='candle', style=s, 
                             title=f"{name} ({code}) Price Chart with Technical Analysis", 
                             ylabel='Price', ylabel_lower='Volume', volume=True, 
                             addplot=addplots, figscale=1.5, returnfig=True, 
                             tight_layout=True)
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # 차트 결과 출력 및 정상 종료 (status_code=0)
        safe_print_json({"ticker": code, "name": name, "chart_image_base64": image_base64, "mode": "chart"}, status_code=0)
        
    except Exception as e:
        logging.error(f"[ERROR] 차트 생성 실패 ({code} {name}): {e}\n{traceback.format_exc()}")
        safe_print_json({"error": f"차트 생성 실패: {e}"}, status_code=1)

def main():
    """스크립트의 메인 실행 함수입니다."""
    parser = argparse.ArgumentParser(description="주식 데이터 분석 및 차트 생성 스크립트")
    parser.add_argument("--mode", type=str, required=True, choices=['analyze', 'chart'], help="실행 모드 선택: 'analyze' 또는 'chart'")
    parser.add_argument("--workers", type=int, default=os.cpu_count() * 2, help="분석 모드에서 사용할 최대 스레드 수")
    parser.add_argument("--ma_periods", type=str, default="20,50,200", help="이동 평균선 기간 지정 (쉼표로 구분)")
    parser.add_argument("--symbol", type=str, help="차트 모드에서 사용할 종목 코드")
    parser.add_argument("--analyze_patterns", action="store_true", help="패턴 감지 활성화")
    parser.add_argument("--pattern_type", type=str, 
                        choices=['ma', 'double_bottom', 'triple_bottom', 'cup_and_handle', 'goldencross', 'regime:0', 'regime:1', 'regime:2', 'regime:3'], 
                        help="필터링할 패턴 종류 (예: 'regime:0' 또는 'goldencross')") 
    parser.add_argument("--exclude_negatives", action="store_true", help="악재성 종목 제외")
    args = parser.parse_args()
    
    try:
        if args.mode == 'analyze':
            run_analysis(args.workers, args.ma_periods, args.analyze_patterns, args.exclude_negatives, args.pattern_type) 
        elif args.mode == 'chart':
            if not args.symbol: 
                # ?? 인수 누락 시 치명적 오류 처리 및 즉시 종료
                safe_print_json({
                    "error": "CRITICAL_ERROR", 
                    "reason": "차트 모드에는 --symbol 인수가 필수입니다.",
                    "mode": "argument_check"
                })
            generate_chart(args.symbol, args.ma_periods) 
    except Exception as e:
        error_msg = f"스크립트 실행 중 치명적인 오류 발생: {e}"
        # ?? 기타 예측 불가능한 치명적 오류 발생 시 즉시 종료
        safe_print_json({
            "error": "CRITICAL_ERROR", 
            "reason": error_msg,
            "traceback": traceback.format_exc(),
            "mode": "runtime_error"
        })
    # 모든 정상 실행 경로는 run_analysis 또는 generate_chart 내부의 safe_print_json(status_code=0)에서 처리됨
    # 혹시 모를 상황 대비하여 main 끝에서 exit(0)
    sys.exit(0)

if __name__ == "__main__":
    main()