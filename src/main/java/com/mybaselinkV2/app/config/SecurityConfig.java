package com.mybaselinkV2.app.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.AuthenticationEntryPoint;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

import com.mybaselinkV2.app.jwt.CustomLogoutHandler;
import com.mybaselinkV2.app.jwt.JwtAuthenticationFilter;
import com.mybaselinkV2.app.jwt.JwtTokenProvider;
import com.mybaselinkV2.app.service.AuthService;
import com.mybaselinkV2.app.service.CustomUserDetailsService;

@Configuration
@EnableAsync
@EnableWebSecurity
public class SecurityConfig {

    private final CustomUserDetailsService userDetailsService;
    private final CustomLogoutHandler customLogoutHandler;
    private final AuthService authService;

    public SecurityConfig(CustomUserDetailsService userDetailsService,
                          CustomLogoutHandler customLogoutHandler,
                          AuthService authService) {
        this.userDetailsService = userDetailsService;
        this.customLogoutHandler = customLogoutHandler;
        this.authService = authService;
    }

    @Bean
    public JwtAuthenticationFilter jwtAuthenticationFilter(JwtTokenProvider jwtTokenProvider) {
        return new JwtAuthenticationFilter(jwtTokenProvider, userDetailsService, authService);
    }

    /**
     * @Order(1) : 웹 페이지 관련 요청을 먼저 처리하는 필터 체인.
     * 모든 사용자가 로그인 페이지와 정적 리소스에 접근할 수 있도록 허용하고,
     * 폼 로그인을 활성화합니다.
     */
    @Bean
    @Order(1)
    public SecurityFilterChain loginFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .securityMatcher("/", "/login", "/error", "/pages/**", 
                             "/common/**", "/css/**", "/js/**", "/images/**", "/favicon/**",
                             "/favicon.ico", "/apple-icon-*.png", "/android-icon-*.png", "/manifest.json")
            .authorizeHttpRequests(auth -> auth
                .anyRequest().permitAll()
            )
            .formLogin(form -> form
                .loginPage("/login")
                .permitAll()
            );
        
        return http.build();
    }
    
    /**
     * @Order(2) : API 요청을 처리하는 필터 체인.
     * JWT 토큰을 사용하여 인증하며, Stateless 세션 정책을 적용합니다.
     */
    @Bean
    @Order(2)
    public SecurityFilterChain apiFilterChain(HttpSecurity http, JwtAuthenticationFilter jwtAuthenticationFilter) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/auth/**").permitAll()
                .requestMatchers("/api/stock/**", "/api/p01a05/**").permitAll()
                .requestMatchers("/api/krx/**", "/chart/**", "/api/profile").permitAll()
                .anyRequest().authenticated()
            )
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint(unauthorizedEntryPoint())
            )
            .logout(logout -> logout
                .logoutUrl("/auth/logout")
                .addLogoutHandler(customLogoutHandler)
                .logoutSuccessHandler((req, res, auth) -> {
                    res.setStatus(200);
                    res.setContentType("application/json;charset=UTF-8");
                    res.getWriter().write("{\"status\":\"로그아웃 성공\"}");
                })
            )
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS));

        http.addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }


    public DaoAuthenticationProvider authenticationProvider() {
        DaoAuthenticationProvider provider = new DaoAuthenticationProvider();
        provider.setUserDetailsService(userDetailsService);
        provider.setPasswordEncoder(passwordEncoder());
        return provider;
    }
    
    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
    
    @Bean
    public AuthenticationEntryPoint unauthorizedEntryPoint() {
        return (request, response, authException) -> {
            response.setStatus(401);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"error\":\"인증이 필요합니다.\"}");
        };
    }
}
