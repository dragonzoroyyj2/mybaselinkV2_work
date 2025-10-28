package com.mybaselinkV2.app.service;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.mybaselinkV2.app.entity.JwtTokenEntity;
import com.mybaselinkV2.app.respsitory.JwtTokenRepository;

/**
 * 🔑 AuthService
 *
 * - JWT 기반 인증/인가 관련 로직 처리
 * - 리프레시 토큰의 저장, 무효화, 유효성 검증
 */
@Service
public class AuthService2 {

    private final JwtTokenRepository jwtTokenRepository;

    public AuthService2(JwtTokenRepository jwtTokenRepository) {
        this.jwtTokenRepository = jwtTokenRepository;
    }

    /**
     * ✅ 로그인: 리프레시 토큰 저장 및 기존 토큰 무효화
     */
    @Transactional
    public void login(UserDetails userDetails, String refreshToken, Instant expiresAt) {
        // 기존에 발급된 리프레시 토큰이 있다면 모두 무효화
        List<JwtTokenEntity> activeTokens = jwtTokenRepository.findByUsernameAndRevokedFalse(userDetails.getUsername());
        activeTokens.forEach(token -> {
            token.setRevoked(true);
            jwtTokenRepository.save(token);
        });

        // 새로운 리프레시 토큰 저장
        JwtTokenEntity newToken = JwtTokenEntity.builder()
                .username(userDetails.getUsername())
                .token(refreshToken)
                .expiresAt(expiresAt)
                .revoked(false)
                .build();
        jwtTokenRepository.save(newToken);
    }

    /**
     * ✅ 로그아웃: 특정 리프레시 토큰 무효화
     */
    @Transactional
    public void logout(String token) {
        jwtTokenRepository.findByToken(token).ifPresent(t -> {
            t.setRevoked(true);
            jwtTokenRepository.save(t);
        });
    }

    /**
     * ✅ 토큰 유효성 검증 (DB 조회)
     */
    public boolean isTokenValid(String token) {
        Optional<JwtTokenEntity> entity = jwtTokenRepository.findByToken(token);
        return entity.isPresent() && !entity.get().isRevoked() && entity.get().getExpiresAt().isAfter(Instant.now());
    }

    /**
     * ✅ 토큰 조회
     */
    public Optional<JwtTokenEntity> findByToken(String token) {
        return jwtTokenRepository.findByToken(token);
    }

    /**
     * ✅ 만료된 토큰 자동 정리
     */
    @Transactional
    public long cleanExpiredTokens() {
        return jwtTokenRepository.deleteAllByExpiresAtBefore(Instant.now());
    }
}
