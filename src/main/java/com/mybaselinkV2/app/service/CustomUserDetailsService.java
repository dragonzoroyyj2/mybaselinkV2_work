package com.mybaselinkV2.app.service;

import java.util.Collections;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import com.mybaselinkV2.app.entity.LoginUserEntity;
import com.mybaselinkV2.app.repository.LoginUserRepository;

/**
 * 🔑 CustomUserDetailsService
 * - Spring Security 인증용
 * - DB에서 사용자 조회
 */
@Service
public class CustomUserDetailsService implements UserDetailsService {

    private final LoginUserRepository loginUserRepository;

    public CustomUserDetailsService(LoginUserRepository loginUserRepository) {
        this.loginUserRepository = loginUserRepository;
    }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        LoginUserEntity user = loginUserRepository.findByUsername(username)
                .orElseThrow(() -> new UsernameNotFoundException("사용자를 찾을 수 없습니다: " + username));

        // 권한 세팅
        GrantedAuthority authority = new SimpleGrantedAuthority(user.getRole());

        return org.springframework.security.core.userdetails.User.builder()
                .username(user.getUsername())
                .password(user.getPassword())
                .authorities(Collections.singletonList(authority))
                .accountExpired(false)
                .accountLocked(false)
                .credentialsExpired(false)
                .disabled(false)
                .build();
    }
}
