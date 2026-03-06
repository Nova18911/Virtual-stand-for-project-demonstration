import pg8000

conn = pg8000.connect(
    host="127.0.0.1",
    port=5432,
    database="course_management",
    user="postgres",
    password="endermen"
)

create_queries = [
    """
    CREATE TABLE IF NOT EXISTS roles (
        access_id SERIAL PRIMARY KEY,
        access_rights VARCHAR(45) NOT NULL
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS passwords (
        login_id SERIAL PRIMARY KEY,
        login VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(50) NOT NULL
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        full_name VARCHAR(100) NOT NULL,
        access_id INTEGER NOT NULL,
        login_id INTEGER NOT NULL,
        FOREIGN KEY (access_id) REFERENCES roles(access_id),
        FOREIGN KEY (login_id) REFERENCES passwords(login_id)
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS courses (
        course_id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE,
        teacher VARCHAR(100) NOT NULL
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS labs (
        lab_id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL UNIQUE,
        course_id INTEGER NOT NULL,
        task TEXT,
        task_file BYTEA NOT NULL,
        start_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        end_date TIMESTAMP NOT NULL,
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS course_user (
        course_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        PRIMARY KEY (course_id, user_id),
        FOREIGN KEY (course_id) REFERENCES courses(course_id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS student_projects (
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
    )
    """
]

try:
   
    cursor = conn.cursor()
    for i, query in enumerate(create_queries, 1):
        cursor.execute(query)
        print(f" Таблица {i} успешно создана")
    
    conn.commit()
    print("\n Все 7 таблиц успешно созданы в базе данных 'course_management'!")
    
except Exception as e:
    print(f"Ошибка при работе с базой данных: {e}")
    if 'conn' in locals() and conn:
        conn.rollback()
    
finally:
    if 'cursor' in locals() and cursor:
        cursor.close()
    if 'conn' in locals() and conn:
        conn.close()
        print("🔌 Соединение с базой данных закрыто")