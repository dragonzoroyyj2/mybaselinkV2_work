package com.mybaselinkV2.app.service;

import com.mybaselinkV2.app.entity.LoginUserEntity;
import org.springframework.stereotype.Service;

@Service
public class LoginUserService {

    // 기존의 LoginUserRepository 필드 제거 또는 주석 처리
    // private final LoginUserRepository userRepository;

    // 기존의 생성자 제거 또는 주석 처리
    // public LoginUserService(LoginUserRepository userRepository) {
    //     this.userRepository = userRepository;
    // }

    /**
     * 🔹 username 기반 사용자 조회 (임시 메모리 구현)
     *
     * @param username 로그인 ID
     * @return LoginUserEntity 또는 null
     */
    public LoginUserEntity findByUsername(String username) {
        if ("test".equals(username)) {
            LoginUserEntity user = new LoginUserEntity();
            user.setUsername("test");
            user.setName("테스트유저");
            user.setEmail("testuser@example.com");
            user.setPassword("$2a$10$wN9iL6b1y2a4q5r6s7t8u9v0w.1.x2y3.z4"); // BCrypt로 인코딩된 "1234"
            user.setRole("ROLE_ADMIN");
            return user;
        }
        return null;
    }
}
