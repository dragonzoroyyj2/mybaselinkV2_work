package com.mybaselinkV2.app.service;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import com.mybaselinkV2.app.entity.JwtTokenEntity;

/**
 * 🔑 AuthService (임시 메모리 구현)
 */
@Service
public class AuthService {

    private Map<String, Instant> validRefreshTokens = new HashMap<>();

    public void login(UserDetails userDetails, String refreshToken, Instant expiresAt) {
        validRefreshTokens.put(refreshToken, expiresAt);
    }

    public void logout(String token) {
        validRefreshTokens.remove(token);
    }

    public boolean isTokenValid(String token) {
        Instant expiresAt = validRefreshTokens.get(token);
        return expiresAt != null && expiresAt.isAfter(Instant.now());
    }

    public Optional<JwtTokenEntity> findByToken(String token) {
        if (isTokenValid(token)) {
            // 임시 엔티티 반환 로직은 생략
        }
        return Optional.empty();
    }
    
    public long cleanExpiredTokens() {
        return 0; // DB 연동이 없으므로 더미 값 반환
    }
}
