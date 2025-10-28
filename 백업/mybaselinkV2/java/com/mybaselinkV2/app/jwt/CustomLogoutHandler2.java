package com.mybaselinkV2.app.jwt;

import java.util.Arrays;

import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.logout.LogoutHandler;
import org.springframework.stereotype.Component;

import com.mybaselinkV2.app.respsitory.JwtTokenRepository;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@Component
public class CustomLogoutHandler2 implements LogoutHandler {

    private final JwtTokenRepository jwtTokenRepository;

    public CustomLogoutHandler2(JwtTokenRepository jwtTokenRepository) {
        this.jwtTokenRepository = jwtTokenRepository;
    }

    @Override
    public void logout(HttpServletRequest request,
                       HttpServletResponse response,
                       Authentication authentication) {

        // 1. 요청 쿠키에서 refresh_token 추출
        String refreshToken = extractTokenFromCookie(request, "refresh_token");

        // 2. DB에서 리프레시 토큰 무효화 처리
        if (refreshToken != null) {
            jwtTokenRepository.findByToken(refreshToken)
                    .ifPresent(tokenEntity -> {
                        tokenEntity.setRevoked(true);
                        jwtTokenRepository.save(tokenEntity);
                    });
        }

        // 3. 클라이언트의 access_token 및 refresh_token 쿠키 삭제
        deleteCookie(response, "access_token", "/");
        deleteCookie(response, "refresh_token", "/auth/refresh");
    }

    private String extractTokenFromCookie(HttpServletRequest request, String cookieName) {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) {
            return null;
        }
        return Arrays.stream(cookies)
                .filter(cookie -> cookieName.equals(cookie.getName()))
                .map(Cookie::getValue)
                .findFirst()
                .orElse(null);
    }

    private void deleteCookie(HttpServletResponse response, String name, String path) {
        Cookie cookie = new Cookie(name, null);
        cookie.setMaxAge(0);
        cookie.setHttpOnly(true);
        cookie.setSecure(true);
        cookie.setPath(path);
        response.addCookie(cookie);
    }
}
