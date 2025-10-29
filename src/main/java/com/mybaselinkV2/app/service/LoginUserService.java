package com.mybaselinkV2.app.service;

import java.util.Map;
import java.util.Optional;

import org.springframework.stereotype.Service;

import com.mybaselinkV2.app.entity.LoginUserEntity;
import com.mybaselinkV2.app.entity.UserEntity;
import com.mybaselinkV2.app.repository.LoginUserRepository;
import com.mybaselinkV2.app.repository.UserRepository;

/**
 * 👤 LoginUserService
 * - 로그인/사용자 정보 조회 전용 서비스
 */
@Service
public class LoginUserService {

    private final LoginUserRepository loginUserRepository;
    private final UserRepository userRepository;

    public LoginUserService(LoginUserRepository loginUserRepository,
                            UserRepository userRepository) {
        this.loginUserRepository = loginUserRepository;
        this.userRepository = userRepository;
    }

    /**
     * 사용자 프로필 조회
     * - LoginUserEntity 또는 UserEntity 기반
     */
    public Optional<Map<String, Object>> findUserProfile(String username) {
        Optional<LoginUserEntity> loginUserOpt = loginUserRepository.findByUsername(username);
        if (loginUserOpt.isPresent()) {
            LoginUserEntity u = loginUserOpt.get();
            return Optional.of(Map.of(
                    "username", u.getUsername(),
                    "role", u.getRole()
            ));
        }

        Optional<UserEntity> userOpt = userRepository.findByUsername(username);
        return userOpt.map(u -> Map.of(
                "username", u.getUsername(),
                "fullName", u.getFullName(),
                "email", u.getEmail(),
                "role", u.getRole()
        ));
    }
}
