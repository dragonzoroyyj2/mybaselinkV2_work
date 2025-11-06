package com.mybaselinkV2.app.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.stream.Collectors;

/**
 * 📊 TaskStatusService (v2.1 실전 통합판)
 * ------------------------------------------------------------
 * ✅ 작업 상태 + 진행률 + 로그 + SSE 스냅샷 관리
 * ✅ thread-safe (ConcurrentHashMap 기반)
 * ✅ Python JSON 결과 파싱 유틸 추가 (parseJsonMap / parseJsonList)
 * ✅ StockBatch / StockLastCloseDownward 등 공용
 * ------------------------------------------------------------
 */
@Service
public class TaskStatusService {

    // ==============================================================\
    // 📄 내부 구조체 정의
    // ==============================================================

    /** 🔹 로그 한 줄 정보 */
    public static final class LogLine {
        private final int seq;
        private final String line;
        private final Instant ts;

        public LogLine(int seq, String line) {
            this.seq = seq;
            this.line = line;
            this.ts = Instant.now();
        }

        public int getSeq() { return seq; }
        public String getLine() { return line; }
        public Instant getTs() { return ts; }
    }

    /** 🔹 작업 상태 정보 */
    public static final class TaskStatus {
        private final String status; // IN_PROGRESS, COMPLETED, CANCELLED, FAILED, CANCEL_REQUESTED
        private final Instant startTime;
        private final Instant endTime;
        private final String runner;
        private final double progress; // 0.0 ~ 100.0
        private final int currentItem; // 현재 처리된 항목 수
        private final int lastLogSeq; // 마지막으로 기록된 로그 시퀀스 번호
        private final int lastSentLogSeq; // 마지막으로 SSE로 전송된 로그 시퀀스 번호
        private final Map<String, Object> result;
        private final String errorMessage;

        public TaskStatus(String status, Instant startTime, Instant endTime, String runner, double progress, int currentItem, int lastLogSeq, int lastSentLogSeq, Map<String, Object> result, String errorMessage) {
            this.status = status;
            this.startTime = startTime;
            this.endTime = endTime;
            this.runner = runner;
            this.progress = progress;
            this.currentItem = currentItem;
            this.lastLogSeq = lastLogSeq;
            this.lastSentLogSeq = lastSentLogSeq;
            this.result = result;
            this.errorMessage = errorMessage;
        }

        // 복사 생성자 (상태 업데이트용)
        public TaskStatus(TaskStatus old, String status, Double progress, Integer currentItem, Integer lastLogSeq, Integer lastSentLogSeq, Map<String, Object> result, String errorMessage) {
            this.status = (status != null) ? status : old.status;
            this.startTime = old.startTime;
            this.endTime = (status != null && (status.equals("COMPLETED") || status.equals("FAILED") || status.equals("CANCELLED"))) ? Instant.now() : old.endTime;
            this.runner = old.runner;
            this.progress = (progress != null) ? progress : old.progress;
            this.currentItem = (currentItem != null) ? currentItem : old.currentItem;
            this.lastLogSeq = (lastLogSeq != null) ? lastLogSeq : old.lastLogSeq;
            this.lastSentLogSeq = (lastSentLogSeq != null) ? lastSentLogSeq : old.lastSentLogSeq;
            this.result = (result != null) ? result : old.result;
            this.errorMessage = (errorMessage != null) ? errorMessage : old.errorMessage;
        }

        // 상태 변경 시 생성자
        public TaskStatus(String status, Map<String, Object> result, String errorMessage) {
            // 기존 상태를 참조할 수 없는 경우 (시작, 종료, 실패 등 단일 이벤트)
            this(status, Instant.now(), Instant.now(), null, 0.0, 0, 0, 0, result, errorMessage);
        }

        // Getters
        public String getStatus() { return status; }
        public Instant getStartTime() { return startTime; }
        public Instant getEndTime() { return endTime; }
        public String getRunner() { return runner; }
        public double getProgress() { return progress; }
        public int getCurrentItem() { return currentItem; }
        public int getLastLogSeq() { return lastLogSeq; }
        public int getLastSentLogSeq() { return lastSentLogSeq; }
        public Map<String, Object> getResult() { return result; }
        public String getErrorMessage() { return errorMessage; }

