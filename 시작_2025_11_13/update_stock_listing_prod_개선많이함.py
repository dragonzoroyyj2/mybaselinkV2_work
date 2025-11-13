# -*- coding: utf-8 -*-
"""
📘 update_stock_listing_prod_final_V2.0.py (최종 개선판 - 데이터 품질 및 효율 강화)
----------------------------------------------------------
✅ 개선 1. Parquet 효율: 'Date' 인덱스 설정 및 Snappy 압축 적용 (분석 속도 향상).
✅ 개선 2. 데이터 품질: 'Close'를 'Adj_Close'로 명시적으로 사용 (수정 주가 가정).
✅ 개선 3. 운영 효율: 워커 수 CPU 코어 * 8로 최대화 (I/O 병렬 처리 최적화).
✅ 로직/구조/진행률/로깅 기존 완전 유지.
----------------------------------------------------------
"""

import os
import sys
import json
import time
import logging
import argparse
import socket
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

try:
    import FinanceDataReader as fdr
    import requests
except ModuleNotFoundError as e:
    print(json.dumps({"error": f"필수 모듈 누락: {e.name} 설치 필요"}, ensure_ascii=False), flush=True)
    sys.exit(1)

# ==============================
# 상수 정의
# ==============================
PER_STOCK_TIMEOUT = 15
MAX_RETRIES = 3
KRX_LIST_CACHE_DAYS = 1

# 🛠️ 개선 3. 워커 수 CPU 코어 * 8로 최대화 (I/O Bound 작업 최적)
DEFAULT_WORKERS = os.cpu_count() * 8 if os.cpu_count() else 14
DEFAULT_HISTORY_YEARS = 3

# ==============================
# 경로 설정
# ==============================
BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "log"
DATA_DIR = BASE_DIR / "data" / "stock_data"
LISTING_FILE = BASE_DIR / "data" / "stock_list" / "stock_listing.json"
LOG_FILE = LOG_DIR / "robust_stock_updater.log"

# ==============================
# 로깅 초기화
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
# 네트워크 확인
# ==============================
def check_network_connection(host="www.google.com", port=80, timeout=5):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        logging.info("네트워크 연결 성공.")
        return True
    except Exception as e:
        msg = f"네트워크 연결 실패: {e}"
        logging.critical(msg)
        print(json.dumps({"error": msg}, ensure_ascii=False), flush=True)
        sys.exit(1)

# ==============================
# KRX 목록 로드
# ==============================
def load_krx_listing():
    logging.info("[PROGRESS] 5.0 KRX 종목 목록 로드 중...")
    total = 0
    
    if LISTING_FILE.exists():
        file_mtime = datetime.fromtimestamp(LISTING_FILE.stat().st_mtime).date()
        today = datetime.now().date()
        cache_age = (today - file_mtime).days
        
        if cache_age < KRX_LIST_CACHE_DAYS:
            try:
                krx = pd.read_json(LISTING_FILE, orient="records")
                if not krx.empty:
                    total = len(krx)
                    logging.info(f"[LOG] KRX 종목 목록 캐시 로드 ({total}개, 캐시 기간 {cache_age}일)")
                    logging.info(f"[KRX_TOTAL] {total}")
                    logging.info(f"[KRX_SAVED] {total}")
                    logging.info("[PROGRESS] 10.0 KRX 목록 로드 완료 (캐시 유효)")
                    return krx
            except Exception:
                logging.warning("[LOG] KRX 캐시 로드 실패, 재다운로드 시도")
        else:
             logging.warning(f"[LOG] KRX 캐시 만료 (기준 {KRX_LIST_CACHE_DAYS}일, 현재 {cache_age}일), 재다운로드 시도")

    try:
        krx = fdr.StockListing("KRX")
        if krx is None or krx.empty:
            raise ValueError("KRX 데이터 다운로드 실패")
        krx.rename(columns={'Symbol': 'Code'}, inplace=True)
        krx["Date"] = datetime.now().strftime("%Y-%m-%d")
        krx.to_json(LISTING_FILE, orient="records", force_ascii=False, indent=2)
        total = len(krx)
        logging.info(f"[LOG] KRX 종목 리스트 저장 완료 ({total}개)")
        logging.info(f"[KRX_TOTAL] {total}")
        logging.info(f"[KRX_SAVED] {total}")
        logging.info("[PROGRESS] 10.0 KRX 목록 로드 완료 (재다운로드)")
        return krx
    except Exception as e:
        logging.error(f"[ERROR] KRX 목록 다운로드 실패: {e}")
        print(json.dumps({"status": "failed", "error": str(e)}), flush=True)
        sys.exit(1)

