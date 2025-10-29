package com.mybaselinkV2.app.repository;

import com.mybaselinkV2.app.entity.LoginUserEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * 🔑 LoginUserRepository
 * - 로그인용 사용자 조회
 * - Spring Security 인증 및 프로필 조회 전용
 */
@Repository
public interface LoginUserRepository extends JpaRepository<LoginUserEntity, Long> {

    /**
     * username 기반 사용자 조회
     */
    Optional<LoginUserEntity> findByUsername(String username);
}
