
-- mybaselink 스키마 설정
SET search_path TO mybaselink;

-- -------------------------------------------------------------
-- admin 사용자 추가
-- -------------------------------------------------------------
INSERT INTO users (username, password, full_name, email, role)
VALUES ('admin', '<BCrypt_해시값_여기에_붙여넣기>', 'Administrator', 'admin@example.com', 'ROLE_ADMIN');

-- -------------------------------------------------------------
-- test 사용자 추가
-- -------------------------------------------------------------
INSERT INTO users (username, password, full_name, email, role)
VALUES ('test', '<BCrypt_해시값_여기에_붙여넣기>', 'Test User', 'test@example.com', 'ROLE_USER');

-- roles 테이블에 ROLE_ADMIN, ROLE_USER 추가 (만약 없다면)
INSERT INTO roles (name) VALUES ('ROLE_ADMIN') ON CONFLICT (name) DO NOTHING;
INSERT INTO roles (name) VALUES ('ROLE_USER') ON CONFLICT (name) DO NOTHING;

-- -------------------------------------------------------------
-- user_roles 테이블에 사용자-권한 매핑 추가
-- -------------------------------------------------------------
INSERT INTO user_roles (user_id, role_id)
VALUES (
    (SELECT id FROM users WHERE username = 'admin'),
    (SELECT id FROM roles WHERE name = 'ROLE_ADMIN')
);

INSERT INTO user_roles (user_id, role_id)
VALUES (
    (SELECT id FROM users WHERE username = 'test'),
    (SELECT id FROM roles WHERE name = 'ROLE_USER')
);










-- mybaselink 스키마 설정
SET search_path TO mybaselink;

-- -------------------------------------------------------------
-- admin 사용자 추가
-- -------------------------------------------------------------
INSERT INTO users (username, password, full_name, email, role)
VALUES ('admin', '<BCrypt_해시값_여기에_붙여넣기>', 'Administrator', 'admin@example.com', 'ROLE_ADMIN');

-- -------------------------------------------------------------
-- test 사용자 추가
-- -------------------------------------------------------------
INSERT INTO users (username, password, full_name, email, role)
VALUES ('test', '<BCrypt_해시값_여기에_붙여넣기>', 'Test User', 'test@example.com', 'ROLE_USER');

-- roles 테이블에 ROLE_ADMIN, ROLE_USER 추가 (만약 없다면)
INSERT INTO roles (name) VALUES ('ROLE_ADMIN') ON CONFLICT (name) DO NOTHING;
INSERT INTO roles (name) VALUES ('ROLE_USER') ON CONFLICT (name) DO NOTHING;

-- -------------------------------------------------------------
-- user_roles 테이블에 사용자-권한 매핑 추가
-- -------------------------------------------------------------
INSERT INTO user_roles (user_id, role_id)
VALUES (
    (SELECT id FROM users WHERE username = 'admin'),
    (SELECT id FROM roles WHERE name = 'ROLE_ADMIN')
);

INSERT INTO user_roles (user_id, role_id)
VALUES (
    (SELECT id FROM users WHERE username = 'test'),
    (SELECT id FROM roles WHERE name = 'ROLE_USER')
);
