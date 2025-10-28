package com.mybaselinkV2.app.entity;

import jakarta.persistence.*;

/**
 * 🔒 LoginUserEntity (안정형 완전판)
 *
 * ✅ 로그인 사용자 정보 엔티티
 */
@Entity
@Table(name = "login_users")
public class LoginUserEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 50)
    private String username;

    @Column(nullable = false, length = 100)
    private String password;

    @Column(nullable = false, length = 20)
    private String role;
    
    // ✅ 추가: 이름 필드
    @Column(nullable = true, length = 50)
    private String name;
    
    // ✅ 추가: 이메일 필드
    @Column(nullable = true, length = 100)
    private String email;

    // ✅ 기본 생성자 (JPA 필수)
    public LoginUserEntity() {}

    // ✅ 전체 필드 생성자 (필요시 사용)
    public LoginUserEntity(Long id, String username, String password, String role, String name, String email) {
        this.id = id;
        this.username = username;
        this.password = password;
        this.role = role;
        this.name = name;
        this.email = email;
    }

    // ✅ Getter 및 Setter 메서드
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }

    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }

    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    
    // ✅ 추가: getName() 메서드
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    // ✅ 추가: getEmail() 메서드
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
