package com.mybaselinkV2.app.jwt;

import java.util.Arrays;

import org.springframework.security.core.Authentication;
import org.springframework.security.web.authentication.logout.LogoutHandler;
import org.springframework.stereotype.Component;

import com.mybaselinkV2.app.service.AuthService; 

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@Component
public class CustomLogoutHandler implements LogoutHandler {

    private final AuthService authService;

    public CustomLogoutHandler(AuthService authService) {
        this.authService = authService;
    }

    @Override
    public void logout(HttpServletRequest request,
                       HttpServletResponse response,
                       Authentication authentication) {

        String refreshToken = extractTokenFromCookie(request, "refresh_token");

        if (refreshToken != null) {
            authService.logout(refreshToken);
        }

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
