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
    name       VARCHAR(50)  NOT NULL UNIQUE,
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
    ('admin@vstand.ru',      'admin123'),
    ('samodelkin@vstand.ru', 'teach001'),
    ('zhilova@vstand.ru',    'teach002'),
    ('ivanov@vstand.ru',     'stud001'),
    ('petrov@vstand.ru',     'stud002'),
    ('sidorova@vstand.ru',   'stud003'),
    ('kozlova@vstand.ru',    'stud004'),
    ('novikov@vstand.ru',    'stud005')
ON CONFLICT (login) DO NOTHING;

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Администратор',
       (SELECT access_id FROM roles WHERE access_rights = 'admin'),
       (SELECT login_id FROM passwords WHERE login = 'admin@vstand.ru')
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'admin@vstand.ru')
);

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Самоделкин Павел Андреевич',
       (SELECT access_id FROM roles WHERE access_rights = 'teacher'),
       (SELECT login_id FROM passwords WHERE login = 'samodelkin@vstand.ru')
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'samodelkin@vstand.ru')
);

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Жилова Юлия Андреевна',
       (SELECT access_id FROM roles WHERE access_rights = 'teacher'),
       (SELECT login_id FROM passwords WHERE login = 'zhilova@vstand.ru')
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'zhilova@vstand.ru')
);

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Иванов Иван Иванович',
       (SELECT access_id FROM roles WHERE access_rights = 'student'),
       (SELECT login_id FROM passwords WHERE login = 'ivanov@vstand.ru')
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'ivanov@vstand.ru')
);

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Петров Пётр Петрович',
       (SELECT access_id FROM roles WHERE access_rights = 'student'),
       (SELECT login_id FROM passwords WHERE login = 'petrov@vstand.ru')
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'petrov@vstand.ru')
);

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Сидорова Анна Сергеевна',
       (SELECT access_id FROM roles WHERE access_rights = 'student'),
       (SELECT login_id FROM passwords WHERE login = 'sidorova@vstand.ru')
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'sidorova@vstand.ru')
);

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Козлова Мария Александровна',
       (SELECT access_id FROM roles WHERE access_rights = 'student'),
       (SELECT login_id FROM passwords WHERE login = 'kozlova@vstand.ru')
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'kozlova@vstand.ru')
);

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Новиков Дмитрий Олегович',
       (SELECT access_id FROM roles WHERE access_rights = 'student'),
       (SELECT login_id FROM passwords WHERE login = 'novikov@vstand.ru')
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'novikov@vstand.ru')
);

INSERT INTO courses (name, teacher, teacher_id) VALUES
    ('МДК 07.02', 'Самоделкин Павел Андреевич',
     (SELECT user_id FROM users WHERE full_name = 'Самоделкин Павел Андреевич')),
    ('Информационные системы и технологии', 'Жилова Юлия Андреевна',
     (SELECT user_id FROM users WHERE full_name = 'Жилова Юлия Андреевна'))
ON CONFLICT (name) DO NOTHING;

INSERT INTO labs (name, course_id, task, start_date, end_date)
SELECT 'Лабораторная работа №1',
       (SELECT course_id FROM courses WHERE name = 'МДК 07.02'),
       'Разработать консольное приложение на Python.',
       '2026-01-15 00:00:00',
       '2026-02-15 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM labs WHERE name = 'Лабораторная работа №1');

INSERT INTO labs (name, course_id, task, start_date, end_date)
SELECT 'Лабораторная работа №2',
       (SELECT course_id FROM courses WHERE name = 'МДК 07.02'),
       'Разработать REST API на Flask.',
       '2026-02-20 00:00:00',
       '2026-03-20 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM labs WHERE name = 'Лабораторная работа №2');

INSERT INTO labs (name, course_id, task, start_date, end_date)
SELECT 'Лабораторная работа №3',
       (SELECT course_id FROM courses WHERE name = 'МДК 07.02'),
       'Контейнеризация приложения с помощью Docker.',
       '2026-03-01 00:00:00',
       '2026-04-01 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM labs WHERE name = 'Лабораторная работа №3');

