package com.mybaselinkV2.app.service;

import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Collections;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    // 임시 인코더
    private final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
    
    // (기존 userService 필드 제거 또는 주석 처리)
    // private final LoginUserService userService;

    // (기존 생성자 제거 또는 주석 처리)
    // public CustomUserDetailsService(LoginUserService userService) {
    //     this.userService = userService;
    // }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        // DB 대신 임시로 메모리에 유저 정보 생성
        if ("test".equals(username)) {
            // 패스워드는 임시로 인코딩된 문자열을 사용
            // "1234"를 BCrypt로 인코딩한 값
            String encodedPassword = encoder.encode("1234"); 
            
            return User.withUsername("test")
                    .password(encodedPassword)
                    .authorities(Collections.singleton(() -> "ROLE_ADMIN"))
                    .build();
        }
        throw new UsernameNotFoundException("사용자를 찾을 수 없습니다: " + username);
    }
}