        public Map<String, Object> toMap(boolean includeAllLogs) {
            Map<String, Object> map = new HashMap<>();
            map.put("status", status);
            map.put("runner", runner);
            map.put("progress", String.format("%.2f", progress));
            map.put("currentItem", currentItem);
            map.put("lastLogSeq", lastLogSeq);
            map.put("startTime", startTime.toString());
            if (endTime != null) map.put("endTime", endTime.toString());
            if (errorMessage != null) map.put("error", errorMessage);
            if (result != null && !result.isEmpty()) map.put("result", result);

            // SSE 브로드캐스트용으로만 사용 (로그 전송 시 마지막 전송 시퀀스를 사용)
            if (!includeAllLogs) {
                map.put("lastSentLogSeq", lastSentLogSeq);
            }

            return map;
        }
    }

    // ==============================================================
    // 💾 메모리 저장소 (Thread Safe)
    // ==============================================================
    // 작업 ID (taskId) -> 작업 상태 정보 (TaskStatus)
    private final Map<String, TaskStatus> statusMap = new ConcurrentHashMap<>();
    // 작업 ID (taskId) -> 로그 라인 리스트 (LogLine)
    private final Map<String, List<LogLine>> logsMap = new ConcurrentHashMap<>();
    // 작업 ID (taskId) -> 다음 로그 시퀀스 번호
    private final Map<String, Integer> logSeqMap = new ConcurrentHashMap<>();

    // 로그 최대 라인 수 (과도한 메모리 사용 방지)
    private static final int MAX_LOG_LINES = 700;

    // ==============================================================
    // ⚙️ 상태 변경 메서드
    // ==============================================================

    /** ✅ 작업 시작 */
    public void start(String taskId, String runner) {
        TaskStatus newStatus = new TaskStatus(
                "IN_PROGRESS", Instant.now(), null, runner, 0.0, 0, 0, 0, null, null
        );
        statusMap.put(taskId, newStatus);
        logsMap.put(taskId, new CopyOnWriteArrayList<>());
        logSeqMap.put(taskId, 0);
        log(taskId, "🟢 [SYSTEM] 작업 시작. 실행자: " + runner);
    }

    /** ✅ 진행률 업데이트 */
    public void updateProgress(String taskId, int currentItem, double progress) {
        statusMap.computeIfPresent(taskId, (id, old) ->
                new TaskStatus(old, null, progress, currentItem, null, null, null, null)
        );
    }

    /** ✅ 로그 추가 */
    public void log(String taskId, String line) {
        if (taskId == null) return;
        logsMap.computeIfPresent(taskId, (id, logs) -> {
            int nextSeq = logSeqMap.compute(id, (k, seq) -> (seq != null ? seq : 0) + 1);
            LogLine logLine = new LogLine(nextSeq, line);
            logs.add(logLine);
            // 최대 로그 라인 수 초과 시 가장 오래된 로그 제거 (UI 롤링 대응)
            if (logs.size() > MAX_LOG_LINES) {
                logs.remove(0);
            }
            // 마지막 로그 시퀀스 업데이트
            statusMap.computeIfPresent(id, (ignoredId, old) ->
                    new TaskStatus(old, null, null, null, nextSeq, null, null, null)
            );
            return logs;
        });
    }

    /** ✅ 마지막으로 전송된 로그 시퀀스 번호 업데이트 */
    public void updateLastSentLogSeq(String taskId, int seq) {
        statusMap.computeIfPresent(taskId, (id, old) ->
                new TaskStatus(old, null, null, null, null, seq, null, null)
        );
    }

    /** ✅ 작업 완료 */
    public void complete(String taskId, Map<String, Object> result) {
        statusMap.computeIfPresent(taskId, (id, old) ->
                new TaskStatus(old, "COMPLETED", 100.0, null, null, null, result, null)
        );
    }

    /** ✅ 작업 완료 (결과 없이) */
    public void complete(String taskId) {
        complete(taskId, null);
    }

    /** ✅ 작업 취소 요청됨 */
    public void cancelRequested(String taskId) {
        statusMap.computeIfPresent(taskId, (id, old) ->
                new TaskStatus(old, "CANCEL_REQUESTED", null, null, null, null, null, null)
        );
    }

