# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import logging
import argparse
import socket
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Union
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

# ==============================
# 0. 상수 정의
# ==============================
DEFAULT_HISTORY_YEARS = 3 # 기본 데이터 수집 기간 (3년)
MAX_RETRIES = 3            # 데이터 수집 최대 재시도 횟수
KRX_LIST_CACHE_DAYS = 1    # KRX 목록 캐시 유지 기간 (일)

# ==============================
# 필수 라이브러리 확인 및 임포트
# ==============================
try:
    import FinanceDataReader as fdr
    # requests 라이브러리 임포트 추가
    import requests 
    
    # DART API 키는 환경 변수에서만 가져오도록 변경 (보안 강화)
    DART_API_KEY = os.getenv("DART_API_KEY") 
    DART_AVAILABLE = bool(DART_API_KEY)
    
    if DART_AVAILABLE:
        try:
            from dart_fss import Dart
        except ImportError:
            DART_AVAILABLE = False
            logging.warning("DART_API_KEY가 설정되었으나 dart-fss 모듈이 없어 DART 기능 비활성화. (pip install dart-fss)")
    else:
        logging.warning("DART_API_KEY 환경 변수가 설정되지 않아 DART 기능 비활성화.")
            
except ModuleNotFoundError as e:
    sys.stdout.write(json.dumps({"error": f"필수 모듈 누락: {e.name} 설치 필요 (pip install {e.name})"}, ensure_ascii=False) + "\n")
    sys.exit(1)

# ==============================
# 1. 경로 및 상수 설정
# ==============================
BASE_DIR = Path('C:/LocBootProject/ex_py')
LOG_DIR = BASE_DIR / "log"
DATA_DIR = BASE_DIR / "data" / "stock_data"
LISTING_FILE = BASE_DIR / "data" / "stock_list" / "stock_listing.json"
LOG_FILE = LOG_DIR / "stock_updater.log"

# ==============================
# 2. 환경 초기화 및 로깅 설정
# ==============================
def setup_env() -> None:
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
# 3. 네트워크 상태 체크
# ==============================
def check_network_connection(host: str = "www.google.com", port: int = 80, timeout: int = 5) -> bool:
    """
    지정된 호스트와 포트로 연결을 시도하여 네트워크 상태를 확인하고 실패 시 즉시 종료합니다.
    """
    logging.info("네트워크 연결 상태 확인 중...")
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        logging.info("네트워크 연결 성공.")
        return True
    except Exception as e:
        error_msg = f"네트워크 연결 실패 (호스트: {host}, 오류: {e}). 작업을 즉시 종료합니다."
        logging.critical(error_msg)
        sys.stdout.write(json.dumps({"error": error_msg}) + "\n")
        sys.exit(1)