INSERT INTO labs (name, course_id, task, start_date, end_date)
SELECT 'Практическая №1',
       (SELECT course_id FROM courses WHERE name = 'Информационные системы и технологии'),
       'Провести анализ предметной области и построить модель данных.',
       '2026-01-21 00:00:00',
       '2026-02-05 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM labs WHERE name = 'Практическая №1');

INSERT INTO labs (name, course_id, task, start_date, end_date)
SELECT 'Практическая №2',
       (SELECT course_id FROM courses WHERE name = 'Информационные системы и технологии'),
       'Спроектировать реляционную базу данных по заданной предметной области.',
       '2026-02-10 00:00:00',
       '2026-03-10 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM labs WHERE name = 'Практическая №2');

INSERT INTO course_user (course_id, user_id)
SELECT c.course_id, u.user_id
FROM courses c, users u
JOIN roles r ON r.access_id = u.access_id
WHERE r.access_rights = 'student'
ON CONFLICT (course_id, user_id) DO NOTHING;

INSERT INTO student_projects (user_id, lab_id, github_link, grade, teacher_comment, grade_date)
SELECT
    (SELECT user_id FROM users u JOIN passwords p ON u.login_id = p.login_id WHERE p.login = 'ivanov@vstand.ru'),
    (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1'),
    'https://github.com/ivanov/lab1',
    5, 'Отличная работа!', '2026-02-10 12:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM student_projects
    WHERE user_id = (SELECT user_id FROM users u JOIN passwords p ON u.login_id = p.login_id WHERE p.login = 'ivanov@vstand.ru')
      AND lab_id = (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1')
);

INSERT INTO student_projects (user_id, lab_id, github_link, grade, teacher_comment, grade_date)
SELECT
    (SELECT user_id FROM users u JOIN passwords p ON u.login_id = p.login_id WHERE p.login = 'ivanov@vstand.ru'),
    (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №2'),
    'https://github.com/ivanov/lab2',
    4, 'Хорошо, но есть замечания по документации.', '2026-03-05 14:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM student_projects
    WHERE user_id = (SELECT user_id FROM users u JOIN passwords p ON u.login_id = p.login_id WHERE p.login = 'ivanov@vstand.ru')
      AND lab_id = (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №2')
);

INSERT INTO student_projects (user_id, lab_id, github_link, grade, teacher_comment, grade_date)
SELECT
    (SELECT user_id FROM users u JOIN passwords p ON u.login_id = p.login_id WHERE p.login = 'petrov@vstand.ru'),
    (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1'),
    'https://github.com/petrov/lab1',
    3, 'Нужно доработать обработку ошибок.', '2026-02-12 10:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM student_projects
    WHERE user_id = (SELECT user_id FROM users u JOIN passwords p ON u.login_id = p.login_id WHERE p.login = 'petrov@vstand.ru')
      AND lab_id = (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1')
);

INSERT INTO student_projects (user_id, lab_id, github_link, grade, teacher_comment, grade_date)
SELECT
    (SELECT user_id FROM users u JOIN passwords p ON u.login_id = p.login_id WHERE p.login = 'sidorova@vstand.ru'),
    (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1'),
    'https://github.com/sidorova/lab1',
    5, 'Превосходно! Чистый код и хорошая документация.', '2026-02-11 09:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM student_projects
    WHERE user_id = (SELECT user_id FROM users u JOIN passwords p ON u.login_id = p.login_id WHERE p.login = 'sidorova@vstand.ru')
      AND lab_id = (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1')
);

INSERT INTO student_projects (user_id, lab_id, github_link, grade, teacher_comment, grade_date)
SELECT
    (SELECT user_id FROM users u JOIN passwords p ON u.login_id = p.login_id WHERE p.login = 'kozlova@vstand.ru'),
    (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1'),
    'https://github.com/kozlova/lab1',
    4, 'Хорошая работа, небольшие замечания по стилю кода.', '2026-02-13 11:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM student_projects
    WHERE user_id = (SELECT user_id FROM users u JOIN passwords p ON u.login_id = p.login_id WHERE p.login = 'kozlova@vstand.ru')
      AND lab_id = (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1')
);