    /** ✅ 작업 취소됨 */
    public void cancel(String taskId) {
        // 취소된 경우 progress는 0으로 리셋하지 않고 마지막 상태를 유지합니다.
        statusMap.computeIfPresent(taskId, (id, old) ->
                new TaskStatus(old, "CANCELLED", old.progress, old.currentItem, null, null, null, "사용자 요청에 의해 취소됨")
        );
        log(taskId, "🟡 [SYSTEM] 작업이 취소되었습니다.");
    }

    /** ✅ 작업 실패 */
    public void fail(String taskId, String err) {
        statusMap.computeIfPresent(taskId, (id, old) ->
                new TaskStatus(old, "FAILED", old.progress, old.currentItem, null, null, null, err)
        );
        log(taskId, "🔴 [SYSTEM] 작업 실패: " + err);
    }

    /** 전체 초기화 (재시작 시 사용) */
    public void reset(String taskId) {
        statusMap.remove(taskId);
        logsMap.remove(taskId);
        logSeqMap.remove(taskId);
    }

    // ==============================================================
    // 🔍 상태 조회 메서드
    // ==============================================================

    /** 작업의 스냅샷 상태를 Map 형태로 반환 (SSE 브로드캐스트용) */
    public Map<String, Object> snapshot(String taskId) {
        TaskStatus status = statusMap.get(taskId);
        if (status == null) {
            return Map.of("status", "IDLE", "progress", 0.0);
        }
        return status.toMap(false); // 로그 정보는 제외하고 전송 (SSE log 이벤트로 별도 처리)
    }

    /** 작업 상태 문자열 반환 */
    public String getStatus(String taskId) {
        TaskStatus status = statusMap.get(taskId);
        return (status != null) ? status.getStatus() : "IDLE";
    }

    /** 작업 시작 시간 반환 */
    public String getStartTime(String taskId) {
        TaskStatus status = statusMap.get(taskId);
        return (status != null && status.getStartTime() != null) ? status.getStartTime().toString() : "";
    }

    /**
     * 마지막으로 전송된 로그 시퀀스 이후의 신규 로그 리스트를 가져옵니다.
     * @param taskId 작업 ID
     * @param lastSentSeq 마지막으로 전송된 시퀀스 번호
     * @return 신규 로그 리스트
     */
    public List<LogLine> getNewLogs(String taskId, int lastSentSeq) {
        List<LogLine> allLogs = logsMap.getOrDefault(taskId, Collections.emptyList());
        // lastSentSeq보다 큰 시퀀스 번호를 가진 로그만 필터링합니다.
        // CopyOnWriteArrayList이므로 stream 처리가 안전합니다.
        return allLogs.stream()
                .filter(logLine -> logLine.getSeq() > lastSentSeq)
                .collect(Collectors.toList());
    }

    /**
     * 작업에 기록된 모든 로그 라인을 반환합니다. (디버깅/전체 조회용)
     */
    public List<LogLine> getAllLogs(String taskId) {
        return logsMap.getOrDefault(taskId, Collections.emptyList());
    }

    // ==============================================================
    // 🧩 Python JSON 파싱 유틸
    // ==============================================================

    private final ObjectMapper mapper = new ObjectMapper();

    /** Python이 반환한 JSON이 `{}` 형태일 때 */
    public Map<String, Object> parseJsonMap(String json) {
        try {
            if (json == null || json.trim().isEmpty()) return new LinkedHashMap<>();
            return mapper.readValue(json, new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            throw new RuntimeException("JSON 파싱 오류(Map): " + e.getMessage(), e);
        }
    }

    /** Python이 반환한 JSON이 `[]` 형태일 때 */
    public List<Map<String, Object>> parseJsonList(String json) {
        try {
            if (json == null || json.trim().isEmpty()) return Collections.emptyList();
            return mapper.readValue(json, new TypeReference<List<Map<String, Object>>>() {});
        } catch (Exception e) {
            throw new RuntimeException("JSON 파싱 오류(List): " + e.getMessage(), e);
        }
    }

    // ==============================================================
    // 🧩 JSON 역변환 유틸 (SSE 브로드캐스트용)
    // ==============================================================

    /** Map을 JSON 문자열로 변환 (SSE Data 전송용) */
    public String mapToJsonString(Map<String, Object> map) throws JsonProcessingException {
        return mapper.writeValueAsString(map);
    }

    /** List를 JSON 문자열로 변환 (SSE Data 전송용) */
    public String listToJsonString(List<Map<String, Object>> list) throws JsonProcessingException {
        return mapper.writeValueAsString(list);
    }
}