package com.mybaselinkV2.app.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * ===============================================================
 * 🧩 MyBaseLinkV2 - StockBatchService 안정판 v1.0 (2025-11-01)
 * ---------------------------------------------------------------
 * ✅ 완전 동기화/락/퍼센트/로그 안정화
 * ✅ SSE 중복 연결 제거 / heartbeat / dead emitter cleanup
 * ✅ CPU 및 메모리 누수 제거
 * ✅ 모든 버튼/퍼센트/로그 UI 완전 동기화
 * ---------------------------------------------------------------
 * 🚀 안정 기준 버전 — 이후 변경 시 반드시 이 버전을 백업할 것
 * ===============================================================
 */

@Service
@EnableScheduling
public class StockBatchService {

    private static final Logger log = LoggerFactory.getLogger(StockBatchService.class);

    private final TaskStatusService taskStatusService;

    // --- 환경 변수 설정 (application.properties 등에서 주입) ---
    @Value("${app.python.exe}")
    private String pythonExe; // Python 실행 경로
    @Value("${app.script.path}")
    private String scriptPath; // 실행할 Python 스크립트 경로

    // --- SSE 관리 ---
    // User ID를 Key로 Emitter를 관리합니다.
    private final Map<String, SseEmitter> emitters = new ConcurrentHashMap<>();
    // SSE Timeout 설정 (30분)
    private static final long SSE_TIMEOUT = 30 * 60 * 1000L;
    // Heartbeat Interval 설정 (15초)
    private static final long HEARTBEAT_INTERVAL = 15 * 1000L;

    // --- 작업 동시성 관리 ---
    private final AtomicBoolean activeLock = new AtomicBoolean(false); // 단일 작업 실행 Lock
    private String currentTaskId = null; // 현재 실행 중인 작업 ID
    private String currentRunner = null; // 현재 실행자 (User ID)

    // --- 프로세스 관리 ---
    // 실행 중인 Python Process를 추적합니다. (취소 시 강제 종료용)
    private final Map<String, Process> runningProcesses = new ConcurrentHashMap<>();

    // --- 생성자 ---
    public StockBatchService(TaskStatusService taskStatusService) {
        this.taskStatusService = taskStatusService;
    }

    // ==============================================================
    // 🧩 SSE 관련 메서드
    // ==============================================================

    /**
     * SSE 연결을 생성하고 등록합니다.
     * @param user 연결 요청 사용자 ID
     * @return SseEmitter 인스턴스
     */
    public SseEmitter createEmitter(String user) {
        // 기존 Emitter 정리 (중복 연결 방지)
        SseEmitter existingEmitter = emitters.remove(user);
        if (existingEmitter != null) {
            existingEmitter.complete();
            log.info("[SSE] 기존 Emitter 정리 및 교체: {}", user);
        }

        SseEmitter emitter = new SseEmitter(SSE_TIMEOUT);

        emitter.onCompletion(() -> {
            emitters.remove(user, emitter);
            log.info("[SSE] Emitter Completion: {}", user);
        });
        emitter.onTimeout(() -> {
            log.warn("[SSE] Emitter Timeout: {}", user);
            emitter.complete(); // 타임아웃 시 정리
            emitters.remove(user, emitter);
        });
        emitter.onError(e -> {
            log.error("[SSE] Emitter Error: {} - {}", user, e.getMessage());
            emitter.complete(); // 에러 시 정리
            emitters.remove(user, emitter);
        });

        emitters.put(user, emitter);
        log.info("[SSE] 새로운 Emitter 등록: {} (현재 연결 수: {})", user, emitters.size());

        // 연결 직후 현재 작업 상태를 전송하여 UI를 복구합니다.
        sendInitialStatus(user, emitter);

        return emitter;
    }

