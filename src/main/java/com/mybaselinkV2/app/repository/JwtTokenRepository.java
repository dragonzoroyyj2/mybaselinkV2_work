package com.mybaselinkV2.app.repository;

import com.mybaselinkV2.app.entity.JwtTokenEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
public interface JwtTokenRepository extends JpaRepository<JwtTokenEntity, Long> {

    Optional<JwtTokenEntity> findByToken(String token);

    List<JwtTokenEntity> findByUsernameAndRevokedFalse(String username);

    long deleteAllByExpiresAtBefore(Instant now);
}
