package com.mybaselinkV2.app.controller;

import com.mybaselinkV2.app.service.StockBatchService;
import org.springframework.http.MediaType;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

/**
 * SSE (Server-Sent Events) Controller
 * - 작업 상태를 클라이언트에게 실시간으로 전송하는 역할
 */
@RestController
public class StockBatchSseController {

    private final StockBatchService batchService;

    public StockBatchSseController(StockBatchService batchService) {
        this.batchService = batchService;
    }

    /**
     * 클라이언트에게 실시간 상태 스트림을 제공합니다.
     * @param auth Spring Security Authentication 객체로 사용자 ID를 얻습니다.
     * @return SseEmitter
     */
    @GetMapping(value = "/api/stock/batch/sse", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream(Authentication auth) {
        // 인증된 사용자 ID를 사용하거나, 인증되지 않은 경우 "anonymous"를 사용합니다.
        String user = auth != null ? auth.getName() : "anonymous";

        // 서비스에 Emitter 생성을 위임하고 관리합니다.
        return batchService.createEmitter(user);
    }
}