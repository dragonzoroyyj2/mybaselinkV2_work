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
 * 🧩 MyBaseLinkV2 - StockBatchService 안정판 v1.1 (2025-11-07)
 * ---------------------------------------------------------------
 * ✅ 기존 업데이트 기능 유지 (startUpdate)
 * ✅ 분석 기능 추가 (startAnalysis) 및 캐싱 로직 통합
 * ✅ 모든 버튼/퍼센트/로그 UI 완전 동기화
 * ---------------------------------------------------------------
 * ===============================================================
 */

@Service
@EnableScheduling
public class StockBatchService {

    private static final Logger log = LoggerFactory.getLogger(StockBatchService.class);
    private final TaskStatusService taskStatusService;

    @Value("${python.executable.path:python}")
    private String pythonExe;

    @Value("${python.update_stock_listing.path}")
    private String scriptPathUpdate; // 기존 업데이트 스크립트 경로

    @Value("${python.analysis_stock.path}")
    private String scriptPathAnalysis; // 새로운 분석 스크립트 경로 (예: Athena-K-Market-AI.py)

    @Value("${python.working.dir}")
    private String workingDir;

    /** 사용자별 emitter */
    private static final class Client {
        final String user;
        final SseEmitter emitter;
        long lastActive;
        Client(String user, SseEmitter emitter) {
            this.user = user;
            this.emitter = emitter;
            this.lastActive = System.currentTimeMillis();
        }
    }

    private final CopyOnWriteArrayList<Client> clients = new CopyOnWriteArrayList<>();

    private final AtomicBoolean activeLock = new AtomicBoolean(false);
    private final Map<String, Process> runningProcesses = new ConcurrentHashMap<>();

    private volatile String currentRunner = null;
    private volatile String currentTaskId = null;

    public StockBatchService(TaskStatusService taskStatusService) {
        this.taskStatusService = taskStatusService;
    }

