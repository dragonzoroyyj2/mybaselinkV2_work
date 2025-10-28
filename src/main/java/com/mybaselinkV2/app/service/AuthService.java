package com.mybaselinkV2.app.service;

import com.mybaselinkV2.app.entity.JwtTokenEntity;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

@Service
public class AuthService {

    private static final Logger log = LoggerFactory.getLogger(AuthService.class);

    private ConcurrentHashMap<String, Instant> validRefreshTokens = new ConcurrentHashMap<>();
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);

    @PostConstruct
    public void init() {
        scheduler.scheduleAtFixedRate(this::cleanExpiredTokens, 1, 1, TimeUnit.HOURS);
    }

    public void login(UserDetails userDetails, String refreshToken, Instant expiresAt) {
        validRefreshTokens.put(refreshToken, expiresAt);
        log.info("Refresh token stored for user: {}", userDetails.getUsername());
    }

    public void logout(String token) {
        if (validRefreshTokens.remove(token) != null) {
            log.info("Refresh token invalidated.");
        }
    }

    public boolean isTokenValid(String token) {
        Instant expiresAt = validRefreshTokens.get(token);
        return expiresAt != null && expiresAt.isAfter(Instant.now());
    }

    public Optional<JwtTokenEntity> findByToken(String token) {
        if (isTokenValid(token)) {
            JwtTokenEntity tempToken = new JwtTokenEntity();
            tempToken.setToken(token);
            tempToken.setExpiresAt(validRefreshTokens.get(token));
            return Optional.of(tempToken);
        }
        return Optional.empty();
    }
    
    public long cleanExpiredTokens() {
        long cleanedCount = validRefreshTokens.entrySet().stream()
                .filter(entry -> entry.getValue().isBefore(Instant.now()))
                .map(Map.Entry::getKey)
                .collect(Collectors.toList())
                .stream()
                .peek(validRefreshTokens::remove)
                .count();
        log.info("Cleaned {} expired refresh tokens from memory.", cleanedCount);
        return cleanedCount;
    }
}
