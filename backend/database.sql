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