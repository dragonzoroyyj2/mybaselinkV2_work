# -*- coding: utf-8 -*-
"""
📘 athena_k_market_ai_prod_V2.0.py (최종 개선판 - 특징 공학 및 데이터 품질 강화)
--------------------------------------------
✅ 개선 1. 데이터 연동: 'Adj_Close' (수정 종가)를 기준으로 모든 분석 수행.
✅ 개선 2. 특징 공학 강화: ATR, CMF, Log Return의 통계량(Skew, Std) 추가.
✅ 개선 3. Market Regime: 강화된 특징을 기반으로 클러스터링 재정의.
✅ 안정화: 모든 패턴 로직 및 차트 JSON 출력 유지.
--------------------------------------------
"""

import os
import sys
import json
import time
import logging
import argparse
import traceback
import socket
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import glob

import pandas as pd
import numpy as np
import ta
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from scipy.signal import find_peaks

# ==============================
# 1. 초기 안전 검사 및 필수 라이브러리 임포트
# (생략)
# ==============================

def safe_print_json(data, status_code=1):
    """표준 출력(stdout)으로 JSON을 안전하게 출력하고 프로세스를 종료합니다."""
    try:
        sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=None, separators=(',', ':'), cls=CustomJsonEncoder) + "\n")
    except Exception as e:
        sys.stdout.write(json.dumps({"error": "JSON_SERIALIZATION_FAIL", "original_error": str(e)}, ensure_ascii=False) + "\n")
        
    sys.stdout.flush()
    if status_code != 0:
        sys.exit(status_code)

def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """간단한 소켓 연결을 통해 인터넷 연결 상태를 확인합니다."""
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

if not check_internet_connection():
    safe_print_json({"error": "CRITICAL_ERROR", "reason": "인터넷 연결을 확인할 수 없습니다.", "mode": "initial_check"})

# ==============================
# 1.5. JSON Custom Encoder 정의
# (생략)
# ==============================
class CustomJsonEncoder(json.JSONEncoder):
    """NumPy 타입 및 Pandas Timestamp를 표준 Python 타입으로 변환합니다."""
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32)):
            if np.isnan(obj):
                return None
            return float(obj)
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, (pd.Timestamp, datetime, np.datetime64)):
            return obj.strftime('%Y-%m-%d')
        return json.JSONEncoder.default(self, obj)


# ==============================
# 2. 경로 및 상수 설정
# ==============================
BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "log"
DATA_DIR = BASE_DIR / "data" / "stock_data" 
LISTING_FILE = BASE_DIR / "data" / "stock_list" / "stock_listing.json" 
CACHE_DIR = BASE_DIR / "cache" 
LOG_FILE = LOG_DIR / "stock_analyzer_ultimate.log"

# 분석 기준 컬럼을 'Adj_Close'로 변경하여 통일
PRICE_COL = 'Adj_Close'
HIGH_COL = 'High'
LOW_COL = 'Low'

# ==============================
# 3. 환경 초기화 및 유틸리티
# (생략 - 기존 유지)
# ==============================

