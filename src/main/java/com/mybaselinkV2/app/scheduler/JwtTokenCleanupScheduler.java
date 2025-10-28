package com.mybaselinkV2.app.scheduler;

import com.mybaselinkV2.app.service.AuthService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class JwtTokenCleanupScheduler {

    private static final Logger logger = LoggerFactory.getLogger(JwtTokenCleanupScheduler.class);
    private final AuthService authService;

    public JwtTokenCleanupScheduler(AuthService authService) {
        this.authService = authService;
    }

    @Scheduled(cron = "0 0 3 * * ?")
    public void removeExpiredTokens() {
        long deletedCount = authService.cleanExpiredTokens();
        logger.info("⏰ JwtTokenCleanupScheduler - 만료 토큰 삭제 완료. 삭제된 토큰 수: {}", deletedCount);
    }
}