    private String currentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        return (auth != null ? auth.getName() : "anonymous");
    }

    /** ✅ 동일 사용자 연결 닫기 */
    private void closeExistingForUser(String user) {
        for (Client c : new ArrayList<>(clients)) {
            if (Objects.equals(c.user, user)) {
                try { c.emitter.complete(); } catch (Exception ignored) {}
                clients.remove(c);
            }
        }
    }

    /** ✅ 브로드캐스트 (owner 계산 포함) */
    private void broadcastStatus(Map<String, Object> base) {
        for (Client c : new ArrayList<>(clients)) {
            Map<String, Object> payload = new LinkedHashMap<>(base);
            payload.put("runner", currentRunner);
            // 현재 작업의 소유자인지 확인
            payload.put("owner", Objects.equals(c.user, currentRunner));
            payload.put("currentUser", c.user);
            try {
                c.emitter.send(SseEmitter.event().name("status").data(payload));
                c.lastActive = System.currentTimeMillis();
            } catch (Exception e) {
                log.warn("🧹 Emitter send 실패 → 제거됨: {}", c.user);
                clients.remove(c);
            }
        }
    }

    /** ✅ 신규 클라이언트 1명에게만 전송 */
    private void sendTo(Client c, Map<String, Object> data) {
        try {
            // Emitter가 유효한지 확인
            if (c.emitter == null) return;
            c.emitter.send(SseEmitter.event().name("status").data(data));
            c.lastActive = System.currentTimeMillis();
        } catch (Exception e) {
            clients.remove(c);
        }
    }

    /** ✅ SSE 구독 생성 */
    public SseEmitter createEmitter(String user) {
        closeExistingForUser(user);

        SseEmitter emitter = new SseEmitter(0L);
        Client me = new Client(user, emitter);
        clients.add(me);

        emitter.onCompletion(() -> clients.remove(me));
        emitter.onTimeout(() -> clients.remove(me));
        emitter.onError(e -> {
            log.warn("❌ SSE 오류 감지: {} -> 연결 해제", user);
            clients.remove(me);
        });

        if (activeLock.get() && currentTaskId != null) {
            Map<String, Object> snap = taskStatusService.snapshot(currentTaskId);
            double progress = 0;
            // 스냅샷에서 진행률 추출
            if (snap != null && snap.get("result") instanceof Map r && r.get("progress") instanceof Number p)
                progress = ((Number) p).doubleValue();

            Map<String, Object> init = new LinkedHashMap<>();
            init.put("status", snap.getOrDefault("status", "IN_PROGRESS")); // 현재 상태 반영
            init.put("runner", currentRunner);
            init.put("owner", Objects.equals(user, currentRunner));
            init.put("currentUser", user);
            init.put("progress", progress);

            // 완료된 작업의 경우 최종 데이터를 함께 전송 (프론트엔드 복원용)
            if ("COMPLETED".equals(snap.get("status")) && snap.get("result") instanceof Map r) {
                if (r.containsKey("finalData")) {
                    init.put("resultData", r.get("finalData"));
                }
            }

            sendTo(me, init);
        } else {
            sendTo(me, Map.of("status", "IDLE", "currentUser", user));
        }
        return emitter;
    }

    /** ✅ Heartbeat (10초마다 ping) */
    @Scheduled(fixedRate = 10000)
    public void heartbeat() {
        for (Client c : new ArrayList<>(clients)) {
            try {
                c.emitter.send(SseEmitter.event().name("ping").data("keep-alive"));
                c.lastActive = System.currentTimeMillis();
            } catch (Exception e) {
                log.debug("💔 Heartbeat 실패 → {}", c.user);
                clients.remove(c);
            }
        }
    }

    /** ✅ Dead Emitter 정리 (30초 이상 반응 없으면 제거) */
    @Scheduled(fixedRate = 30000)
    public void cleanupDeadEmitters() {
        long now = System.currentTimeMillis();
        for (Client c : new ArrayList<>(clients)) {
            if (now - c.lastActive > 30000) {
                log.warn("🧹 Dead emitter 정리됨: {}", c.user);
                clients.remove(c);
                try { c.emitter.complete(); } catch (Exception ignore) {}
            }
        }
    }

    /**
     * 🚀 일괄 업데이트 (기존 기능)
     * - `python.update_stock_listing.path` 스크립트 실행
     */
    @Async
    public void startUpdate(String taskId, boolean force, int workers) {
        runPythonBatch(taskId, scriptPathUpdate, List.of(
            "--workers", String.valueOf(workers),
            force ? "--force" : ""
        ).stream().filter(s -> !s.isEmpty()).collect(Collectors.toList()), false);
    }


    /**
     * 🔬 주식 패턴 분석 시작 (신규 기능)
     * - `python.analysis_stock.path` 스크립트 실행
     * - 캐싱 로직 포함
     */
    @Async
    public void startAnalysis(String taskId, String analysisType, List<Integer> maPeriods,
                              boolean excludeNegatives, int dataPeriodYears, int topNCount) {

        String runner = currentUser();

        // 1. 🛑 선점 처리
        if (activeLock.get() && !Objects.equals(runner, currentRunner))
            throw new IllegalStateException("다른 사용자가 분석 중입니다.");
        else
            activeLock.set(true);

        currentRunner = runner;
        currentTaskId = taskId;

        // 2. 🔔 캐시 키 생성 (모든 파라미터 포함)
        String maPeriodsStr = maPeriods != null ? 
                              maPeriods.stream().map(String::valueOf).collect(Collectors.joining(",")) : "";
        String cacheKey = String.format("ANALYSIS_%s_%s_%b_%d_%d",
            analysisType, maPeriodsStr, excludeNegatives, dataPeriodYears, topNCount);
        
        // 3. 🔍 캐시 조회
        Map<String, Object> cachedResult = taskStatusService.getAnalysisResultCache(cacheKey);

        if (cachedResult != null) {
            // ✅ 캐시 히트 (Hit) - 즉시 완료 처리
            log.info("[{}] ✅ 캐시 히트: 분석 결과를 즉시 반환합니다. Key: {}", taskId, cacheKey);
            
            taskStatusService.complete(taskId);
            taskStatusService.updateFinalResult(taskId, cachedResult);
            
            // SSE 브로드캐스트 (최종 결과 Map 포함)
            broadcastStatus(Map.of(
                "status", "COMPLETED",
                "progress", 100,
                "resultData", cachedResult,
                "logs", List.of("[LOG] 캐시된 분석 결과를 즉시 반환했습니다.")
            ));
            
            // ⚠️ 락 해제 및 종료
            cleanupTaskLock(taskId);
            return; 
        }

        // 4. ❌ 캐시 미스 (Miss) - 파이썬 실행 준비
        List<String> args = new ArrayList<>();
        args.add("--analysis_type"); args.add(analysisType);
        args.add("--data_period_years"); args.add(String.valueOf(dataPeriodYears));
        args.add("--top_n_count"); args.add(String.valueOf(topNCount));
        if (!maPeriodsStr.isEmpty()) {
             args.add("--ma_periods"); args.add(maPeriodsStr);
        }
        if (excludeNegatives) args.add("--exclude_negatives");

        runPythonBatch(taskId, scriptPathAnalysis, args, true);
        
        // 5. 💾 파이썬 실행 완료 후, 캐시에 저장 (runPythonBatch 내부에서 처리됨)
        // runPythonBatch가 완료되면 락이 해제되므로 이 메서드에는 더 이상 코드가 필요 없음
    }


    /**
     * 🧪 Python 프로세스 실행 공통 로직 (startUpdate, startAnalysis 통합)
     * @param taskId 현재 작업 ID
     * @param scriptPath 실행할 Python 스크립트 경로
     * @param args 스크립트에 전달할 인자 목록
     * @param isAnalysis 분석 작업 여부 (캐싱을 위해 필요)
     */
    private void runPythonBatch(String taskId, String scriptPath, List<String> args, boolean isAnalysis) {
        
        String runner = currentRunner; // 락을 획득했으므로 사용 가능

        taskStatusService.reset(taskId);
        broadcastStatus(Map.of(
            "status", "RESET", "progress", 0,
            "logs", List.of("[LOG] 새 작업 준비 중... (스크립트: " + new File(scriptPath).getName() + ")")
        ));

        taskStatusService.setTaskStatus(taskId,
            new TaskStatusService.TaskStatus("IN_PROGRESS",
                new HashMap<>(Map.of("progress", 0, "runner", runner)), null));

        broadcastStatus(Map.of("status", "START", "progress", 0));

        Process process = null;
        String finalPythonOutput = null;

        try {
            List<String> cmd = new ArrayList<>();
            cmd.add(pythonExe); cmd.add("-u"); cmd.add(scriptPath);
            cmd.addAll(args);

            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.directory(new File(workingDir));
            pb.redirectErrorStream(true);
            pb.environment().put("PYTHONIOENCODING", "utf-8");

            process = pb.start();
            runningProcesses.put(taskId, process);

            // (기존 업데이트 로직의 파싱 패턴)
            Pattern pProgress = Pattern.compile("\\[PROGRESS]\\s*(\\d+(?:\\.\\d+)?)");
            Pattern pKrxTotal = Pattern.compile("\\[KRX_TOTAL]\\s*(\\d+)");
            Pattern pKrxSaved = Pattern.compile("\\[KRX_SAVED]\\s*(\\d+)");
            Pattern pCount = Pattern.compile("\\((\\d+)/(\\d+)\\)");

            int krxTotal=0, krxSaved=0, dataTotal=0, dataSaved=0;
            double progress=0; long lastFlush=System.currentTimeMillis();
            List<String> buffer=new ArrayList<>();

            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {

                String line;
                while ((line = reader.readLine()) != null) {
                    taskStatusService.appendLog(taskId, line);
                    log.info("[PYTHON] {}", line);
                    buffer.add(line);

                    // 💡 최종 JSON 결과 추출 (분석 작업의 경우)
                    if (isAnalysis && line.trim().startsWith("{") && line.trim().endsWith("}")) {
                        finalPythonOutput = line; // 마지막으로 수신된 JSON 라인을 저장
                    }


                    // 💡 기존 업데이트 작업의 진행률 계산 로직 (분석 작업은 Python의 PROGRESS만 사용 권장)
                    if (!isAnalysis) {
                        Matcher mKT=pKrxTotal.matcher(line); if(mKT.find()) krxTotal=safeInt(mKT.group(1));
                        Matcher mKS=pKrxSaved.matcher(line); if(mKS.find()) krxSaved=safeInt(mKS.group(1));
                        Matcher mCnt=pCount.matcher(line); if(mCnt.find()){ dataSaved=safeInt(mCnt.group(1)); dataTotal=safeInt(mCnt.group(2)); }

                        double krxPct=(krxTotal>0)?(krxSaved*100.0/krxTotal):0;
                        double dataPct=(dataTotal>0)?(dataSaved*100.0/dataTotal):0;
                        double weighted=(krxPct*0.2)+(dataPct*0.8);
                        progress=Math.min(100, weighted);
                    }

                    // Python이 명시적으로 보낸 PROGRESS를 최우선으로 반영
                    Matcher mProg=pProgress.matcher(line); 
                    if(mProg.find()) {
                        double pythonProg = safeDouble(mProg.group(1));
                        progress=Math.max(progress, pythonProg);
                    }
                    
                    if(System.currentTimeMillis()-lastFlush>500){
                        Map<String,Object> payload=new LinkedHashMap<>();
                        payload.put("status","IN_PROGRESS");
                        payload.put("progress",progress);
                        payload.put("logs",new ArrayList<>(buffer));
                        if (!isAnalysis) {
                            payload.put("krxTotal",krxTotal); payload.put("krxSaved",krxSaved);
                            payload.put("dataTotal",dataTotal); payload.put("dataSaved",dataSaved);
                        }
                        taskStatusService.updateProgress(taskId,progress,runner);
                        broadcastStatus(payload);
                        buffer.clear();
                        lastFlush=System.currentTimeMillis();
                    }
                }
            }

            // 6. ⏰ 프로세스 종료 대기 및 상태 확인
            boolean finished=process.waitFor(Duration.ofHours(1).toSeconds(),TimeUnit.SECONDS);
            if(!finished){ 
                process.destroyForcibly(); 
                taskStatusService.fail(taskId,"시간 초과");
                broadcastStatus(Map.of("status","FAILED")); 
                return; 
            }
            if(process.exitValue()!=0){ 
                taskStatusService.fail(taskId,"Python 오류 종료 (Exit Code: " + process.exitValue() + ")");
                broadcastStatus(Map.of("status","FAILED")); 
                return; 
            }
            
            // 7. 🎉 성공 처리 및 최종 데이터 저장/캐싱
            Map<String, Object> finalResultData = new LinkedHashMap<>();
            if (isAnalysis) {
                if (finalPythonOutput != null) {
                    finalResultData = taskStatusService.parseJsonMap(finalPythonOutput);
                }
                
                // 💾 캐시에 저장
                String currentCacheKey = String.format("ANALYSIS_%s_%s_%b_%d_%d",
                    args.get(1), args.get(3), args.contains("--exclude_negatives"), 
                    safeInt(args.get(5)), safeInt(args.get(7))); // 매개변수 구조에 따라 키 재생성
                taskStatusService.setAnalysisResultCache(currentCacheKey, finalResultData);
                
                // TaskStatus에 최종 결과 데이터 저장
                taskStatusService.updateFinalResult(taskId, finalResultData);

                log.info("[{}] ✅ 분석 완료 및 캐싱 성공. 결과 크기: {} items", taskId, finalResultData.size());
            }


            taskStatusService.complete(taskId);
            
            Map<String, Object> completePayload = new LinkedHashMap<>();
            completePayload.put("status","COMPLETED");
            completePayload.put("progress",100);
            completePayload.put("logs",List.of("[LOG] 모든 작업 완료"));
            if (isAnalysis) {
                 completePayload.put("resultData", finalResultData);
            } else {
                 completePayload.put("krxTotal",krxTotal); completePayload.put("krxSaved",krxTotal);
                 completePayload.put("dataTotal",dataTotal); completePayload.put("dataSaved",dataTotal);
            }
            broadcastStatus(completePayload);

        } catch(Exception e){
            log.error("[{}] 실행중 오류",taskId,e);
            taskStatusService.fail(taskId,e.getMessage());
            broadcastStatus(Map.of("status","FAILED"));
        } finally {
            if(process!=null&&process.isAlive()){ try{process.destroyForcibly();}catch(Exception ignore){} }
            runningProcesses.remove(taskId);
            cleanupTaskLock(taskId); // 락 해제 공통 함수 호출
        }
    }

    /** 락 해제 공통 함수 */
    private void cleanupTaskLock(String taskId) {
        activeLock.set(false);
        currentRunner=null;
        currentTaskId=null;
        log.info("[{}] 🔓 Lock 해제",taskId);
    }


    /** ✅ 취소 */
    public void cancelTask(String taskId,String requester){
        if(!Objects.equals(taskId,currentTaskId))return;
        if(!Objects.equals(requester,currentRunner))return;
        Process p=runningProcesses.get(taskId);
        if(p!=null&&p.isAlive())p.destroyForcibly();
        taskStatusService.cancel(taskId);
        broadcastStatus(Map.of("status","CANCELLED"));
        cleanupTaskLock(taskId);
    }

    private int safeInt(String s){ try{return Integer.parseInt(s.trim());}catch(Exception e){return 0;} }
    private double safeDouble(String s){ try{return Double.parseDouble(s.trim());}catch(Exception e){return 0.0;} }

    public boolean isLocked(){return activeLock.get();}
    public String getCurrentTaskId(){return currentTaskId;}
    public String getCurrentRunner(){return currentRunner;}
}