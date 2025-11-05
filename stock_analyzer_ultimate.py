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
    📈 이중 바닥 패턴 감지 (튜닝: tolerance 5%, 최소 기간 30일)
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
    🧱 삼중 바닥 패턴 감지 (튜닝: tolerance 5%, 최소 기간 75일)
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
    ☕ 컵 앤 핸들 패턴 감지 (튜닝: 컵 깊이 최소 15%, 핸들 조정 폭 최대 30%)
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