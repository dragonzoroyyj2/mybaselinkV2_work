package com.mybaselinkV2.app.controller;

import com.mybaselinkV2.app.jwt.JwtTokenProvider;
import com.mybaselinkV2.app.entity.LoginUserEntity;
import com.mybaselinkV2.app.repository.LoginUserRepository;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final LoginUserRepository loginUserRepository;
    private final JwtTokenProvider jwtTokenProvider;
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    public AuthController(LoginUserRepository loginUserRepository,
                          JwtTokenProvider jwtTokenProvider) {
        this.loginUserRepository = loginUserRepository;
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @PostMapping("/login")
    public String login(@RequestParam String username,
                        @RequestParam String password,
                        HttpServletResponse response) {

        LoginUserEntity user = loginUserRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("사용자 없음"));

        if (!passwordEncoder.matches(password, user.getPassword())) {
            throw new RuntimeException("비밀번호 불일치");
        }

        String token = jwtTokenProvider.generateAccessToken(username, null);

        Cookie cookie = new Cookie("jwt", token);
        cookie.setHttpOnly(true);
        cookie.setPath("/");
        cookie.setMaxAge((int) (jwtTokenProvider.getAccessExpirationMillis() / 1000));
        response.addCookie(cookie);

        return "로그인 성공";
    }

    @PostMapping("/logout")
    public String logout(HttpServletResponse response) {
        Cookie cookie = new Cookie("jwt", "");
        cookie.setHttpOnly(true);
        cookie.setPath("/");
        cookie.setMaxAge(0);
        response.addCookie(cookie);

        return "로그아웃 성공";
    }
}
