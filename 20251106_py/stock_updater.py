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