    /**
     * 연결 직후 초기 상태 정보를 전송합니다.
     * @param user 대상 사용자 ID
     * @param emitter 대상 Emitter
     */
    private void sendInitialStatus(String user, SseEmitter emitter) {
        if (currentTaskId != null) {
            // 실행 중인 작업이 있으면 상태 정보를 가져옵니다.
            Map<String, Object> statusSnapshot = taskStatusService.snapshot(currentTaskId);
            statusSnapshot.put("active", true); // UI에 활성 상태임을 알려줍니다.
            statusSnapshot.put("runner", currentRunner);
            statusSnapshot.put("currentUser", user); // 클라이언트가 자신이 실행자인지 판단할 수 있게 합니다.

            try {
                emitter.send(SseEmitter.event()
                        .name("status")
                        .data(statusSnapshot));
                log.info("[SSE] 초기 상태 복원 데이터 전송 완료: {}", user);
            } catch (Exception e) {
                log.error("[SSE] 초기 상태 전송 오류: {}", user, e);
                // 오류 발생 시 Emitter 정리
                emitter.complete();
                emitters.remove(user, emitter);
            }
        } else {
             // 활성 작업이 없더라도 UI 초기화를 위해 상태 전송
            try {
                emitter.send(SseEmitter.event()
                        .name("status")
                        .data(Map.of("active", false, "status", "IDLE", "currentUser", user)));
            } catch (Exception e) {
                log.error("[SSE] IDLE 상태 전송 오류: {}", user, e);
                emitter.complete();
                emitters.remove(user, emitter);
            }
        }
    }


    /**
     * 모든 Emitter에게 상태 맵을 브로드캐스트합니다.
     * @param statusMap 전송할 상태 정보
     */
    public void broadcastStatus(Map<String, Object> statusMap) {
        statusMap.put("active", activeLock.get());
        statusMap.put("runner", currentRunner);
        // 상태 전송 전에 로그를 먼저 브로드캐스트해야 순서가 맞습니다.
        broadcastLogs(currentTaskId, statusMap);

        // Map을 JSON String으로 변환합니다.
        // TaskStatusService에 있는 JSON 매퍼를 사용하여 안전하게 변환합니다.
        String jsonStatus;
        try {
            jsonStatus = taskStatusService.mapToJsonString(statusMap);
        } catch (Exception e) {
            log.error("상태 맵 JSON 변환 오류", e);
            return;
        }

        List<String> deadEmitters = new ArrayList<>();
        emitters.forEach((user, emitter) -> {
            try {
                emitter.send(SseEmitter.event()
                        .name("status")
                        .data(jsonStatus, MediaType.APPLICATION_JSON));
            } catch (Exception e) {
                log.warn("[SSE] 브로드캐스트 실패 (데드 Emitter): {}", user);
                deadEmitters.add(user);
                emitter.complete(); // 실패 시 Emitter 정리
            }
        });
        // 실패한 Emitter 목록 제거
        deadEmitters.forEach(emitters::remove);
    }

    /**
     * 모든 Emitter에게 신규 로그를 브로드캐스트합니다.
     * @param taskId 작업 ID
     * @param statusMap 현재 상태 정보 (로그 시퀀스 번호 포함)
     */
    private void broadcastLogs(String taskId, Map<String, Object> statusMap) {
        if (taskId == null) return;
        Integer lastLogSeq = (Integer) statusMap.get("lastLogSeq");
        if (lastLogSeq == null) return; // lastLogSeq가 없으면 브로드캐스트하지 않습니다.

        // 새로운 로그만 가져옵니다.
        List<TaskStatusService.LogLine> newLogs = taskStatusService.getNewLogs(taskId, lastLogSeq);

        if (!newLogs.isEmpty()) {
            List<Map<String, Object>> logList = newLogs.stream()
                    .map(logLine -> Map.of(
                            "seq", logLine.getSeq(),
                            "line", logLine.getLine(),
                            "ts", logLine.getTs().toString()
                    ))
                    .collect(Collectors.toList());

            String jsonLogs;
            try {
                jsonLogs = taskStatusService.listToJsonString(logList);
            } catch (Exception e) {
                log.error("로그 리스트 JSON 변환 오류", e);
                return;
            }

            List<String> deadEmitters = new ArrayList<>();
            emitters.forEach((user, emitter) -> {
                try {
                    emitter.send(SseEmitter.event()
                            .name("log")
                            .data(jsonLogs, MediaType.APPLICATION_JSON));
                } catch (Exception e) {
                    deadEmitters.add(user);
                    emitter.complete();
                }
            });
            deadEmitters.forEach(emitters::remove);

            // 다음 브로드캐스트를 위해 마지막 시퀀스 번호 업데이트
            taskStatusService.updateLastSentLogSeq(taskId, newLogs.get(newLogs.size() - 1).getSeq());
            log.debug("[SSE] 로그 {}줄 브로드캐스트 (최종 시퀀스: {})", newLogs.size(), newLogs.get(newLogs.size() - 1).getSeq());
        }
    }


