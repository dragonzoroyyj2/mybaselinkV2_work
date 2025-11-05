package com.yourproject.stock.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;

import java.io.*;
import java.util.concurrent.TimeUnit;

@Service
public class PythonRunnerService {

    private final String PYTHON_PATH = "python3"; // 또는 "python", 또는 가상 환경 경로 (예: /home/user/venv/bin/python)
    private final String ANALYZER_SCRIPT_PATH = "/path/to/your/project/stock_analyzer_ultimate.py"; // 실제 경로로 변경 필요

    /**
     * stock_analyzer_ultimate.py 스크립트를 실행하고 JSON 결과를 반환합니다.
     * @param code 분석할 종목 코드
     * @param pattern 감지할 패턴 (예: DoubleBottom, CupAndHandle)
     * @return 파이썬이 출력한 JSON 문자열
     */
    public String analyzeStock(String code, String pattern) throws IOException, InterruptedException {
        
        // 1. ProcessBuilder 설정
        ProcessBuilder pb = new ProcessBuilder(
                PYTHON_PATH,
                ANALYZER_SCRIPT_PATH,
                code,      // 첫 번째 인자: 종목 코드
                pattern    // 두 번째 인자: 패턴 타입
        );

        // 환경 변수 설정 (필요하다면, 예를 들어 DART_API_KEY 설정)
        // pb.environment().put("DART_API_KEY", System.getenv("DART_API_KEY"));
        
        Process process = null;
        String jsonResult = null;

        try {
            // 2. 프로세스 실행
            process = pb.start();
            
            // 3. 파이썬의 표준 출력(stdout)에서 JSON 결과 읽기
            // BufferedReader를 사용하여 파이썬이 출력하는 JSON 문자열을 모두 읽어들입니다.
            jsonResult = readProcessOutput(process.getInputStream());

            // 4. 파이썬의 표준 에러(stderr)에서 오류 메시지 읽기 (오류 추적용)
            String errorOutput = readProcessOutput(process.getErrorStream());
            if (!errorOutput.isEmpty()) {
                // 파이썬에서 에러가 발생했으나 JSON은 반환했을 수 있습니다. 로그에 기록합니다.
                System.err.println("Python stderr Output: " + errorOutput); 
            }

            // 5. 프로세스 종료 대기 (최대 60초)
            boolean finished = process.waitFor(60, TimeUnit.SECONDS);

            if (!finished) {
                // 시간 초과 시 프로세스 강제 종료
                process.destroyForcibly();
                throw new IOException("Python 스크립트 실행 시간 초과.");
            }
            
            // 6. 종료 코드 확인 (정상 종료: 0)
            if (process.exitValue() != 0) {
                 // 파이썬 스크립트가 0이 아닌 코드로 종료됨 (실행 실패)
                 throw new IOException("Python 스크립트 실행 실패. 종료 코드: " + process.exitValue());
            }

        } catch (Exception e) {
            e.printStackTrace();
            // 오류 발생 시 오류 JSON 형식으로 반환
            return "{\"error\": \"분석 서버 오류 발생: " + e.getMessage() + "\"}";
        } finally {
            if (process != null) {
                // 자원 해제
                process.destroy();
            }
        }
        
        // 파이썬이 출력한 최종 JSON 문자열 반환
        return jsonResult;
    }

    // Process의 출력 스트림을 읽어 문자열로 반환하는 헬퍼 함수
    private String readProcessOutput(InputStream inputStream) throws IOException {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream, "UTF-8"))) {
            StringBuilder builder = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line).append("\n"); // 한 줄씩 읽어와 누적
            }
            // 마지막 개행 문자 제거 후 반환
            return builder.toString().trim();
        }
    }
}