# ==============================
# 4. KRX 종목 목록 로드 (캐시 적용)
# ==============================
def load_krx_listing() -> Union[pd.DataFrame, None]:
    """
    KRX 상장 종목 목록을 다운로드하거나 캐시에서 로드합니다.
    """
    logging.info("[PROGRESS] 0.0 KRX 종목 목록 로드 중...")
    
    # 1. 캐시 유효성 검사
    if LISTING_FILE.exists():
        file_mod_time = datetime.fromtimestamp(LISTING_FILE.stat().st_mtime)
        if (datetime.now() - file_mod_time).days < KRX_LIST_CACHE_DAYS:
            try:
                with open(LISTING_FILE, "r", encoding="utf-8") as f:
                    items = json.load(f)
                listing_df = pd.DataFrame(items)
                logging.info(f"KRX 종목 목록을 캐시 파일에서 로드했습니다. ({len(listing_df)}개 종목)")
                return listing_df
            except Exception as e:
                logging.warning(f"KRX 종목 목록 캐시 파일 로드 실패: {e}. 재다운로드 시도.")

    # 2. 재다운로드
    try:
        logging.info("KRX 종목 목록 재다운로드 중...")
        listing_df = fdr.StockListing('KRX')
        listing_df.rename(columns={'Symbol': 'Code', 'Name': 'Name'}, inplace=True)
        
        # 3. 새 목록을 캐시 파일로 저장
        items = listing_df.to_dict('records')
        with open(LISTING_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
            
        return listing_df
    except Exception as e:
        logging.error(f"KRX 종목 목록 다운로드 실패: {e}")
        return None


# ==============================
# 5. DART 종목 코드 업데이트
# ==============================
def update_dart_corp_codes(listing_df: pd.DataFrame) -> pd.DataFrame:
    """
    DART API를 사용하여 종목별 기업 고유 번호를 매핑합니다.
    """
    logging.info("[PROGRESS] 5.0 DART 기업 고유 번호 매핑 시작...")
    if not DART_AVAILABLE or DART_API_KEY is None:
        logging.warning("DART API 키가 없어 기업 고유 번호 매핑을 건너뜁니다.")
        listing_df['DartCorpCode'] = None 
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
# 6. 시세 데이터 업데이트 (재시도 및 증분 업데이트 적용)
# ==============================
def fetch_and_save_data(item: Dict[str, Any], history_years: int) -> int:
    """단일 종목의 시세 데이터를 가져와 Parquet 파일로 저장합니다."""
    code = item.get("Code")
    name = item.get("Name")
    path = DATA_DIR / f"{code}.parquet"
    
    end_date = datetime.now()
    existing_df = pd.DataFrame() # 기존 DataFrame 초기화
    
    # 1. 증분 업데이트: 기존 데이터의 마지막 날짜 확인
    last_date = None
    if path.exists():
        try:
            existing_df = pd.read_parquet(path)
            if not existing_df.empty and 'Date' in existing_df.columns:
                last_date = pd.to_datetime(existing_df['Date']).max().date()
                if last_date >= end_date.date():
                    return 1 # 캐시 히트: 업데이트 완료
            
        except Exception as e:
            logging.warning(f"기존 파일 로드 실패 ({code} {name}): {e}. 전체 재다운로드 시도.")
            last_date = None
    
    # 2. 시작 날짜 설정
    if last_date:
        start_date = last_date + timedelta(days=1)
        if (end_date.date() - start_date).days < 1: return 1
    else:
        start_date = end_date - timedelta(days=history_years * 365)
    
    # 3. 데이터 수집 및 재시도 로직
    for attempt in range(MAX_RETRIES):
        try:
            # FinanceDataReader 호출
            df = fdr.DataReader(
                code, 
                start=start_date.strftime('%Y-%m-%d'), 
                end=end_date.strftime('%Y-%m-%d')     
            )
            
            if df.empty:
                logging.warning(f"데이터 없음 ({code} {name}): {start_date}부터 데이터가 비어 있음.")
                return 1
                
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index()
            df['Date'] = pd.to_datetime(df['Date'])

            # 4. 데이터 병합 및 저장
            if last_date and not existing_df.empty:
                combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=['Date'], keep='last')
                combined_df = combined_df.sort_values(by='Date')
                combined_df.to_parquet(path, index=False)
                logging.info(f"성공 (증분): {code} {name} (총 {len(combined_df)}일)")
            else:
                df.to_parquet(path, index=False)
                logging.info(f"성공 (전체): {code} {name} (총 {len(df)}일)")
                
            return 1 # 최종 성공
            
        # SSL, Timeout, Connection 오류 발생 시 재시도 (일반적인 네트워크 불안정성 대응)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.SSLError) as e:
            logging.warning(f"네트워크/SSL 오류 발생 ({code} {name}) [시도 {attempt + 1}/{MAX_RETRIES}]: {e}")
            if attempt < MAX_RETRIES - 1:
                # 지수 백오프 (1초, 2초 대기)
                time.sleep(2 ** attempt) 
            else:
                return 0 # 최종 실패
        except Exception as e:
            # 그 외 일반 오류 (FDR 내부 오류, 데이터 처리 오류 등)
            logging.warning(f"데이터 수집 중 알 수 없는 오류 발생 ({code} {name}) [시도 {attempt + 1}/{MAX_RETRIES}]: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt) 
            else:
                return 0
    return 0 

# ==============================
# 7. 실행 함수
# ==============================
def run_update(workers: int, history_years: int) -> None:
    # 1. 네트워크 체크
    check_network_connection() 

    start_time = time.time()
    
    # 2. KRX 종목 목록 로드 (캐시 적용)
    listing_df = load_krx_listing()
    if listing_df is None or listing_df.empty:
        logging.critical("KRX 종목 목록을 가져올 수 없어 작업을 중단합니다.")
        return

    # 3. DART 코드 매핑
    listing_df = update_dart_corp_codes(listing_df)
    items = listing_df.to_dict('records')
    
    total_count = len(items)
    completed_count = 0
    
    logging.info(f"[PROGRESS] 15.0 시세 데이터 업데이트 시작: 총 {total_count} 종목, 최대 워커 {workers}개 사용. 기간: {history_years}년") 

    # 4. 병렬 데이터 수집
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_item = {
            executor.submit(fetch_and_save_data, item, history_years): item 
            for item in items
        }
        
        for future in as_completed(future_to_item):
            if future.result() == 1:
                completed_count += 1
            
            progress_pct = 15.0 + (completed_count / total_count) * 80.0
            logging.info(f"[PROGRESS] {progress_pct:.1f} 종목 저장 {completed_count}/{total_count}")

    end_time = time.time()
    logging.info(f"[PROGRESS] 100.0 전체 완료. 총 소요 시간: {end_time - start_time:.2f}초")


# ==============================
# 8. 메인 실행 로직
# ==============================
def main():
    parser = argparse.ArgumentParser(description="주식 시세 데이터 업데이트 스크립트 (외부망 최적화 버전)")
    parser.add_argument(
        "--workers", 
        type=int, 
        default=16, 
        help="데이터 수집에 사용할 최대 스레드 수 (병렬 처리 개수). 기본값은 16입니다."
    )
    parser.add_argument(
        "--history_years", 
        type=int, 
        default=DEFAULT_HISTORY_YEARS,
        help=f"다운로드할 데이터의 기간 (년 단위). 기본값은 {DEFAULT_HISTORY_YEARS}년입니다."
    )
    parser.add_argument(
        "--dart_api_key",
        type=str,
        default=None,
        help="DART 기업 공시 정보를 위한 API Key입니다. 환경 변수 DART_API_KEY가 없을 경우 사용됩니다."
    )
    # --proxy_server 및 --ignore_ssl 옵션 제거

    args = parser.parse_args()

    # 명령줄 인자로 API 키가 넘어오면 환경 변수보다 우선하여 적용
    if args.dart_api_key:
        os.environ["DART_API_KEY"] = args.dart_api_key
        global DART_API_KEY, DART_AVAILABLE
        DART_API_KEY = args.dart_api_key
        DART_AVAILABLE = True

    try:
        # run_update 함수에서 use_proxy 인자 제거
        run_update(args.workers, args.history_years)
    except Exception as e:
        error_msg = f"스크립트 실행 중 치명적인 오류 발생: {e}"
        logging.critical(f"{error_msg}")
        sys.stdout.write(json.dumps({"error": error_msg}) + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()