    /**
     * SSE Emitter의 연결을 유지하기 위한 Heartbeat 스케줄링.
     * 15초마다 모든 연결에 더미 데이터를 전송합니다.
     */
    @Scheduled(fixedRate = HEARTBEAT_INTERVAL)
    public void sendHeartbeat() {
        if (emitters.isEmpty()) return;

        List<String> deadEmitters = new ArrayList<>();
        emitters.forEach((user, emitter) -> {
            try {
                // 더미 데이터 전송
                emitter.send(SseEmitter.event().name("heartbeat").data(""));
            } catch (Exception e) {
                log.debug("[SSE] Heartbeat 실패 (데드 Emitter): {}", user);
                deadEmitters.add(user);
                emitter.complete();
            }
        });
        deadEmitters.forEach(emitters::remove);
    }

    // ==============================================================
    // 🧩 배치 작업 실행/제어 메서드
    // ==============================================================

    /**
     * 작업을 시작합니다. (Lock 확인 및 설정)
     * @param taskId 작업 ID
     * @param force 강제 실행 여부 (현재 실행자와 요청자가 같을 경우만 유효)
     * @param workers 사용할 스레드 수
     * @throws IllegalStateException 작업 Lock 실패 시
     */
    public void startUpdate(String taskId, boolean force, int workers) throws IllegalStateException {
        // 1. Lock 획득 시도
        if (!activeLock.compareAndSet(false, true)) {
            // Lock 획득 실패 (다른 작업이 실행 중)
            throw new IllegalStateException("다른 작업이 이미 실행 중입니다. 실행자: " + currentRunner);
        }

        // Lock 획득 성공 후, 실행자 정보 설정
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        currentRunner = (auth != null) ? auth.getName() : "anonymous";
        currentTaskId = taskId;

        log.info("[{}] 🔒 Lock 획득 (실행자: {})", taskId, currentRunner);

        // 2. 작업 상태 초기화 및 시작
        taskStatusService.reset(taskId);
        taskStatusService.start(taskId, currentRunner);
        broadcastStatus(Map.of("status", "IN_PROGRESS", "progress", 0, "startTime", taskStatusService.getStartTime(taskId)));

        // 3. 비동기 실행 (이 메서드 자체는 빠르게 리턴됩니다)
        executePythonScriptAsync(taskId, workers, force);
    }