def setup_env(log_level=logging.INFO):
    """환경 디렉토리를 설정하고 로깅을 초기화합니다."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LISTING_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8", mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_listing():
    """종목 리스트 파일 (stock_listing.json)을 로드합니다."""
    default_item = [{"Code": "005930", "Name": "삼성전자"}]
    if not LISTING_FILE.exists():
        logging.error(f"종목 리스트 파일 없음: {LISTING_FILE}")
        return default_item
    try:
        with open(LISTING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"종목 리스트 파일 로드 실패: {e}")
        return default_item

def get_stock_name(symbol):
    """종목 코드로 이름을 찾아 반환합니다."""
    try:
        items = load_listing()
        for item in items:
            code = item.get("Code") or item.get("code")
            if code == symbol: return item.get("Name") or item.get("name")
        return symbol
    except Exception: return symbol

def cleanup_old_cache(days=7):
    """지정된 기간(일)보다 오래된 캐시 파일을 삭제합니다."""
    logging.info(f"만료된 ({days}일 이상) 캐시 파일 정리 시작.")
    cutoff_time = datetime.now() - timedelta(days=days)
    cache_files = CACHE_DIR.glob('*.json')
    deleted_count = 0
    for file_path in cache_files:
        try:
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mod_time < cutoff_time:
                file_path.unlink()  
                deleted_count += 1
                logging.debug(f"캐시 파일 삭제: {file_path.name}")
        except Exception as e:
            logging.error(f"캐시 파일 {file_path.name} 정리 중 오류 발생: {e}")
    logging.info(f"총 {deleted_count}개의 오래된 캐시 파일을 정리했습니다.")


# ==============================
# 4. 고급 특징 공학 및 클러스터링 로직 (개선)
# ==============================

def calculate_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """고급 패턴 인식을 위해 기술적 지표를 특징(Feature)으로 추가합니다. (Adj_Close 기반)"""
    
    # 필수 기술적 지표 계산 (Adj_Close 기반)
    df['RSI'] = ta.momentum.RSIIndicator(close=df[PRICE_COL], window=14, fillna=False).rsi()
    df['MACD'] = ta.trend.MACD(close=df[PRICE_COL], fillna=False).macd()
    df['MACD_Signal'] = ta.trend.MACD(close=df[PRICE_COL], fillna=False).macd_signal()
    df['MACD_Hist'] = ta.trend.MACD(close=df[PRICE_COL], fillna=False).macd_diff() 

    bollinger = ta.volatility.BollingerBands(close=df[PRICE_COL], window=20, window_dev=2, fillna=False)
    df['BB_Width'] = bollinger.bollinger_wband()
    
    # Long Term Down Trend 분석 및 MA 조건 체크를 위한 필수 MA 계산
    df['SMA_20'] = ta.trend.SMAIndicator(close=df[PRICE_COL], window=20, fillna=False).sma_indicator()
    df['SMA_50'] = ta.trend.SMAIndicator(close=df[PRICE_COL], window=50, fillna=False).sma_indicator()
    df['SMA_200'] = ta.trend.SMAIndicator(close=df[PRICE_COL], window=200, fillna=False).sma_indicator()

    # 🛠️ 개선 2. 특징 공학 강화: ATR (Volatility)
    df['ATR'] = ta.volatility.AverageTrueRange(
        high=df[HIGH_COL], low=df[LOW_COL], close=df[PRICE_COL], window=14, fillna=False
    ).average_true_range()

    # 🛠️ 개선 2. 특징 공학 강화: CMF (Chaikin Money Flow)
    df['CMF'] = ta.volume.ChaikinMoneyFlowIndicator(
        high=df[HIGH_COL], low=df[LOW_COL], close=df[PRICE_COL], volume=df['Volume'], window=20, fillna=False
    ).chaikin_money_flow()
    
    # 🛠️ 개선 2. 특징 공학 강화: Log Return 통계량
    df['Log_Return'] = np.log(df[PRICE_COL] / df[PRICE_COL].shift(1))
    
    # Log Return의 50일 이동 표준편차 (변동성) 및 왜도 (쏠림 정도)
    df['Log_Return_Std'] = df['Log_Return'].rolling(window=50).std()
    df['Log_Return_Skew'] = df['Log_Return'].rolling(window=50).skew()
    
    df['TREND_CROSS'] = (df['SMA_50'] > df['SMA_200']).astype(int)

    # 🛠️ 개선 3. Market Regime용 강화된 특징 목록
    feature_subset = [
        'RSI', 'MACD', 'BB_Width', 'ATR', 'CMF', 
        'Log_Return_Std', 'Log_Return_Skew', 'TREND_CROSS', 'SMA_200', 'Log_Return'
    ]
    
    df_with_features = df.copy().dropna(subset=feature_subset)
    return df_with_features

def add_market_regime_clustering(df_full: pd.DataFrame, n_clusters=4) -> pd.DataFrame:
    """K-Means 클러스터링을 통해 시장 국면(Market Regime)을 정의하고 할당합니다. (강화된 특징 사용)"""
    # 🛠️ 개선 3. 강화된 특징을 사용하여 Market Regime 정의
    feature_cols = [
        'RSI', 'MACD', 'BB_Width', 'ATR', 'CMF', 
        'Log_Return_Std', 'Log_Return_Skew', 'TREND_CROSS', 'Log_Return'
    ]
    min_data_length = 200

    if len(df_full) < min_data_length or not all(col in df_full.columns for col in feature_cols):
        df_full['MarketRegime'] = -1 
        return df_full

    data = df_full[feature_cols].copy()

    if data.drop_duplicates().shape[0] < n_clusters:
        df_full['MarketRegime'] = -1 
        return df_full
    
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data) 

    try:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, init='k-means++')
        df_full['MarketRegime'] = kmeans.fit_predict(scaled_data) 
    except ValueError as e:
        logging.warning(f"KMeans 클러스터링 실패: {e}")
        df_full['MarketRegime'] = -1

    return df_full


# ==============================
# 5. 기술적 분석 패턴 로직 (수정 - Adj_Close 사용)
# (모든 패턴 감지 함수는 PRICE_COL ('Adj_Close')을 사용하도록 수정되었습니다.)
# ==============================

def find_peaks_and_troughs(df, prominence=0.01, width=3):
    """주요 봉우리와 골짜기 인덱스 찾기 (최근 250일 기준, Adj_Close 사용)"""
    recent_df = df.iloc[-250:].copy()
    if recent_df.empty: return np.array([]), np.array([])
    
    std_dev = recent_df[PRICE_COL].std()
    peaks, _ = find_peaks(recent_df[PRICE_COL], prominence=std_dev * prominence, width=width)
    troughs, _ = find_peaks(-recent_df[PRICE_COL], prominence=std_dev * prominence, width=width)
    
    start_idx = len(df) - len(recent_df)
    return peaks + start_idx, troughs + start_idx


def find_double_bottom(df, troughs, tolerance=0.05, min_duration=30):
    """이중 바닥 패턴 감지 (Adj_Close 사용)"""
    recent_troughs = [t for t in troughs if t >= len(df) - 250]
    if len(recent_troughs) < 2: return 'None', None
    
    idx2, idx1 = recent_troughs[-1], recent_troughs[-2] 
    price1, price2 = df[PRICE_COL].iloc[idx1], df[PRICE_COL].iloc[idx2]
    
    if idx2 - idx1 < min_duration: return 'None', None
    
    is_price_matching = abs(price1 - price2) / min(price1, price2) < tolerance
    if not is_price_matching: return 'None', None
    
    interim_high = df[PRICE_COL].iloc[idx1:idx2].max() 
    current_price = df[PRICE_COL].iloc[-1]

    if current_price > interim_high: 
        return 'Breakout', interim_high
    
    min_bottom_price = min(price1, price2)
    if interim_high > min_bottom_price:
        retrace_ratio = (current_price - min_bottom_price) / (interim_high - min_bottom_price)
    else:
        retrace_ratio = 0
        
    if retrace_ratio > 0.5 and current_price < interim_high: 
        return 'Potential', interim_high
        
    return 'None', None


def find_triple_bottom(df, troughs, tolerance=0.05, min_duration_total=75):
    """삼중 바닥 패턴 감지 (Adj_Close 사용)"""
    recent_troughs = [t for t in troughs if t >= len(df) - 250]
    if len(recent_troughs) < 3: return 'None', None
    
    idx3, idx2, idx1 = recent_troughs[-1], recent_troughs[-2], recent_troughs[-3]
    price1, price2, price3 = df[PRICE_COL].iloc[idx1], df[PRICE_COL].iloc[idx2], df[PRICE_COL].iloc[idx3]
    
    if idx3 - idx1 < min_duration_total: return 'None', None
    
    min_price = min(price1, price2, price3)
    max_price = max(price1, price2, price3)
    is_price_matching = (max_price - min_price) / min_price < tolerance
    if not is_price_matching: return 'None', None
    
    high1 = df[PRICE_COL].iloc[idx1:idx2].max()
    high2 = df[PRICE_COL].iloc[idx2:idx3].max()
    neckline = max(high1, high2) 
    current_price = df[PRICE_COL].iloc[-1]

    if current_price > neckline: 
        return 'Breakout', neckline
    
    if neckline > min_price:
        retrace_ratio = (current_price - min_price) / (neckline - min_price) 
    else:
        retrace_ratio = 0
        
    if retrace_ratio > 0.5 and current_price < neckline:
        return 'Potential', neckline
        
    return 'None', None


def find_cup_and_handle(df, peaks, troughs, handle_drop_ratio=0.3):
    """컵 앤 핸들 패턴 감지 (Adj_Close 사용)"""
    recent_peaks = [p for p in peaks if p >= len(df) - 250]
    if len(recent_peaks) < 2: return 'None', None
    
    peak_right_idx = recent_peaks[-1]
    peak_right_price = df[PRICE_COL].iloc[peak_right_idx]
    
    neckline = peak_right_price
    
    handle_start_idx = peak_right_idx 
    handle_max_drop = peak_right_price * (1 - handle_drop_ratio) 
    current_price = df[PRICE_COL].iloc[-1]
    
    recent_max = df[PRICE_COL].iloc[handle_start_idx:-1].max() if len(df) > handle_start_idx + 1 else peak_right_price
    is_handle_forming = (recent_max <= peak_right_price) 
    is_handle_forming &= (current_price > handle_max_drop)

    if is_handle_forming:
        if current_price > neckline:
            return 'Breakout', neckline
        else:
            return 'Potential', neckline
        
    return 'None', None


def find_long_term_down_trend(df: pd.DataFrame):
    """장기 하락 추세 (Adj_Close < MA20 < MA50 < MA200 조건 확인)"""
    if len(df) < 200:
        return False, "NotEnoughData"

    current_close = df[PRICE_COL].iloc[-1]
    
    try:
        ma20 = df['SMA_20'].iloc[-1]
        ma50 = df['SMA_50'].iloc[-1]
        ma200 = df['SMA_200'].iloc[-1]
    except KeyError:
        return False, "MA_Missing"

    is_inverse_order = (ma20 < ma50) and (ma50 < ma200)
    is_price_below_ma20 = current_close < ma20
    
    if is_inverse_order and is_price_below_ma20:
        return True, "StrongDownTrend"
        
    is_all_below_ma = (current_close < ma20) and (current_close < ma50) and (current_close < ma200)
    if is_all_below_ma:
           return False, "PotentialDownTrend" 

    return False, "None" 


# ==============================
# 6. 기술적 조건 및 패턴 분석 (수정 - Adj_Close 사용)
# ==============================

def check_ma_conditions(df, periods, analyze_patterns):
    """이동 평균선 조건 및 패턴 분석을 수행하고 결과를 딕셔너리로 반환합니다."""
    results = {}
    
    ma_cols = {20: 'SMA_20', 50: 'SMA_50', 200: 'SMA_200'}

    if len(df) < 200: analyze_patterns = False

    # 1. 주가와 MA 비교 (Adj_Close 사용)
    for p in periods:
        col_name = ma_cols.get(p)
        if col_name and col_name in df.columns and not df.empty:
            results[f"above_ma{p}"] = df[PRICE_COL].iloc[-1] > df[col_name].iloc[-1]
        else:
            results[f"above_ma{p}"] = False

    # 2. 골든/데드 크로스 감지 (기존 유지)
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

    # 3. 기술적 패턴 분석 (Adj_Close 사용)
    is_down_trend, down_trend_status = find_long_term_down_trend(df) 
    results['pattern_long_term_down_trend'] = is_down_trend
    results['down_trend_status'] = down_trend_status

    if analyze_patterns:
        peaks, troughs = find_peaks_and_troughs(df)
        db_status, db_price = find_double_bottom(df, troughs)
        tb_status, tb_price = find_triple_bottom(df, troughs)
        ch_status, ch_price = find_cup_and_handle(df, peaks, troughs)
    else:
        db_status, db_price = 'Disabled', None
        tb_status, tb_price = 'Disabled', None
        ch_status, ch_price = 'Disabled', None

    results['pattern_double_bottom_status'] = db_status
    results['db_neckline_price'] = db_price
    results['pattern_triple_bottom_status'] = tb_status
    results['tb_neckline_price'] = tb_price
    results['pattern_cup_and_handle_status'] = ch_status
    results['ch_neckline_price'] = ch_price

    # 4. 시장 국면 (Market Regime)
    if 'MarketRegime' in df.columns and not df.empty:
        results['market_regime'] = int(df['MarketRegime'].iloc[-1])
    else:
        results['market_regime'] = -1

    return results


# ==============================
# 7. 분석 실행 및 캐싱 로직 (수정 - 데이터 로드 방식)
# ==============================

def analyze_symbol(item, periods, analyze_patterns, pattern_type_filter, top_n, symbol_filter=None): 
    """단일 종목을 분석하고 필터링 조건에 맞는지 확인하여 결과를 반환합니다."""
    code = item.get("Code") or item.get("code")
    name = item.get("Name") or item.get("name")
    path = DATA_DIR / f"{code}.parquet"

    if not path.exists():
        logging.debug(f"[{code}] 데이터 파일 없음.")
        return None

    try:
        # 🛠️ 개선 1. Parquet 파일 로드 시 인덱스 유지 및 Adj_Close 컬럼 확인
        df_raw = pd.read_parquet(path)
        
        if df_raw.index.name != 'Date' and 'Date' in df_raw.columns:
            df_raw = df_raw.set_index('Date')
            
        if 'Adj_Close' not in df_raw.columns and 'Close' in df_raw.columns:
             df_raw.rename(columns={'Close': 'Adj_Close'}, inplace=True)

        if df_raw.empty or len(df_raw) < 250:
            logging.debug(f"[{code}] 데이터 부족 ({len(df_raw)}일).")
            return None

        df_full = calculate_advanced_features(df_raw)
        df_full = add_market_regime_clustering(df_full)
        
        df_analyze = df_full.iloc[-250:].copy() 

        if len(df_analyze) < 200: 
            logging.debug(f"[{code}] 최종 분석 데이터 부족 ({len(df_analyze)}일).")
            return None

        analysis_results = check_ma_conditions(df_analyze, periods, analyze_patterns)

        # 필터링 로직 적용
        is_match = True
        if pattern_type_filter:
            if pattern_type_filter == 'goldencross':
                is_match = analysis_results.get("goldencross_50_200_detected", False)
            elif pattern_type_filter == 'deadcross': 
                is_match = analysis_results.get("deadcross_50_200_detected", False)
            elif pattern_type_filter == 'long_term_down_trend':
                is_match = analysis_results.get("pattern_long_term_down_trend", False)
                
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
            elif pattern_type_filter == 'ma':
                is_match = all(analysis_results.get(f"above_ma{p}", False) for p in periods if p in [20, 50, 200])
            elif pattern_type_filter == 'all_below_ma':
                # 주가가 20, 50, 200일 MA 아래에 있는지 확인 (Adj_Close 사용)
                ma_columns = {20: 'SMA_20', 50: 'SMA_50', 200: 'SMA_200'}
                is_match = all(
                    (df_analyze[PRICE_COL].iloc[-1] < df_analyze.get(ma_columns[p], 999999999).iloc[-1])
                    for p in [20, 50, 200] if ma_columns[p] in df_analyze.columns
                )
            else:
                is_match = False

        if pattern_type_filter and not is_match: 
            logging.debug(f"[{code}] 필터 '{pattern_type_filter}' 불일치.")
            return None

        if analysis_results:
            analysis_clean = {k: v for k, v in analysis_results.items() if v is not None}
            # Market Regime을 정렬 기준으로 사용
            sort_score = analysis_clean.get('market_regime', -1) 
            
            return {
                "ticker": code,
                "name": name,
                "technical_conditions": analysis_clean, 
                "sort_score": sort_score 
            }
        return None
    except Exception as e:
        logging.error(f"[ERROR] {code} {name} 분석 실패: {e}\n{traceback.format_exc()}") 
        return None

# run_analysis 함수 (기존 유지)
def run_analysis(workers, ma_periods_str, analyze_patterns_flag, pattern_type_filter, top_n, symbol_filter=None): 
    # (기존 run_analysis 함수 내용)

    cleanup_old_cache() 
    
    start_time = time.time()
    periods = [int(p.strip()) for p in ma_periods_str.split(',') if p.strip().isdigit()]

    today_str = datetime.now().strftime("%Y%m%d")
    analyze_patterns = analyze_patterns_flag 
    
    cache_filter_key = f"{pattern_type_filter or 'ma_only'}_{'pattern' if analyze_patterns else 'no_pattern'}"
    cache_key = f"{today_str}_{cache_filter_key.replace(':', '_')}_{top_n}.json" 
    cache_path = CACHE_DIR / cache_key
    
    if not symbol_filter and cache_path.exists(): 
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            logging.info(f"캐시 로드 성공: {cache_key}")
            sys.stdout.write(json.dumps(cached_data, ensure_ascii=False, indent=None, separators=(',', ':'), cls=CustomJsonEncoder) + "\n")
            sys.stdout.flush()
            sys.exit(0)
        except Exception as e:
            logging.error(f"캐시 파일 로드/파싱 실패: {e}. 재분석을 시도합니다.")

    required_periods = [20, 50, 200]
    for p in required_periods:
        if p not in periods: periods.append(p)

    items = load_listing()
    
    if symbol_filter:
        items = [item for item in items if (item.get("Code") or item.get("code")) == symbol_filter]
        if not items:
            logging.error(f"지정된 종목 코드({symbol_filter})를 리스팅에서 찾을 수 없습니다.")
            safe_print_json({"error": "SYMBOL_NOT_FOUND", "ticker": symbol_filter}, status_code=1)
            return
    
    initial_item_count = len(items) 
    total_symbols_loaded = len(load_listing()) 
    
    if initial_item_count == 0:
        safe_print_json({"error": "LISTING_DATA_EMPTY" if not symbol_filter else "SYMBOL_NOT_FOUND"}, status_code=1)
        return

    results = []
    logging.info(f"분석 시작 (캐시 미스): 총 {initial_item_count} 종목, 필터: {pattern_type_filter or 'None'}")
    processed_count = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_item = {
            executor.submit(analyze_symbol, item, periods, analyze_patterns, pattern_type_filter, top_n): item
            for item in items
        }

        for future in as_completed(future_to_item):
            processed_count += 1
            
            progress_percent = round((processed_count / initial_item_count) * 100, 2) 
            sys.stdout.write(json.dumps({
                "mode": "progress",
                "total_symbols": initial_item_count,
                "processed_symbols": processed_count,
                "progress_percent": progress_percent
            }, ensure_ascii=False, cls=CustomJsonEncoder, indent=None, separators=(',', ':')) + "\n")
            sys.stdout.flush()

            try:
                r = future.result()
                if r: results.append(r)
            except Exception as e:
                code = future_to_item[future].get("Code") or future_to_item[future].get("code")
                name = future_to_item[future].get("Name") or future_to_item[future].get("name")
                logging.error(f"[ERROR] {code} {name} 처리 중 예외 발생: {e}") 

    results.sort(key=lambda x: x.get('sort_score', -1), reverse=True)
    final_results = results[:top_n] if top_n > 0 else results
    
    for r in final_results:
        r.pop('sort_score', None)

    end_time = time.time()

    data_check = {
        "listing_file_exists": LISTING_FILE.exists(),
        "total_symbols_loaded": total_symbols_loaded,
        "symbols_processed": initial_item_count,
        "symbols_filtered": len(results),
        "symbols_returned": len(final_results),
        "time_taken_sec": round(end_time - start_time, 2),
    }

    final_output = {
        "results": final_results,
        "mode": "analyze_result",
        "filter": pattern_type_filter or 'ma_only',
        "data_check": data_check
    }
    
    if not symbol_filter:
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(final_output, f, ensure_ascii=False, cls=CustomJsonEncoder, indent=None, separators=(',', ':'))
            logging.info(f"분석 결과 캐시 저장 완료: {cache_key}")
        except Exception as e:
            logging.error(f"캐시 파일 저장 실패: {e}")

    logging.info(f"분석 완료 및 결과 반환. 총 소요 시간: {data_check['time_taken_sec']}초")
    safe_print_json(final_output, status_code=0)


# ==============================
# 8. 차트 생성 로직 (수정 - Adj_Close 사용)
# ==============================

def generate_chart(symbol, ma_periods_str, chart_period):
    """
    단일 종목의 시계열 데이터를 Chart.js JSON 포맷으로 변환하여 반환합니다.
    (Adj_Close 기준으로 모든 가격 데이터 포맷팅)
    """
    code = symbol
    name = get_stock_name(code)
    periods = [int(p.strip()) for p in ma_periods_str.split(',') if p.strip().isdigit()] 
    path = DATA_DIR / f"{code}.parquet"

    if not path.exists():
        safe_print_json({"error": f"데이터 파일을 찾을 수 없음: {path}"}, status_code=1)
        return

    try:
        # 🛠️ 개선 1. Parquet 파일 로드 시 인덱스 유지 및 Adj_Close 컬럼 확인
        df = pd.read_parquet(path)
        
        if df.index.name != 'Date' and 'Date' in df.columns:
            df = df.set_index('Date')

        if 'Adj_Close' not in df.columns and 'Close' in df.columns:
             df.rename(columns={'Close': 'Adj_Close'}, inplace=True)
             
        if df.empty:
            safe_print_json({"error": "데이터프레임이 비어 있습니다."}, status_code=1)
            return

        df_full = calculate_advanced_features(df)
        df_for_chart = df_full.iloc[-chart_period:].copy()

        if df_for_chart.empty:
            safe_print_json({"error": "특징 계산 후 데이터가 부족하여 차트 생성 불가."}, status_code=1)
            return

        # 1. 캔들스틱 데이터 포맷팅 (OHLCV) - 종가는 Adj_Close 사용
        ohlcv_data = []
        for index, row in df_for_chart.iterrows():
            ohlcv_data.append({
                "x": index.strftime('%Y년 %m월 %d일'), 
                "o": row['Open'], "h": row['High'], "l": row['Low'], "c": row[PRICE_COL], "v": row['Volume']
            })

        # 2. 이동평균선(MA) 데이터 포맷팅 (Adj_Close 기반)
        ma_data = {}
        for p in periods:
            ma_col_name = f'SMA_{p}'
            # MA가 calculate_advanced_features에서 계산되지 않은 경우에만 다시 계산 (Adj_Close 기반)
            if ma_col_name not in df_for_chart.columns:
                 df_for_chart[ma_col_name] = ta.trend.SMAIndicator(close=df_for_chart[PRICE_COL], window=p, fillna=False).sma_indicator() 

            ma_values = []
            for index, row in df_for_chart.iterrows():
                if not pd.isna(row[ma_col_name]):
                    ma_values.append({"x": index.strftime('%Y년 %m월 %d일'), "y": row[ma_col_name]})
            ma_data[f"MA{p}"] = ma_values
            
        # 3. MACD 데이터 포맷팅 (Adj_Close 기반)
        macd_data = {"MACD": [], "Signal": [], "Histogram": []}
        for index, row in df_for_chart.iterrows():
            date_str = index.strftime('%Y년 %m월 %d일') 
            if not pd.isna(row['MACD']):
                macd_data["MACD"].append({"x": date_str, "y": row['MACD']})
            if not pd.isna(row['MACD_Signal']):
                macd_data["Signal"].append({"x": date_str, "y": row['MACD_Signal']})
            if not pd.isna(row['MACD_Hist']):
                macd_data["Histogram"].append({"x": date_str, "y": row['MACD_Hist']})

        # 4. 크로스 지점 감지 및 패턴 넥라인 정보 추가
        cross_data = []
        pattern_data = [] 

        ma50_col = 'SMA_50'
        ma200_col = 'SMA_200'
        
        # 4-1. MA 크로스 지점 감지
        if ma50_col in df_for_chart.columns and ma200_col in df_for_chart.columns:
            ma_cross = df_for_chart[ma50_col] > df_for_chart[ma200_col]
            cross_points = ma_cross[ma_cross != ma_cross.shift(1)]

            for date, is_above in cross_points.items():
                if date == df_for_chart.index[0]: continue
                prev_above = ma_cross.shift(1).loc[date]
                cross_type = ""
                
                if not prev_above and is_above: cross_type = "GoldenCross"
                elif prev_above and not is_above: cross_type = "DeadCross"
                
                if cross_type:
                    cross_data.append({"x": date.strftime('%Y년 %m월 %d일'), "y": df_for_chart.loc[date, PRICE_COL], "type": cross_type})

        # 4-2. 패턴 넥라인 정보 감지 및 추가 (전체 데이터프레임 사용)
        is_down_trend, down_trend_status = find_long_term_down_trend(df_full) 
        if is_down_trend:
            today_date = df_full.index[-1].strftime('%Y년 %m월 %d일') 
            pattern_data.append({"x": today_date, "y": df_full[PRICE_COL].iloc[-1], "type": "LongTermDownTrend", "status": down_trend_status})

        peaks, troughs = find_peaks_and_troughs(df_full)
        patterns = {
            'DoubleBottom': find_double_bottom(df_full, troughs),
            'TripleBottom': find_triple_bottom(df_full, troughs),
            'CupAndHandle': find_cup_and_handle(df_full, peaks, troughs)
        }
        
        for p_type, (status, price) in patterns.items():
            if status in ['Breakout', 'Potential'] and price is not None:
                pattern_data.append({
                    "x": df_full.index[-1].strftime('%Y년 %m월 %d일'), 
                    "y": price, 
                    "type": p_type, 
                    "status": status,
                    "is_neckline": True
                })
        
        # 5. 최종 결과 JSON 구성
        final_output = {
            "ticker": code,
            "name": name,
            "mode": "chart_data",
            "ohlcv_data": ohlcv_data,
            "ma_data": ma_data,
            "macd_data": macd_data,
            "cross_points": cross_data,
            "pattern_points": pattern_data 
        }

        safe_print_json(final_output, status_code=0)

    except Exception as e:
        logging.error(f"[ERROR] Chart.js 데이터 생성 실패 ({code} {name}): {e}\n{traceback.format_exc()}")
        safe_print_json({"error": f"Chart.js 데이터 생성 실패: {e}"}, status_code=1)


# main 함수 (기존 유지)
def main():
    """스크립트의 메인 실행 함수입니다. 인수를 파싱하고 모드별 함수를 호출합니다."""
    parser = argparse.ArgumentParser(description="주식 데이터 분석 및 차트 데이터 생성 스크립트")
    
    parser.add_argument("--mode", type=str, required=True, choices=['analyze', 'chart'], help="실행 모드 선택: 'analyze' 또는 'chart'")
    parser.add_argument("--workers", type=int, default=os.cpu_count() * 2, help="분석 모드에서 사용할 최대 스레드 수")
    parser.add_argument("--ma_periods", type=str, default="20,50,200", help="이동 평균선 기간 지정 (쉼표로 구분, 예: 5,20,50)")
    parser.add_argument("--chart_period", type=int, default=250, help="차트 모드에서 표시할 거래일 수 (기본값: 250일)")
    
    parser.add_argument("--symbol", type=str, help="분석 또는 차트 모드에서 사용할 단일 종목 코드 (Ticker)")
    
    parser.add_argument("--analyze_patterns", action="store_true", help="패턴 감지 활성화 (활성화 시 모든 상승/하락 패턴이 감지됨)")
    
    parser.add_argument("--pattern_type", type=str,
                          choices=['ma', 'all_below_ma', 'long_term_down_trend', 'goldencross', 'deadcross', 
                                   'double_bottom', 'triple_bottom', 'cup_and_handle', 
                                   'regime:0', 'regime:1', 'regime:2', 'regime:3'],
                          help="분석 모드에서 필터링할 패턴 종류")
    parser.add_argument("--debug", action="store_true", help="디버그 모드 활성화 (로깅 레벨 DEBUG)")
    parser.add_argument("--top_n", type=int, default=10, help="분석 결과 중 상위 N개 종목만 반환 (0 이하: 전체 반환)")
    

    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_env(log_level=log_level) 
    
    if args.mode == 'analyze':
        analyze_patterns_flag = args.analyze_patterns
        
        run_analysis(
            workers=args.workers,
            ma_periods_str=args.ma_periods,
            analyze_patterns_flag=analyze_patterns_flag, 
            pattern_type_filter=args.pattern_type,
            top_n=args.top_n, 
            symbol_filter=args.symbol 
        )
    elif args.mode == 'chart':
        if not args.symbol:
            safe_print_json({"error": "MISSING_ARGUMENT", "reason": "차트 모드는 --symbol 인자를 필수로 요구합니다."}, status_code=1)
            return
            
        generate_chart(
            symbol=args.symbol,
            ma_periods_str=args.ma_periods,
            chart_period=args.chart_period
        )


if __name__ == "__main__":
    main()