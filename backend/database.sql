DROP TABLE IF EXISTS docker_containers CASCADE;
DROP TABLE IF EXISTS student_projects CASCADE;
DROP TABLE IF EXISTS course_user CASCADE;
DROP TABLE IF EXISTS labs CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS passwords CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP INDEX IF EXISTS idx_docker_containers_project_id;
DROP INDEX IF EXISTS idx_docker_containers_status;
DROP INDEX IF EXISTS idx_docker_containers_project_type;
DROP INDEX IF EXISTS idx_student_projects_user_id;
DROP INDEX IF EXISTS idx_student_projects_lab_id;
DROP INDEX IF EXISTS idx_labs_course_id;
DROP INDEX IF EXISTS idx_course_user_user_id;

-- Роли
CREATE TABLE IF NOT EXISTS roles (
    access_id     SERIAL PRIMARY KEY,
    access_rights VARCHAR(45) NOT NULL UNIQUE
);

-- Логины и пароли
CREATE TABLE IF NOT EXISTS passwords (
    login_id SERIAL PRIMARY KEY,
    login    VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(50)  NOT NULL
);

-- Пользователи
CREATE TABLE IF NOT EXISTS users (
    user_id   SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    access_id INTEGER NOT NULL,
    login_id  INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'approved',
    is_approved BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    rejected_at TIMESTAMP,
    FOREIGN KEY (access_id) REFERENCES roles(access_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (login_id) REFERENCES passwords(login_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Курсы
CREATE TABLE IF NOT EXISTS courses (
    course_id  SERIAL PRIMARY KEY,
    name       VARCHAR(100)  NOT NULL UNIQUE,
    teacher    VARCHAR(100) NOT NULL,
    teacher_id INTEGER,
    FOREIGN KEY (teacher_id) REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- Лабораторные работы
CREATE TABLE IF NOT EXISTS labs (
    lab_id        SERIAL PRIMARY KEY,
    name          VARCHAR(50) NOT NULL UNIQUE,
    course_id     INTEGER     NOT NULL,
    task          TEXT,
    task_file     BYTEA       NOT NULL DEFAULT '\x',
    task_filename VARCHAR(255),
    start_date    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date      TIMESTAMP   NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Запись студентов на курсы
CREATE TABLE IF NOT EXISTS course_user (
    course_id INTEGER NOT NULL,
    user_id   INTEGER NOT NULL,
    PRIMARY KEY (course_id, user_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Работы студентов
CREATE TABLE IF NOT EXISTS student_projects (
    project_id      SERIAL PRIMARY KEY,
    user_id         INTEGER   NOT NULL,
    lab_id          INTEGER   NOT NULL,
    github_link     TEXT      NOT NULL,
    submission_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    grade           INTEGER,
    teacher_comment TEXT,
    build_info      TEXT,
    grade_date      TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (lab_id) REFERENCES labs(lab_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CHECK (grade IS NULL OR (grade >= 2 AND grade <= 5))
);

-- Docker контейнеры
CREATE TABLE IF NOT EXISTS docker_containers (
    container_id VARCHAR(64)  PRIMARY KEY,
    project_id   INTEGER      NOT NULL,
    port         INTEGER,
    image_name   VARCHAR(255) NOT NULL,
    started_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    stopped_at   TIMESTAMP,
    status       VARCHAR(20)  DEFAULT 'running',
    project_type VARCHAR(20)  DEFAULT 'console',
    main_file    VARCHAR(255),
    CHECK (status IN ('running', 'stopped', 'removed')),
    CHECK (project_type IN ('console', 'gui')),
    FOREIGN KEY (project_id) REFERENCES student_projects(project_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_docker_containers_project_id   ON docker_containers(project_id);
CREATE INDEX IF NOT EXISTS idx_docker_containers_status       ON docker_containers(status);
CREATE INDEX IF NOT EXISTS idx_docker_containers_project_type ON docker_containers(project_type);
CREATE INDEX IF NOT EXISTS idx_student_projects_user_id       ON student_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_student_projects_lab_id        ON student_projects(lab_id);
CREATE INDEX IF NOT EXISTS idx_labs_course_id                 ON labs(course_id);
CREATE INDEX IF NOT EXISTS idx_course_user_user_id            ON course_user(user_id);

INSERT INTO roles (access_rights) VALUES
    ('admin'),
    ('teacher'),
    ('student')
ON CONFLICT (access_rights) DO NOTHING;

INSERT INTO passwords (login, password) VALUES
    ('admin@vstand.ru',      'admin123')
ON CONFLICT (login) DO NOTHING;

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Администратор',
       (SELECT access_id FROM roles WHERE access_rights = 'admin'),
       (SELECT login_id FROM passwords WHERE login = 'admin@vstand.ru')
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'admin@vstand.ru')
);