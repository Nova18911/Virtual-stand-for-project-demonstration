CREATE TABLE roles (
    access_id SERIAL PRIMARY KEY,
    access_rights VARCHAR(45) NOT NULL
);


CREATE TABLE passwords (
    login_id SERIAL PRIMARY KEY,
    login VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL
);


CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    access_id INTEGER NOT NULL,
    login_id INTEGER NOT NULL,
    FOREIGN KEY (access_id) REFERENCES roles(access_id),
    FOREIGN KEY (login_id) REFERENCES passwords(login_id)
);


CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    teacher VARCHAR(100) NOT NULL
);


CREATE TABLE labs (
    lab_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    course_id INTEGER NOT NULL,
    task TEXT,
    task_file BYTEA NOT NULL,
    start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);


CREATE TABLE course_user (
    course_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (course_id, user_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE student_projects (
    project_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    lab_id INTEGER NOT NULL,
    github_link TEXT NOT NULL,
    submission_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    grade INTEGER,
    teacher_comment TEXT,
    grade_date TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (lab_id) REFERENCES labs(lab_id),
    CHECK (grade IS NULL OR (grade > 1 AND grade < 6))
);

CREATE TABLE IF NOT EXISTS docker_containers (
    container_id VARCHAR(64) PRIMARY KEY,
    project_id INTEGER NOT NULL,
    port INTEGER NOT NULL,
    image_name VARCHAR(255) NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'running',
    CHECK (status IN ('running', 'stopped', 'removed')),
    FOREIGN KEY (project_id) REFERENCES student_projects(project_id)
);

CREATE INDEX IF NOT EXISTS idx_docker_containers_project_id ON docker_containers(project_id);
CREATE INDEX IF NOT EXISTS idx_docker_containers_status ON docker_containers(status);
CREATE INDEX IF NOT EXISTS idx_docker_containers_container_id ON docker_containers(container_id);

-- Роли
INSERT INTO roles (access_rights) VALUES
    ('admin'),
    ('teacher'),
    ('student')
ON CONFLICT DO NOTHING;

-- Логины и пароли
INSERT INTO passwords (login, password) VALUES
    ('admin',    '11'),
    ('samodelkin', 'pass123'),
    ('zhilova',    'pass456'),
    ('ivanov',     'stud001'),
    ('petrov',     'stud002'),
    ('sidorova',   'stud003'),
    ('kozlova',    'stud004'),
    ('novikov',    'stud005')
ON CONFLICT (login) DO NOTHING;

-- Пользователи
INSERT INTO users (full_name, access_id, login_id)
SELECT 'Администратор',
       (SELECT access_id FROM roles WHERE access_rights = 'admin'),
       (SELECT login_id  FROM passwords WHERE login = 'admin')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'admin'));

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Самоделкин П.А.',
       (SELECT access_id FROM roles WHERE access_rights = 'teacher'),
       (SELECT login_id  FROM passwords WHERE login = 'samodelkin')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'samodelkin'));

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Жилова Ю.А.',
       (SELECT access_id FROM roles WHERE access_rights = 'teacher'),
       (SELECT login_id  FROM passwords WHERE login = 'zhilova')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'zhilova'));

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Иванов Иван Иванович',
       (SELECT access_id FROM roles WHERE access_rights = 'student'),
       (SELECT login_id  FROM passwords WHERE login = 'ivanov')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'ivanov'));

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Петров Пётр Петрович',
       (SELECT access_id FROM roles WHERE access_rights = 'student'),
       (SELECT login_id  FROM passwords WHERE login = 'petrov')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'petrov'));

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Сидорова Анна Сергеевна',
       (SELECT access_id FROM roles WHERE access_rights = 'student'),
       (SELECT login_id  FROM passwords WHERE login = 'sidorova')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'sidorova'));

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Козлова Мария Александровна',
       (SELECT access_id FROM roles WHERE access_rights = 'student'),
       (SELECT login_id  FROM passwords WHERE login = 'kozlova')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'kozlova'));

INSERT INTO users (full_name, access_id, login_id)
SELECT 'Новиков Дмитрий Олегович',
       (SELECT access_id FROM roles WHERE access_rights = 'student'),
       (SELECT login_id  FROM passwords WHERE login = 'novikov')
WHERE NOT EXISTS (SELECT 1 FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'novikov'));

-- Курсы
INSERT INTO courses (name, teacher) VALUES
    ('МДК 07.02',                           'Самоделкин П.А.'),
    ('Информационные системы и технологии', 'Жилова Ю.А.')
ON CONFLICT (name) DO NOTHING;

