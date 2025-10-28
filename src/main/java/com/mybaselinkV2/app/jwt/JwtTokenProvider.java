package com.mybaselinkV2.app.jwt;

import com.mybaselinkV2.app.entity.LoginUserEntity;
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.SignatureException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.User;
import org.springframework.stereotype.Component;

import java.security.Key;
import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

@Component
public class JwtTokenProvider {

    private static final Logger log = LoggerFactory.getLogger(JwtTokenProvider.class);

    private final Key key;
    private final long accessExpirationMillis;
    private final long refreshExpirationMillis;

    public JwtTokenProvider(@Value("${jwt.secret.key}") String secretKey,
                            @Value("${jwt.access-expiration-millis}") long accessExpirationMillis,
                            @Value("${jwt.refresh-expiration-millis}") long refreshExpirationMillis) {
        this.key = Keys.hmacShaKeyFor(secretKey.getBytes());
        this.accessExpirationMillis = accessExpirationMillis;
        this.refreshExpirationMillis = refreshExpirationMillis;
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
                .signWith(this.key, SignatureAlgorithm.HS256)
                .compact();
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token);
            return true;
        } catch (SignatureException e) {
            log.info("Invalid JWT signature.", e);
        } catch (MalformedJwtException e) {
            log.info("Invalid JWT token.", e);
        } catch (ExpiredJwtException e) {
            log.info("Expired JWT token.", e);
        } catch (UnsupportedJwtException e) {
            log.info("Unsupported JWT token.", e);
        } catch (IllegalArgumentException e) {
            log.info("JWT claims string is empty.", e);
        }
        return false;
    }

    public String getUsername(String token) {
        Claims claims = getClaims(token);
        return claims != null ? claims.getSubject() : null;
    }

    public List<String> getRoles(String token) {
        Claims claims = getClaims(token);
        if (claims != null) {
            Object roles = claims.get("roles");
            if (roles instanceof List<?>) {
                return ((List<?>) roles).stream().map(Object::toString).collect(Collectors.toList());
            }
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
            return Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token).getBody();
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