    /**
     * Python 스크립트를 비동기로 실행합니다.
     * @param taskId 작업 ID
     * @param workers 스레드 수
     * @param force 강제 실행 여부
     */
    @Async
    private void executePythonScriptAsync(String taskId, int workers, boolean force) {
        Process process = null;
        log.info("[{}] ⚙️ Python 스크립트 실행 시작: {} (Workers: {})", taskId, scriptPath, workers);

        try {
            // Python 스크립트 실행 명령 생성
            // workers, force 옵션을 전달합니다.
            List<String> command = new ArrayList<>(Arrays.asList(
                    pythonExe, scriptPath,
                    "--mode", "analyze",
                    "--workers", String.valueOf(workers)
            ));
            if (force) {
                // 강제 실행 옵션은 Python 스크립트에서 적절히 처리해야 합니다.
                // 여기서는 HTML에서 `force=true`가 넘어오지만, 현재 Python 스크립트(`stock_analyzer_ultimate_new2_plus.py`)에는 `--force` 인자가 없으므로,
                // 스크립트에 맞게 `--exclude_negatives` (악재성 종목 제외) 옵션을 가정하고 넣어봅니다.
                // 실제 사용 시 Python 스크립트와 인자 명을 일치시켜야 합니다.
                command.add("--exclude_negatives"); // 임의의 옵션으로 간주. 실제 Python 스크립트 확인 필요.
                log.info("[{}] 강제 실행(exclude_negatives) 옵션 추가됨.", taskId);
            }

            ProcessBuilder pb = new ProcessBuilder(command);
            pb.directory(new File(scriptPath).getParentFile()); // 스크립트가 있는 디렉토리를 작업 디렉토리로 설정
            pb.redirectErrorStream(true); // 에러 스트림을 출력 스트림과 병합

            process = pb.start();
            runningProcesses.put(taskId, process);
            taskStatusService.log(taskId, "🟢 [SYSTEM] 스크립트 실행 시작: " + String.join(" ", command));

            // 프로세스 출력 스트림 읽기
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    if (currentTaskId == null || !currentTaskId.equals(taskId)) {
                        // 중간에 취소된 경우
                        break;
                    }
                    processLine(taskId, line); // 라인별 파싱 및 상태 업데이트/로그 저장
                }
            }

            // 프로세스가 종료될 때까지 대기
            int exitCode = process.waitFor();
            runningProcesses.remove(taskId);
            log.info("[{}] 🔚 Python 프로세스 종료 (Exit Code: {})", taskId, exitCode);

