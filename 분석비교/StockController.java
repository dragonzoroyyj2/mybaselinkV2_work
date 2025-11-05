package com.yourproject.stock.controller;

import com.yourproject.stock.service.PythonRunnerService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/stock")
public class StockController {

    private final PythonRunnerService pythonRunnerService;

    @Autowired
    public StockController(PythonRunnerService pythonRunnerService) {
        this.pythonRunnerService = pythonRunnerService;
    }

    /**
     * 사용자 요청: 종목과 패턴을 받아 분석을 요청합니다.
     * @param code 종목 코드 (예: "005930")
     * @param pattern 패턴 타입 (예: "DoubleBottom")
     * @return 파이썬이 반환한 JSON 형식의 분석 결과
     */
    @GetMapping("/analyze/{code}")
    public String getAnalysisResult(@PathVariable String code, 
                                    @RequestParam("pattern") String pattern) {
        try {
            // 파이썬 서비스를 호출하고 결과를 받습니다.
            String resultJson = pythonRunnerService.analyzeStock(code, pattern);
            
            // 파이썬의 JSON 결과를 클라이언트에게 그대로 전달
            return resultJson;
        } catch (Exception e) {
            // 분석 중 발생한 모든 오류 처리
            return "{\"error\": \"분석 요청 처리 중 오류: " + e.getMessage() + "\"}";
        }
    }
}