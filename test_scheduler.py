# -*- coding: utf-8 -*-
import datetime
import os

# 스크립트가 실행된 폴더에 로그 파일을 생성합니다.
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scheduler_test_log.txt")

with open(LOG_PATH, "a", encoding="utf-8") as f:
    f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scheduler test execution successful.\n")

print("Test script finished.")


"""
매우 안정적인 아키텍처를 갖추게 되었습니다.

실시간 감시 (데몬): dart_monitor.py → Windows 작업 스케줄러 (시스템 시작 시 24/7 실행)

배치 업데이트: stock_updater.py → Windows 작업 스케줄러 (매일 새벽 실행, Java와 리소스 완전 분리)

실시간 분석: stock_analyzer_ultimate.py → Java Spring Boot API (사용자 요청 시 즉시 실행/종료)
-*- coding: utf-8 -*-

# C:\Test\test_scheduler.py (수정 후)
# -*- coding: utf-8 -*-  # ?? 이 한 줄을 맨 위에 추가합니다.
import datetime
import os
# ... (이하 코드 동일)







??? Windows 작업 스케줄러 여는 3가지 확실한 방법
방법 1: 검색 창 사용 (가장 빠름)
시작 버튼 옆의 검색 창 (또는 Windows 로고 키를 누른 후)을 클릭합니다.

다음 단어 중 하나를 입력합니다.

작업 스케줄러 (한글)

Task Scheduler (영문)

taskschd.msc (실행 파일 이름)

검색 결과 상단에 나타나는 작업 스케줄러 앱을 클릭하여 실행합니다.

방법 2: 실행 창 (Run Command) 사용
Windows 키 + R 키를 동시에 누릅니다. (실행 창이 열립니다.)

열린 창에 다음 명령어를 입력하고 엔터를 누릅니다.

taskschd.msc
작업 스케줄러 창이 즉시 열립니다.

방법 3: 제어판을 통한 접근 (클래식 방법)
시작 메뉴를 열고 **제어판**을 검색하여 실행합니다.

제어판에서 **시스템 및 보안**을 클릭합니다.

시스템 및 보안 창에서 **관리 도구**를 클릭합니다.

관리 도구 목록에서 **작업 스케줄러**를 찾아 더블 클릭하여 실행합니다.


 where python 


py 실행

"C:\Users\User\AppData\Local\Programs\Python\Python310\python.exe" C:\Test\test_scheduler.py







pdater.py)의 다음 실행 시각매일 새벽 3시 등이 설정되어 있는지 확인?? 팁: 빠르게 실행하거나 수정하기즉시 실행: 등록된 작업을 오른쪽 마우스 버튼으로 클릭하고 **실행**을 선택하면 즉시 스크립트를 실행해 볼 수 있습니다. (데몬(dart_monitor.py)이 비정상 종료되었을 때 유용합니다.)속성 수정: 등록된 작업을 더블 클릭하거나 오른쪽 마우스 버튼 → **속성**을 선택하여 Python 경로, 시작 위치, 트리거 시간을 수정할 수 있습니다.이제 등록된 작업을 쉽게 찾아서 모니터링 상태를 확인하고 관리하실 수 있을 것입니다!
"""