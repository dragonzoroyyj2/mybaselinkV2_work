# dart_monitor.py - 최종 안정화 버전
import os
import sys
import json
import time
import requests
import re
import io
import logging # 로깅 모듈 추가
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from pathlib import Path
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ==============================
# 1. 경로 및 상수 설정 & 로깅 설정
# ==============================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "stock_data"
RESULTS_FILE = BASE_DIR / "monitoring_results.json"
RCEPTS_FILE = BASE_DIR / "notified_rcepts.json"
LOG_FILE = BASE_DIR / "dart_monitor.log" # 전용 로그 파일

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

# ==============================
# 2. 환경 변수 설정 (토큰/키)
# ==============================
DART_API_KEY = os.getenv("DART_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# DART 공시 검색 키워드 및 제외 키워드
TARGET_KEYWORDS = ["공급계약", "계약체결", "수주계약"]
EXCLUDE_KEYWORDS = ["해지", "취소", "정정"] 

# 한글 폰트 설정 (서버 환경에 맞춰 변경 필요: 'Malgun Gothic', 'NanumGothic' 등)
try:
    plt.rcParams['font.family'] = 'Malgun Gothic' 
    plt.rcParams['axes.unicode_minus'] = False 
except Exception:
    logging.warning("한글 폰트 설정 실패. 시스템에 폰트가 설치되어 있는지 확인하세요.")

# ==============================
# 3. 데이터 및 상태 관리 함수 (안정성 강화)
# ==============================

def load_notified_rcepts():
    """이전에 알림을 보낸 공시번호 목록을 로드합니다."""
    if RCEPTS_FILE.exists():
        try:
            with open(RCEPTS_FILE, "r", encoding="utf-8") as f:
                rcepts = set(json.load(f))
                return rcepts
        except json.JSONDecodeError:
            logging.warning("RCEPTS_FILE 로드 중 JSON 오류 발생. 파일 초기화.")
            return set()
    return set()

def save_notified_rcepts(rcept_set):
    """현재 알림을 보낸 공시번호 목록을 저장합니다."""
    try:
        with open(RCEPTS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(rcept_set), f, ensure_ascii=False, indent=4)
        logging.info("RCEPTS_FILE 저장 완료.")
    except Exception as e:
        logging.error(f"RCEPTS_FILE 저장 실패: {e}")

def save_monitoring_result(report_data):
    """모니터링 결과를 JSON 파일에 추가합니다."""
    
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            logging.warning("RESULTS_FILE 로드 중 JSON 오류 발생. 파일 초기화.")
            data = []
    else:
        data = []
        
    data.insert(0, report_data)
    
    try:
        with open(RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"화면 조회용 결과 파일 저장 완료: {RESULTS_FILE}")
    except Exception as e:
        logging.error(f"결과 파일 저장 실패: {e}")

# (텔레그램 전송 및 차트 생성 함수는 변경 없음)
# (DART 보고서 파싱 함수는 변경 없음)

# ==============================
# 6. 메인 모니터링 루프 (로깅 및 안정성 강화)
# ==============================

def dart_monitoring_loop(interval_minutes=5):
    """5분마다 DART 공시를 반복적으로 확인하고 알림을 보냅니다."""
    
    notified_rcepts = load_notified_rcepts() 
    logging.info(f"DART 모니터링 시작. 이전 알림 이력 {len(notified_rcepts)}개 로드 완료.")
    
    last_save_time = time.time()
    
    while True:
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=interval_minutes + 1)
    
            # DART API 호출
            url = "https://opendart.fss.or.kr/api/list.json"
            params = {
                "crtfc_key": DART_API_KEY,
                "bgn_de": start_time.strftime("%Y%m%d"),
                "end_de": end_time.strftime("%Y%m%d"),
                "page_count": 100, 
                "page_no": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != '000':
                logging.warning(f"DART API 오류 응답: {data.get('message')}. {interval_minutes}분 대기.")
                time.sleep(interval_minutes * 60)
                continue
                
            total_reports = len(data.get('list', []))
            if total_reports > 0:
                logging.info(f"최근 {interval_minutes}분 동안 {total_reports}개의 공시 확인.")
                
            for report in data.get('list', []):
                rcept_no = report['rcept_no']
                report_name = report['report_nm']
                corp_name = report['corp_name']
                stock_code = report.get('stock_code') 
                
                # 1. 필터링 및 중복 검사
                if rcept_no in notified_rcepts:
                    continue
                
                is_target_keyword = any(k in report_name for k in TARGET_KEYWORDS)
                is_excluded_keyword = any(k in report_name for k in EXCLUDE_KEYWORDS)
                
                if is_target_keyword and not is_excluded_keyword and stock_code:
                    logging.info(f"--- [NEW EVENT] {corp_name} - {report_name} 포착 ---")
                    
                    # 2. 공시 내용 요약 및 DART URL 생성
                    dart_report_summary = parse_dart_report_for_summary(rcept_no)
                    dart_url = f"http://dart.fss.or.kr/dsaf001/zts/detailedReport.do?rceptNo={rcept_no}"
                    
                    # 3. 일봉 차트 이미지 생성
                    chart_image_bytes = generate_chart_image_bytes(stock_code)
                    
                    # 4. 텔레그램 메시지 구성
                    caption_text = (
                        f"🔔 <b>실시간 DART 공시 포착</b> 🔔\n"
                        f"회사명: <b>{corp_name} ({stock_code})</b>\n"
                        f"요약: {dart_report_summary}\n" 
                        f"공시명: {report_name}\n"
                        f"<a href='{dart_url}'>[공시 원문 바로가기]</a>"
                    )
                    
                    # 5. 텔레그램 전송
                    if chart_image_bytes:
                        send_telegram_photo(TELEGRAM_CHAT_ID, chart_image_bytes, caption_text)
                    else: 
                        send_telegram_message(TELEGRAM_CHAT_ID, caption_text)
                        
                    # 6. 화면 조회용 데이터 저장
                    result_data = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "corp_name": corp_name,
                        "stock_code": stock_code,
                        "report_name": report_name,
                        "report_summary": dart_report_summary,
                        "dart_url": dart_url,
                        "rcept_no": rcept_no,
                        "telegram_sent": True
                    }
                    save_monitoring_result(result_data)
                    
                    # 7. 중복 방지 세트에 추가
                    notified_rcepts.add(rcept_no) 
            
            # RCEPT_NO 셋은 1시간(3600초)마다 저장하여 파일 I/O 부하 감소
            if time.time() - last_save_time > 3600: 
                save_notified_rcepts(notified_rcepts)
                last_save_time = time.time()
                
        except requests.RequestException as e:
            logging.error(f"DART/Telegram 통신 오류: {e}")
        except Exception as e:
            logging.critical(f"모니터링 루프 중 치명적 오류 발생: {e}", exc_info=True)
            
        logging.info(f"다음 확인까지 {interval_minutes}분 대기...")
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    if not all([DART_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        logging.error("필수 환경 변수(DART_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)를 설정해야 합니다.")
        sys.exit(1)

    if not DATA_DIR.exists():
        logging.error(f"데이터 경로({DATA_DIR})가 존재하지 않습니다. stock_updater.py를 먼저 실행하세요.")
        sys.exit(1)
        
    dart_monitoring_loop(interval_minutes=5)