package com.mybaselinkV2.app.jwt;

import com.mybaselinkV2.app.entity.JwtTokenEntity;
import com.mybaselinkV2.app.respsitory.JwtTokenRepository;
import com.mybaselinkV2.app.entity.LoginUserEntity;
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.User;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

@Component
public class JwtTokenProvider2 {

    private final JwtTokenRepository jwtTokenRepository;

    @Value("${jwt.secret}")
    private String secretKey;

    @Value("${jwt.access-expiration-millis}")
    public long accessExpirationMillis;

    @Value("${jwt.refresh-expiration-millis}")
    public long refreshExpirationMillis;

    public JwtTokenProvider2(JwtTokenRepository jwtTokenRepository) {
        this.jwtTokenRepository = jwtTokenRepository;
    }

    public String generateAccessToken(LoginUserEntity user, Collection<? extends GrantedAuthority> roles) {
        return createToken(user, roles, accessExpirationMillis);
    }

    public String generateRefreshToken(LoginUserEntity user, Collection<? extends GrantedAuthority> roles) {
        return createToken(user, roles, refreshExpirationMillis);
    }

    private String createToken(LoginUserEntity user, Collection<? extends GrantedAuthority> roles, long expirationMillis) {
        Instant now = Instant.now();
        Instant expiresAt = now.plusMillis(expirationMillis);

        List<String> roleList = roles.stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toList());

        return Jwts.builder()
                .setSubject(user.getUsername())
                .claim("roles", roleList)
                .claim("name", user.getName())
                .claim("email", user.getEmail())
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(expiresAt))
                .signWith(Keys.hmacShaKeyFor(secretKey.getBytes()))
                .compact();
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parserBuilder()
                    .setSigningKey(secretKey.getBytes())
                    .build()
                    .parseClaimsJws(token);
            return true;
        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    public String getUsername(String token) {
        return getClaims(token).getSubject();
    }

    public List<String> getRoles(String token) {
        Object roles = getClaims(token).get("roles");
        if (roles instanceof List<?>) {
            return ((List<?>) roles).stream()
                    .map(Object::toString)
                    .collect(Collectors.toList());
        }
        return Collections.emptyList();
    }

    public String getName(String token) {
        Claims claims = getClaims(token);
        return claims != null ? claims.get("name", String.class) : null;
    }

    public String getEmail(String token) {
        Claims claims = getClaims(token);
        return claims != null ? claims.get("email", String.class) : null;
    }

    private Claims getClaims(String token) {
        try {
            return Jwts.parserBuilder()
                    .setSigningKey(secretKey.getBytes())
                    .build()
                    .parseClaimsJws(token)
                    .getBody();
        } catch (JwtException e) {
            return null;
        }
    }

    public Date extractExpiration(String token) {
        return getClaims(token).getExpiration();
    }

    public long getRemainingMillis(String token) {
        Date expiration = extractExpiration(token);
        return expiration.getTime() - System.currentTimeMillis();
    }

    public Authentication getAuthentication(String token) {
        List<GrantedAuthority> authorities = getRoles(token).stream()
                .map(role -> (GrantedAuthority) () -> role)
                .collect(Collectors.toList());

        User principal = new User(getUsername(token), "", authorities);
        return new UsernamePasswordAuthenticationToken(principal, token, authorities);
    }

    public String resolveAccessToken(HttpServletRequest request) {
        return resolveTokenFromCookie(request, "access_token");
    }

    public String resolveRefreshToken(HttpServletRequest request) {
        return resolveTokenFromCookie(request, "refresh_token");
    }

    private String resolveTokenFromCookie(HttpServletRequest request, String cookieName) {
        Cookie[] cookies = request.getCookies();
        if (cookies != null) {
            for (Cookie cookie : cookies) {
                if (cookieName.equals(cookie.getName())) {
                    return cookie.getValue();
                }
            }
        }
        return null;
    }

    public Instant getRefreshExpiresAt() {
        return Instant.now().plusMillis(refreshExpirationMillis);
    }

    public long getAccessExpirationMillis() {
        return accessExpirationMillis;
    }

    public long getRefreshExpirationMillis() {
        return refreshExpirationMillis;
    }
}
