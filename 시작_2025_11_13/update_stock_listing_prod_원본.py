# -*- coding: utf-8 -*-
"""
📘 update_stock_listing_prod_final.py (v1.0 실전 안정판 - 최종 개선판)
----------------------------------------------------------
✅ StockBatchGProdService(v3.3) 완전 동기화
✅ BASE_DIR = Path(__file__).resolve().parents[2]
✅ 로직/구조/진행률/로깅 기존 완전 유지
----------------------------------------------------------
🌟 개선점 반영 완료: KRX 종목 목록 캐시 기간 (KRX_LIST_CACHE_DAYS) 명시적 검사 로직 적용
🔥 개선점 반영 완료: fetch_and_save_data 내 상세 오류 로깅 적용
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
    # 한국어 메시지 출력
    print(json.dumps({"error": f"필수 모듈 누락: {e.name} 설치 필요"}, ensure_ascii=False), flush=True)
    sys.exit(1)

# ==============================
# 상수 정의
# ==============================
PER_STOCK_TIMEOUT = 15 # ⏱️ 증가: 10s -> 15s. API의 느린 응답에 대비
MAX_RETRIES = 3
KRX_LIST_CACHE_DAYS = 1 # 🌟 KRX 목록 캐시 유효 기간: 1일

DEFAULT_WORKERS = 14	 # 🌟 초안정화: 8 -> 4로 극단적 감소. 안정성 최대화
DEFAULT_HISTORY_YEARS = 3

# ==============================
# 경로 설정
# ==============================
# BASE_DIR: 스크립트가 실행되는 현재 작업 디렉토리
# Path(__file__).resolve().parents[2] 위치는
#로컬 →  상위 2단계로 올라가면 /MyBaseLinkV2/python
#운영 →  C:/SET_MyBaseLinkV2/server/python_scripts/python/stock/py
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
        
        # 🌟 개선 로직: 캐시 파일이 존재하고 유효 기간(KRX_LIST_CACHE_DAYS) 내에 있는지 확인
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
# 단일 종목 데이터 수집
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
            existing_df = pd.read_parquet(path)
            if not existing_df.empty and 'Date' in existing_df.columns:
                existing_df['Date'] = pd.to_datetime(existing_df['Date'])
                last_date = existing_df['Date'].max().date()
                if last_date >= end_date:
                    return f"{code} {name} → 이미 최신", "cached"
        except Exception as e:
            # 파일 읽기 오류는 상세 로그를 남기지 않고, 재다운로드 유도 (last_date = None)
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
            # 타임아웃 처리를 위해 requests 라이브러리 레벨의 예외를 명시적으로 처리해야 함.
            df = fdr.DataReader(code, start=start_date_str, end=end_date.strftime('%Y-%m-%d'))
            if df.empty:
                return f"{code} {name} → 데이터 없음", "no_data"
            df = df.reset_index()
            
            if update_type == "증분" and not existing_df.empty:
                existing_df['Date'] = pd.to_datetime(existing_df['Date'])
                combined_df = pd.concat([existing_df, df], ignore_index=True).drop_duplicates(subset=['Date'], keep='last')
                combined_df.sort_values(by='Date').to_parquet(path, index=False)
                return f"{code} {name} → 저장 완료 (증분, {len(df)}행)", "success"
            else:
                df.to_parquet(path, index=False)
                return f"{code} {name} → 저장 완료 ({update_type}, {len(df)}행)", "success"
        
        except requests.exceptions.RequestException as e:
            # 네트워크/요청 오류 상세 로깅 (타임아웃 포함)
            logging.error(f"[{code}] {name} 네트워크 오류/타임아웃 발생 (시도 {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1 + attempt)
            else:
                return f"{code} {name} → 최종 실패: {type(e).__name__}", "failed"
        
        except Exception as e:
            # 🔥 제시된 개선사항 반영: 상세 오류 로깅 (기타 예외) 🔥
            # exc_info=False로 설정하여 traceback은 남기지 않고 메시지만 상세히 기록
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
                # 개별 스레드 실행 결과에 대한 타임아웃 처리
                result_msg, result_type = future.result(timeout=PER_STOCK_TIMEOUT + 5) # 스레드 실행 자체에 대한 추가 타임아웃
                
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
                # TimeoutError는 ThreadPoolExecutor에서 발생하므로 여기서 로그 기록
                logging.error(f"[TIMEOUT] {code} → 응답 없음 (작업 실행 {PER_STOCK_TIMEOUT + 5}초 초과)")
            except Exception as e:
                failed_count += 1
                completed_count += 1
                # 스레드 실행 중 발생한 기타 치명적 오류 로깅
                logging.critical(f"[CRITICAL_ERROR] {code} 치명적 예외 발생: {e}")

    progress = 30.0 + (completed_count / total_count) * 70.0 if total_count > 0 else 0.0
    return completed_count, success_count, failed_count, total_count, progress

# ==============================
# 메인 실행
# ==============================
def main():
    parser = argparse.ArgumentParser(description="주식 시세 데이터 업데이트 (v2.6)")
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

        # ✅ 일부 실패는 정상 종료 (completed == total을 기준으로 최종 status 결정)
        if completed == total:
            stats["status"] = "completed"
        else:
            # 하나라도 미완료시 failed로 처리 (Timeout 포함)
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