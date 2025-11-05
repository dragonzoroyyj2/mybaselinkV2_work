package com.yourproject.stock.scheduler;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;

@Component
public class StockUpdateScheduler {

    private final String PYTHON_PATH = "python3"; // 서버 환경에 맞게 변경 (예: /usr/bin/python3)
    private final String UPDATER_SCRIPT_PATH = "/path/to/your/project/stock_updater.py"; // 👈 실제 경로로 변경
    
    // 환경 변수 설정 (중요: DART_API_KEY는 서버 환경 변수 또는 애플리케이션 설정 파일에서 불러와야 함)
    // 여기서는 System.getenv()로 가정합니다.
    private final String DART_API_KEY = System.getenv("DART_API_KEY"); 

    /**
     * 매일 새벽 3시에 stock_updater.py 스크립트를 실행합니다.
     * (cron 표현식: 초 분 시 일 월 요일)
     */
    @Scheduled(cron = "0 0 3 * * *") // 매일 3시 0분 0초에 실행
    public void runStockUpdater() {
        System.out.println("=================================================");
        System.out.println("✅ [배치 시작] 주식 데이터 업데이트 배치 (stock_updater.py) 시작: " + System.currentTimeMillis());
        System.out.println("=================================================");

        ProcessBuilder pb = new ProcessBuilder(
            PYTHON_PATH,
            UPDATER_SCRIPT_PATH
        );
        
        // 1. DART API Key 환경 변수 설정 (파이썬 스크립트가 사용하도록)
        if (DART_API_KEY == null || DART_API_KEY.isEmpty()) {
             System.err.println("🔴 [오류] DART_API_KEY 환경 변수가 설정되지 않았습니다. 배치를 중단합니다.");
             return;
        }
        pb.environment().put("DART_API_KEY", DART_API_KEY);

        Process process = null;
        try {
            // 2. 프로세스 실행
            process = pb.start();

            // 3. 파이썬의 표준 출력(stdout)을 읽어 로그에 기록
            readAndLogStream(process, "STDOUT");
            
            // 4. 파이썬의 표준 에러(stderr)를 읽어 로그에 기록 (오류 추적용)
            readAndLogStream(process, "STDERR");

            // 5. 프로세스 종료 대기 (데이터 수집은 시간이 오래 걸리므로 충분한 시간 부여)
            // 3시간(180분) 동안 기다림. 10년치 데이터 수집 시 필요할 수 있음.
            boolean finished = process.waitFor(180, java.util.concurrent.TimeUnit.MINUTES); 

            if (!finished) {
                process.destroyForcibly();
                System.err.println("🔴 [오류] stock_updater.py 실행 시간 초과 (180분). 강제 종료됨.");
            }
            
            // 6. 종료 코드 확인
            if (process.exitValue() != 0) {
                 System.err.println("❌ [실패] stock_updater.py 실행 실패. 종료 코드: " + process.exitValue());
            } else {
                 System.out.println("🟢 [성공] stock_updater.py 데이터 업데이트 배치 완료.");
            }

        } catch (IOException | InterruptedException e) {
            System.err.println("🛑 [치명적 오류] 배치 실행 중 예외 발생: " + e.getMessage());
            e.printStackTrace();
        } finally {
            if (process != null) {
                process.destroy();
            }
        }
    }
    
    // Process의 출력 스트림을 읽어 콘솔에 로그로 기록하는 헬퍼 함수
    private void readAndLogStream(Process process, String type) {
        new Thread(() -> {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                    type.equals("STDOUT") ? process.getInputStream() : process.getErrorStream(), 
                    "UTF-8"))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    // Python 스크립트의 로그를 Java 로그로 전달
                    System.out.println("  [Python " + type + "] " + line); 
                }
            } catch (IOException e) {
                System.err.println("  [I/O 오류] Python " + type + " 스트림 읽기 실패: " + e.getMessage());
            }
        }).start();
    }
}