-- ==========================
-- 테이블 생성 (H2 초기화용)
-- ==========================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    full_name VARCHAR(100),
    email VARCHAR(100),
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- ==========================
-- 초기 데이터 삽입
-- ==========================
INSERT INTO roles (name) VALUES ('ADMIN');
INSERT INTO roles (name) VALUES ('USER');

INSERT INTO users (username, password, full_name, email, created_at)
VALUES ('admin', '$2a$10$btGX6c1k9Yeh2vvBfj0pTe8rwLzfxW7I1C5piOUQ9UVfgtbGXKgYG', '관리자', 'admin@example.com', CURRENT_TIMESTAMP);

INSERT INTO users (username, password, full_name, email, created_at)
VALUES ('test', '$2a$10$btGX6c1k9Yeh2vvBfj0pTe8rwLzfxW7I1C5piOUQ9UVfgtbGXKgYG', '일반 사용자', 'test@example.com', CURRENT_TIMESTAMP);

-- 매핑
INSERT INTO user_roles (user_id, role_id) VALUES (1, 1); -- admin → ADMIN
INSERT INTO user_roles (user_id, role_id) VALUES (2, 2); -- test → USER
