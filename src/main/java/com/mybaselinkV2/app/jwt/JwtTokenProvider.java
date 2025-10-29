package com.mybaselinkV2.app.jwt;

import com.mybaselinkV2.app.entity.JwtTokenEntity;
import com.mybaselinkV2.app.repository.JwtTokenRepository;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.*;
import java.util.stream.Collectors;

@Component
public class JwtTokenProvider {

    private final JwtTokenRepository jwtTokenRepository;

    @Value("${application.security.jwt.secret-key}")
    private String secretKey;

    @Value("${application.security.jwt.expiration}")
    private long accessExpirationMillis;

    public JwtTokenProvider(JwtTokenRepository jwtTokenRepository) {
        this.jwtTokenRepository = jwtTokenRepository;
    }

    public long getAccessExpirationMillis() {
        return accessExpirationMillis;
    }

    public String generateAccessToken(String username, Collection<? extends GrantedAuthority> roles) {
        Instant now = Instant.now();
        Instant expiresAt = now.plusMillis(accessExpirationMillis);

        List<String> roleList = roles == null ? Collections.emptyList()
                : roles.stream().map(GrantedAuthority::getAuthority).collect(Collectors.toList());

        String token = Jwts.builder()
                .setSubject(username)
                .claim("roles", roleList)
                .setIssuedAt(Date.from(now))
                .setExpiration(Date.from(expiresAt))
                .signWith(Keys.hmacShaKeyFor(secretKey.getBytes()))
                .compact();

        JwtTokenEntity entity = new JwtTokenEntity(token, username, expiresAt);
        entity.setCreatedAt(now);
        jwtTokenRepository.save(entity);

        return token;
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parserBuilder()
                    .setSigningKey(secretKey.getBytes())
                    .build()
                    .parseClaimsJws(token);

            Optional<JwtTokenEntity> entity = jwtTokenRepository.findByToken(token);
            return entity.isPresent() && !entity.get().isRevoked()
                    && entity.get().getExpiresAt().isAfter(Instant.now());

        } catch (JwtException | IllegalArgumentException e) {
            return false;
        }
    }

    public String getUsername(String token) {
        return getClaims(token).getSubject();
    }

    public List<String> getRoles(String token) {
        Object roles = getClaims(token).get("roles");
        if (roles instanceof List<?> list) {
            return list.stream().map(Object::toString).collect(Collectors.toList());
        }
        return Collections.emptyList();
    }

    private Claims getClaims(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(secretKey.getBytes())
                .build()
                .parseClaimsJws(token)
                .getBody();
    }
}