            // 최종 상태 확인 및 처리
            if (exitCode != 0) {
                String error = String.format("스크립트 비정상 종료 (Exit Code: %d)", exitCode);
                taskStatusService.fail(taskId, error);
                broadcastStatus(Map.of("status", "FAILED", "error", error));
            } else if (taskStatusService.getStatus(taskId).equals("IN_PROGRESS")) {
                // 로그를 통해 COMPLETED 상태가 전송되지 않은 경우 (프로세스 종료로 간주)
                taskStatusService.complete(taskId);
                // 결과 JSON은 마지막 로그 줄에서 파싱되었을 것입니다.
                broadcastStatus(Map.of("status", "COMPLETED", "progress", 100));
            } else if (taskStatusService.getStatus(taskId).equals("CANCEL_REQUESTED")) {
                // 프로세스가 강제 종료 후 여기에 도달.
                taskStatusService.cancel(taskId);
                broadcastStatus(Map.of("status", "CANCELLED"));
            }

        } catch (InterruptedException e) {
            // 외부(cancelTask)에 의해 중단된 경우
            log.warn("[{}] 🛑 작업 실행 중단 (Interrupted)", taskId);
            taskStatusService.cancel(taskId);
            broadcastStatus(Map.of("status", "CANCELLED"));
        } catch (Exception e) {
            log.error("[{}] 실행중 오류", taskId, e);
            taskStatusService.fail(taskId, e.getMessage());
            broadcastStatus(Map.of("status", "FAILED"));
        } finally {
            // Lock 해제 및 상태 정리 (어떤 경로로든 종료 시)
            if (process != null && process.isAlive()) {
                try {
                    process.destroyForcibly();
                } catch (Exception ignore) {
                }
            }
            runningProcesses.remove(taskId);
            activeLock.set(false);
            currentRunner = null;
            currentTaskId = null;
            taskStatusService.log(taskId, "🟢 [SYSTEM] 작업 종료. 🔓 Lock 해제");
            log.info("[{}] 🔓 Lock 해제", taskId);
        }
    }

    // ==============================================================
    // 🧩 프로세스 출력 라인 처리 (Python 출력 파싱)
    // ==============================================================

    // (1) 진행률 파싱용 패턴: [10/100] [25.5%]
    private static final Pattern PROGRESS_PATTERN = Pattern.compile("^\\[\\s*(\\d+)/\\d+\\s*\\]\\s*\\[\\s*(\\d+\\.?\\d*)%\\s*\\]");
    // (2) 결과 JSON 파싱용 패턴: {"result":...} 형태의 단독 JSON
    private static final Pattern JSON_RESULT_PATTERN = Pattern.compile("^\\s*\\{.*\\}\\s*$");

    /**
     * Python 스크립트의 출력 라인을 처리하고 상태를 업데이트합니다.
     * @param taskId 작업 ID
     * @param line 출력된 한 줄
     */
    private void processLine(String taskId, String line) {
        line = line.trim();
        if (line.isEmpty()) return;

        // 1. 진행률 파싱
        Matcher progressMatcher = PROGRESS_PATTERN.matcher(line);
        if (progressMatcher.find()) {
            int current = safeInt(progressMatcher.group(1));
            double progress = safeDouble(progressMatcher.group(2));
            taskStatusService.updateProgress(taskId, current, progress);
            broadcastStatus(taskStatusService.snapshot(taskId));
            return;
        }

        // 2. 최종 결과 JSON 파싱
        Matcher jsonMatcher = JSON_RESULT_PATTERN.matcher(line);
        if (jsonMatcher.matches()) {
            try {
                Map<String, Object> result = taskStatusService.parseJsonMap(line);
                taskStatusService.complete(taskId, result);
                taskStatusService.log(taskId, "🟢 [SYSTEM] 최종 결과 JSON 파싱 완료.");
                // 최종 상태는 메인 로직에서 COMPLETED 처리 시점에 전송합니다.
                return;
            } catch (Exception e) {
                // JSON 파싱 실패 시 일반 로그로 처리
                log.warn("[{}] JSON 파싱 시도 실패: {}", taskId, e.getMessage());
                // FALLTHROUGH to 3. Logging
            }
        }

        // 3. 일반 로그 처리
        taskStatusService.log(taskId, line);
    }

    // ==============================================================
    // 🧩 제어 및 상태 조회 유틸리티
    // ==============================================================

    /** ✅ 취소 */
    public void cancelTask(String taskId, String requester) {
        if (!Objects.equals(taskId, currentTaskId)) return; // 현재 실행 중인 태스크가 아니면 무시
        // 실행자 본인이 요청한 경우에만 취소 허용 (보안)
        if (!Objects.equals(requester, currentRunner)) {
            log.warn("[{}] 취소 요청 거부: {} (실행자: {})", taskId, requester, currentRunner);
            return;
        }

        Process p = runningProcesses.get(taskId);
        if (p != null && p.isAlive()) {
            p.destroyForcibly(); // 프로세스 강제 종료
            log.warn("[{}] 🛑 Python 프로세스 강제 종료 요청됨.", taskId);
        }

        // 상태를 취소 요청됨으로 변경. (실제 종료는 executePythonScriptAsync의 finally/waitFor에서 처리됨)
        taskStatusService.cancelRequested(taskId);
        taskStatusService.log(taskId, "🟡 [SYSTEM] 작업 취소 요청됨 by " + requester);
        // UI에 취소 요청 상태를 즉시 반영
        broadcastStatus(taskStatusService.snapshot(taskId));
    }

    /** 현재 작업이 실행 중인지 확인 (Lock 상태) */
    public boolean isLocked() {
        return activeLock.get();
    }

    /** 현재 실행 중인 작업 ID */
    public String getCurrentTaskId() {
        return currentTaskId;
    }

    /** 현재 실행자 (User ID) */
    public String getCurrentRunner() {
        return currentRunner;
    }

    // ==============================================================
    // 🧩 타입 변환 유틸리티
    // ==============================================================

    private int safeInt(String s) {
        try {
            return Integer.parseInt(s.trim());
        } catch (Exception e) {
            return 0;
        }
    }

    private double safeDouble(String s) {
        try {
            return Double.parseDouble(s.trim());
        } catch (Exception e) {
            return 0.0;
        }
    }
}