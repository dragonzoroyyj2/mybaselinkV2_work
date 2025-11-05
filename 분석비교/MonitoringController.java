package com.yourproject.stock.controller;

import org.springframework.web.bind.annotation.GetMapping;sp
import org.springframework.web.bind.annotation.RestController;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
/*
 * 
 * [
  {
    "timestamp": "2025-11-05 17:15:22",
    "corp_name": "삼성엔지니어링",
    "stock_code": "028050",
    "report_name": "[정정]단일판매ㆍ공급계약체결",
    "report_summary": "계약금액: 2,500,000,000,000 원 | 계약상대: 사우디 아람코 | 매출비율: 120.5%",
    "dart_url": "http://dart.fss.or.kr/dsaf001/zts/detailedReport.do?rceptNo=20251105000543",
    "rcept_no": "20251105000543",
    "telegram_sent": true
  },
  {
    "timestamp": "2025-11-05 16:30:05",
    "corp_name": "현대차",
    "stock_code": "005380",
    "report_name": "주요사항보고서(유상증자결정)",
    "report_summary": "주요 내용 추출 실패 (공시 원문 참조)",
    "dart_url": "http://dart.fss.or.kr/dsaf001/zts/detailedReport.do?rceptNo=20251105000401",
    "rcept_no": "20251105000401",
    "telegram_sent": true
  }
]
 * 
 */
@RestController
public class MonitoringController {
    
    // dart_monitor.py와 동일한 경로 설정
    private static final String RESULTS_FILE_PATH = "./monitoring_results.json";

    /**
     * 웹 화면에서 실시간 DART 이벤트 목록을 조회합니다.
     * @return monitoring_results.json 파일 내용
     */
    @GetMapping("/api/dart/events")
    public String getDartEvents() {
        try {
            Path filePath = Paths.get(RESULTS_FILE_FILE_PATH);
            if (Files.exists(filePath)) {
                // JSON 파일 내용을 문자열로 읽어 반환
                return Files.readString(filePath); 
            } else {
                return "[]"; // 파일이 없으면 빈 배열 반환
            }
        } catch (IOException e) {
            // 파일 I/O 오류 발생 시 에러 메시지 반환
            return "{\"error\": \"DART 이벤트 데이터 로드 중 오류 발생\"}";
        }
    }
}