# ==============================
# 단일 종목 데이터 수집 (수정)
# ==============================
def fetch_and_save_data(item: Dict[str, Any], history_years: int, force_download: bool):
    code = item.get("Code")
    name = item.get("Name")
    path = DATA_DIR / f"{code}.parquet"
    end_date = datetime.now().date()
    existing_df = pd.DataFrame()
    last_date = None

    if path.exists() and not force_download:
        try:
            # 🛠️ 개선 1. Parquet 파일 로드 시 인덱스 처리 (기존/신규 포맷 호환)
            existing_df = pd.read_parquet(path)
            if not existing_df.empty:
                # 인덱스가 Date인 경우 (신규 포맷)
                if existing_df.index.name == 'Date':
                    existing_df = existing_df.reset_index()
                existing_df['Date'] = pd.to_datetime(existing_df['Date'])
                last_date = existing_df['Date'].max().date()
                if last_date >= end_date:
                    return f"{code} {name} → 이미 최신", "cached"
        except Exception as e:
            logging.warning(f"[{code}] {name} Parquet 파일 읽기 오류: {e}. 전체 재다운로드를 시도합니다.")
            last_date = None

    if last_date and not force_download:
        start_date_str = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
        update_type = "증분"
    else:
        start_date_str = (datetime.now() - timedelta(days=history_years * 365)).strftime('%Y-%m-%d')
        update_type = "전체"

    for attempt in range(MAX_RETRIES):
        try:
            df = fdr.DataReader(code, start=start_date_str, end=end_date.strftime('%Y-%m-%d'))
            
            if df.empty:
                return f"{code} {name} → 데이터 없음", "no_data"
            
            # 🛠️ 개선 2. 컬럼 이름 명시: 분석 스크립트와의 통일성을 위해 Close를 Adj_Close로 변경
            if 'Close' in df.columns:
                df.rename(columns={'Close': 'Adj_Close'}, inplace=True)
            
            # Date 컬럼을 인덱스로 설정
            if df.index.name != 'Date':
                df.index.name = 'Date'
            
            # 증분 업데이트 처리
            if update_type == "증분" and not existing_df.empty:
                if existing_df.index.name != 'Date':
                    existing_df = existing_df.set_index('Date')
                
                combined_df = pd.concat([existing_df, df]).drop_duplicates(keep='last').sort_index()
                
                # 🛠️ 개선 1. Snappy 압축 적용 및 인덱스 저장
                combined_df.to_parquet(path, index=True, compression='snappy')
                return f"{code} {name} → 저장 완료 (증분, {len(df)}행)", "success"
            
            # 전체 업데이트 처리
            else:
                # 🛠️ 개선 1. Snappy 압축 적용 및 인덱스 저장
                df.to_parquet(path, index=True, compression='snappy')
                return f"{code} {name} → 저장 완료 ({update_type}, {len(df)}행)", "success"

        except requests.exceptions.RequestException as e:
            logging.error(f"[{code}] {name} 네트워크 오류/타임아웃 발생 (시도 {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1 + attempt)
            else:
                return f"{code} {name} → 최종 실패: {type(e).__name__}", "failed"
        
        except Exception as e:
            logging.error(f"[{code}] {name} 데이터 수집 중 상세 예외 발생: {type(e).__name__} - {e}", exc_info=False)
            return f"{code} {name} → 실패: {type(e).__name__}", "failed"

    return f"{code} {name} → 최종 실패 (모든 재시도 소진)", "failed"

# ==============================
# 병렬 다운로드 처리
# ==============================
def download_and_save_stocks(krx, workers: int, history_years: int, force_download: bool):
    items = krx.to_dict('records')
    total_count = len(items)
    logging.info(f"[PROGRESS] 25.0 KRX 목록 {total_count}건 로드됨 (워커: {workers})")
    if force_download:
        logging.info("[LOG] --force 전체 다운로드 강제모드")
    logging.info("[PROGRESS] 30.0 개별 종목 다운로드 시작")

    update_step = max(1, total_count // 50)
    completed_count = success_count = failed_count = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(fetch_and_save_data, item, history_years, force_download): item for item in items}

        for future in as_completed(futures):
            item = futures[future]
            code = item.get("Code")
            try:
                result_msg, result_type = future.result(timeout=PER_STOCK_TIMEOUT + 5)
                
                if result_type == "failed":
                    failed_count += 1
                elif result_type != "cached":
                    success_count += 1
                    
                completed_count += 1
                logging.info(f"[LOG] {result_msg} ({completed_count}/{total_count})")
                
                if (completed_count % update_step == 0) or (completed_count == total_count):
                    pct = 30.0 + (completed_count / total_count) * 70.0
                    logging.info(f"[PROGRESS] {pct:.1f} 종목 저장 {completed_count}/{total_count}")
                    
            except TimeoutError:
                failed_count += 1
                completed_count += 1
                logging.error(f"[TIMEOUT] {code} → 응답 없음 (작업 실행 {PER_STOCK_TIMEOUT + 5}초 초과)")
            except Exception as e:
                failed_count += 1
                completed_count += 1
                logging.critical(f"[CRITICAL_ERROR] {code} 치명적 예외 발생: {e}")

    progress = 30.0 + (completed_count / total_count) * 70.0 if total_count > 0 else 0.0
    return completed_count, success_count, failed_count, total_count, progress

# ==============================
# 메인 실행
# ==============================
def main():
    parser = argparse.ArgumentParser(description="주식 시세 데이터 업데이트 (v2.6)")
    # 🛠️ 개선 3. DEFAULT_WORKERS를 계산된 최적값으로 설정
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--history_years", type=int, default=DEFAULT_HISTORY_YEARS)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    start_time = time.time()
    stats = {"status": "failed", "success": 0, "failed": 0, "total": 0, "progress": 0.0}
    check_network_connection()

    try:
        krx_listing = load_krx_listing()
        completed, success, failed, total, progress = download_and_save_stocks(krx_listing, args.workers, args.history_years, args.force)
        stats.update({"success": success, "failed": failed, "total": total, "progress": round(progress, 1)})

        if completed == total:
            stats["status"] = "completed"
        else:
            stats["status"] = "failed" 

    except Exception as e:
        logging.critical(f"[ERROR] 실행 중 오류: {e}", exc_info=True)
        stats.update({"status": "failed", "error": str(e)})

    finally:
        elapsed = time.time() - start_time
        logging.info(f"[LOG] 총 소요: {elapsed:.2f}초")

        if stats["status"] == "completed":
            stats["progress"] = 100.0
        logging.info(f"[PROGRESS] {stats['progress']:.1f} 최종 진행률 반영")

        print(json.dumps(stats, ensure_ascii=False), flush=True)
        logging.shutdown()

        sys.exit(0 if stats["status"] == "completed" else 1)


if __name__ == "__main__":
    main()