-- Лабораторные работы
INSERT INTO labs (name, course_id, task, task_file, start_date, end_date)
SELECT 'Лабораторная работа №1',
       (SELECT course_id FROM courses WHERE name = 'МДК 07.02'),
       'Задание смотреть в прикреплённом файле',
       '\x'::bytea,
       '2026-01-15 00:00:00',
       '2026-02-15 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM labs WHERE name = 'Лабораторная работа №1');

INSERT INTO labs (name, course_id, task, task_file, start_date, end_date)
SELECT 'Лабораторная работа №2',
       (SELECT course_id FROM courses WHERE name = 'МДК 07.02'),
       'Разработать REST API',
       '\x'::bytea,
       '2026-02-20 00:00:00',
       '2026-03-20 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM labs WHERE name = 'Лабораторная работа №2');

INSERT INTO labs (name, course_id, task, task_file, start_date, end_date)
SELECT 'Лабораторная работа №3',
       (SELECT course_id FROM courses WHERE name = 'МДК 07.02'),
       'Контейнеризация приложения',
       '\x'::bytea,
       '2026-03-01 00:00:00',
       '2026-04-01 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM labs WHERE name = 'Лабораторная работа №3');

INSERT INTO labs (name, course_id, task, task_file, start_date, end_date)
SELECT 'Практическая №1',
       (SELECT course_id FROM courses WHERE name = 'Информационные системы и технологии'),
       'Сдать до 05.02.26!',
       '\x'::bytea,
       '2026-01-21 00:00:00',
       '2026-02-05 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM labs WHERE name = 'Практическая №1');

INSERT INTO labs (name, course_id, task, task_file, start_date, end_date)
SELECT 'Практическая №2',
       (SELECT course_id FROM courses WHERE name = 'Информационные системы и технологии'),
       'Проектирование БД',
       '\x'::bytea,
       '2026-02-10 00:00:00',
       '2026-03-10 23:59:59'
WHERE NOT EXISTS (SELECT 1 FROM labs WHERE name = 'Практическая №2');

-- Запись студентов на курсы (все студенты на оба курса)
INSERT INTO course_user (course_id, user_id)
SELECT c.course_id, u.user_id
FROM courses c, users u
JOIN roles r ON r.access_id = u.access_id
WHERE r.access_rights = 'student'
ON CONFLICT DO NOTHING;

-- Работы студентов
INSERT INTO student_projects (user_id, lab_id, github_link, grade, teacher_comment, grade_date)
SELECT
    (SELECT user_id FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'ivanov')),
    (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1'),
    'https://github.com/ivanov/lab1',
    5,
    'Отличная работа!',
    '2026-02-10 12:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM student_projects
    WHERE user_id = (SELECT user_id FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'ivanov'))
      AND lab_id  = (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1')
);

INSERT INTO student_projects (user_id, lab_id, github_link, grade, teacher_comment, grade_date)
SELECT
    (SELECT user_id FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'ivanov')),
    (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №2'),
    'https://github.com/ivanov/lab2',
    4,
    'Хорошо, но есть замечания',
    '2026-03-05 14:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM student_projects
    WHERE user_id = (SELECT user_id FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'ivanov'))
      AND lab_id  = (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №2')
);

INSERT INTO student_projects (user_id, lab_id, github_link, grade, teacher_comment, grade_date)
SELECT
    (SELECT user_id FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'petrov')),
    (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1'),
    'https://github.com/petrov/lab1',
    3,
    'Нужно доработать',
    '2026-02-12 10:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM student_projects
    WHERE user_id = (SELECT user_id FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'petrov'))
      AND lab_id  = (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1')
);

INSERT INTO student_projects (user_id, lab_id, github_link, grade, teacher_comment, grade_date)
SELECT
    (SELECT user_id FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'sidorova')),
    (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1'),
    'https://github.com/sidorova/lab1',
    5,
    'Превосходно!',
    '2026-02-11 09:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM student_projects
    WHERE user_id = (SELECT user_id FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'sidorova'))
      AND lab_id  = (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1')
);

INSERT INTO student_projects (user_id, lab_id, github_link, grade, teacher_comment, grade_date)
SELECT
    (SELECT user_id FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'kozlova')),
    (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1'),
    'https://github.com/kozlova/lab1',
    4,
    'Хорошая работа',
    '2026-02-13 11:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM student_projects
    WHERE user_id = (SELECT user_id FROM users WHERE login_id = (SELECT login_id FROM passwords WHERE login = 'kozlova'))
      AND lab_id  = (SELECT lab_id FROM labs WHERE name = 'Лабораторная работа №1')
);