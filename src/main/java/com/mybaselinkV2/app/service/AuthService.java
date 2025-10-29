package com.mybaselinkV2.app.service;

import java.time.Instant;
import java.util.Optional;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.mybaselinkV2.app.entity.JwtTokenEntity;
import com.mybaselinkV2.app.repository.JwtTokenRepository;

@Service
public class AuthService {

    private final JwtTokenRepository tokenRepository;

    public AuthService(JwtTokenRepository tokenRepository) {
        this.tokenRepository = tokenRepository;
    }

    @Transactional
    public void login(UserDetails userDetails, String token, Instant expiresAt) {
        JwtTokenEntity entity = new JwtTokenEntity();
        entity.setUsername(userDetails.getUsername());
        entity.setToken(token);
        entity.setCreatedAt(Instant.now());
        entity.setExpiresAt(expiresAt);
        entity.setRevoked(false);
        tokenRepository.save(entity);
    }

    @Transactional
    public void logout(String token) {
        Optional<JwtTokenEntity> opt = tokenRepository.findByToken(token);
        opt.ifPresent(t -> {
            t.setRevoked(true);
            tokenRepository.save(t);
        });
    }

    @Transactional
    public void refreshToken(String oldToken, String newToken, Instant expiresAt) {
        Optional<JwtTokenEntity> optOld = tokenRepository.findByToken(oldToken);

        String username = optOld
                .map(JwtTokenEntity::getUsername)
                .orElseThrow(() -> new RuntimeException("기존 토큰 정보 없음!"));

        optOld.ifPresent(t -> {
            t.setRevoked(true);
            tokenRepository.save(t);
        });

        JwtTokenEntity newEntity = new JwtTokenEntity();
        newEntity.setToken(newToken);
        newEntity.setUsername(username);
        newEntity.setCreatedAt(Instant.now());
        newEntity.setExpiresAt(expiresAt);
        newEntity.setRevoked(false);

        tokenRepository.save(newEntity);
    }

    public boolean isTokenValid(String token) {
        Optional<JwtTokenEntity> opt = tokenRepository.findByToken(token);
        return opt.isPresent() && !opt.get().isRevoked() && opt.get().getExpiresAt().isAfter(Instant.now());
    }

    public Optional<JwtTokenEntity> findByToken(String token) {
        return tokenRepository.findByToken(token);
    }
}
