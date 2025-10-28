package com.mybaselinkV2.app.respsitory;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.mybaselinkV2.app.entity.UserEntity;

/**
 * 🔑 UserRepository - 사용자 조회/관리용 Repository
 */
@Repository
public interface UserRepository extends JpaRepository<UserEntity, Long> {

    /**
     * username 으로 사용자 조회 (로그인에 사용)
     */
    UserEntity findByUsername(String username);
}
