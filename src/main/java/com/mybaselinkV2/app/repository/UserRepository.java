package com.mybaselinkV2.app.repository;

import com.mybaselinkV2.app.entity.UserEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * ✅ UserRepository
 * - 프로필 및 권한 조회 전용
 * - 로그인과 무관하게 사용자 정보 확인용
 */
@Repository
public interface UserRepository extends JpaRepository<UserEntity, Long> {

    Optional<UserEntity> findByUsername(String username);

    Optional<UserEntity> findByEmail(String email);
}
