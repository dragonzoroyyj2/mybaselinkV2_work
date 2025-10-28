package com.mybaselinkV2.app.controller;

import java.util.HashMap;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseCookie;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.mybaselinkV2.app.entity.LoginUserEntity;
import com.mybaselinkV2.app.jwt.JwtTokenProvider;
import com.mybaselinkV2.app.service.AuthService;
import com.mybaselinkV2.app.service.CustomUserDetailsService;
import com.mybaselinkV2.app.service.LoginUserService;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final AuthenticationManager authenticationManager;
    private final JwtTokenProvider jwtTokenProvider;
    private final AuthService authService;
    private final CustomUserDetailsService userDetailsService;
    private final LoginUserService loginUserService;

    public AuthController(AuthenticationManager authenticationManager,
                          JwtTokenProvider jwtTokenProvider,
                          AuthService authService,
                          CustomUserDetailsService userDetailsService,
                          LoginUserService loginUserService) {
        this.authenticationManager = authenticationManager;
        this.jwtTokenProvider = jwtTokenProvider;
        this.authService = authService;
        this.userDetailsService = userDetailsService;
        this.loginUserService = loginUserService;
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody Map<String, String> request, HttpServletResponse response) {
        String username = request.get("username");
        String password = request.get("password");

        try {
            Authentication auth = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(username, password)
            );

            UserDetails userDetails = (UserDetails) auth.getPrincipal();
            LoginUserEntity user = loginUserService.findByUsername(username);

            String accessToken = jwtTokenProvider.generateAccessToken(user, userDetails.getAuthorities());
            String refreshToken = jwtTokenProvider.generateRefreshToken(user, userDetails.getAuthorities());

            authService.login(userDetails, refreshToken, jwtTokenProvider.getRefreshExpiresAt());

            ResponseCookie accessCookie = ResponseCookie.from("access_token", accessToken)
                    .httpOnly(true)
                    .secure(true)
                    .path("/")
                    .maxAge(jwtTokenProvider.getAccessExpirationMillis() / 1000)
                    .sameSite("Strict")
                    .build();
            response.addHeader("Set-Cookie", accessCookie.toString());

            ResponseCookie refreshCookie = ResponseCookie.from("refresh_token", refreshToken)
                    .httpOnly(true)
                    .secure(true)
                    .path("/auth/refresh")
                    .maxAge(jwtTokenProvider.getRefreshExpirationMillis() / 1000)
                    .sameSite("Strict")
                    .build();
            response.addHeader("Set-Cookie", refreshCookie.toString());

            Map<String, Object> result = new HashMap<>();
            result.put("message", "로그인 성공");
            result.put("username", username);
            result.put("name", user.getName());
            result.put("email", user.getEmail());
            result.put("role", userDetails.getAuthorities());
            return ResponseEntity.ok(result);

        } catch (BadCredentialsException e) {
            Map<String, Object> error = new HashMap<>();
            error.put("error", "아이디 또는 비밀번호가 올바르지 않습니다.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(error);
        }
    }

    @PostMapping("/logout")
    public ResponseEntity<Map<String, Object>> logout() {
        Map<String, Object> result = new HashMap<>();
        result.put("message", "로그아웃 요청이 처리되었습니다.");
        return ResponseEntity.ok(result);
    }

    @PostMapping("/refresh")
    public ResponseEntity<Map<String, Object>> refreshSession(HttpServletRequest request, HttpServletResponse response) {
        String refreshToken = jwtTokenProvider.resolveRefreshToken(request);
        Map<String, Object> result = new HashMap<>();

        if (refreshToken == null || !authService.isTokenValid(refreshToken)) {
            result.put("error", "유효한 리프레시 토큰이 없습니다.");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(result);
        }

        String username = jwtTokenProvider.getUsername(refreshToken);
        UserDetails userDetails = userDetailsService.loadUserByUsername(username);
        LoginUserEntity user = loginUserService.findByUsername(username);

        String newAccessToken = jwtTokenProvider.generateAccessToken(
                user,
                userDetails.getAuthorities()
        );

        ResponseCookie newAccessCookie = ResponseCookie.from("access_token", newAccessToken)
                .httpOnly(true)
                .secure(true)
                .path("/")
                .maxAge(jwtTokenProvider.getAccessExpirationMillis() / 1000)
                .sameSite("Strict")
                .build();
        response.addHeader("Set-Cookie", newAccessCookie.toString());

        result.put("message", "세션 연장 완료");
        result.put("username", username);
        result.put("role", userDetails.getAuthorities());
        result.put("name", user.getName());
        result.put("email", user.getEmail());
        return ResponseEntity.ok(result);
    }

    @GetMapping("/validate")
    public ResponseEntity<Map<String, Object>> validateToken(HttpServletRequest request) {
        String token = jwtTokenProvider.resolveAccessToken(request);
        Map<String, Object> result = new HashMap<>();

        if (token != null && jwtTokenProvider.validateToken(token)) {
            result.put("valid", true);
            result.put("username", jwtTokenProvider.getUsername(token));
            result.put("roles", jwtTokenProvider.getRoles(token));
            result.put("name", jwtTokenProvider.getName(token));
            result.put("email", jwtTokenProvider.getEmail(token));
            result.put("remainingMillis", jwtTokenProvider.getRemainingMillis(token));
            return ResponseEntity.ok(result);
        } else {
            result.put("valid", false);
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(result);
        }
    }
}
