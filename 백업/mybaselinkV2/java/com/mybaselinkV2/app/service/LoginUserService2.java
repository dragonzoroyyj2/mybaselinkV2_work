package com.mybaselinkV2.app.service;

import org.springframework.stereotype.Service;

import com.mybaselinkV2.app.entity.LoginUserEntity;
import com.mybaselinkV2.app.respsitory.LoginUserRepository;

/**
 * 🔑 LoginUserService - 로그인 전용 사용자 서비스
 *
 * 역할:
 * 1. DB에서 사용자 조회
 * 2. 로그인 전용 로직 관리
 */
@Service
public class LoginUserService2 {

    private final LoginUserRepository userRepository;

    public LoginUserService2(LoginUserRepository userRepository) {
        this.userRepository = userRepository;
    }

    /**
     * 🔹 username 기반 사용자 조회
     *
     * @param username 로그인 ID
     * @return LoginUserEntity 또는 null
     */
    public LoginUserEntity findByUsername(String username) {
        return userRepository.findByUsername(username);
    }
}
