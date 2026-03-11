import pg8000

#подключение к системной бд для создания бд сайта (параметры user и password у каждого свои)
conn = pg8000.connect(
    user='postgres',
    password='12345',
    host='localhost',
    port=5432,
    database='postgres'
)


with conn.cursor() as cursor:
    conn.autocommit = True
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'course_management'")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute("CREATE DATABASE course_management")
    conn.autocommit = False
conn.close()

#подключение к созданной бд (параметры user и password у каждого свои)
conn = pg8000.connect(
    user='postgres',
    password='12345',
    host='localhost',
    port=5432,
    database='course_management'
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

admin_data = {
    'access_rights': 'admin',
    'login': '12',
    'password': '11',
    'full_name': 'Aдминистратор'
}


def insert_test_data():
    conn = None
    cursor = None
    try:
        conn = pg8000.connect(
            user='postgres',
            password='12345',
            host='localhost',
            port=5432,
            database='course_management'
        )
        cursor = conn.cursor()

        # Вставляем курсы
        courses_data = [
            ('МДК 07.02', 'Самоделкин П.А. Преподаватель университета'),
            ('Информационные системы и технологии', 'Жилова Ю.А. Преподаватель университета')
        ]

        for course_name, teacher in courses_data:
            cursor.execute("""
                INSERT INTO courses (name, teacher) 
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (course_name, teacher))

        # Вставляем лабораторные работы
        labs_data = [
            ('Лабораторная работа №2', 'МДК 07.02', 'Задание смотреть в прикреплённом файле',
             '2026-02-20 00:00:00', '2026-03-20 23:59:59'),
            ('Практическая №1', 'Информационные системы и технологии', 'Сдать до 05.02.26!',
             '2026-02-21 00:00:00', '2026-02-05 23:59:59')
        ]

        for lab_name, course_name, task, start_date, end_date in labs_data:
            cursor.execute("""
                INSERT INTO labs (name, course_id, task, task_file, start_date, end_date)
                SELECT %s, course_id, %s, %s, %s::timestamp, %s::timestamp
                FROM courses 
                WHERE name = %s
            """, (lab_name, task, b'', start_date, end_date, course_name))

        conn.commit()
        print("✅ Тестовые данные успешно добавлены!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Вызываем функцию
insert_test_data()

try:
    cursor = conn.cursor()
    for i, query in enumerate(create_queries, 1):
        cursor.execute(query)
        print(f" Таблица {i} успешно создана")

    conn.commit()
    print("\n Все 7 таблиц успешно созданы в базе данных 'course_management'!")

    cursor = conn.cursor()

    cursor.execute("SELECT access_id FROM roles WHERE access_rights = %s", (admin_data['access_rights'],))
    role = cursor.fetchone()

    if not role:
        cursor.execute("INSERT INTO roles (access_rights) VALUES (%s) RETURNING access_id",
                       (admin_data['access_rights'],))
        access_id = cursor.fetchone()[0]
    else:
        access_id = role[0]

    cursor.execute("SELECT login_id FROM passwords WHERE login = %s", (admin_data['login'],))
    login = cursor.fetchone()

    if not login:
        cursor.execute("INSERT INTO passwords (login, password) VALUES (%s, %s) RETURNING login_id",
                       (admin_data['login'], admin_data['password']))
        login_id = cursor.fetchone()[0]
    else:
        login_id = login[0]

    cursor.execute("""
            SELECT user_id FROM users 
            WHERE full_name = %s AND access_id = %s AND login_id = %s
        """, (admin_data['full_name'], access_id, login_id))

    if not cursor.fetchone():
        cursor.execute("""
                INSERT INTO users (full_name, access_id, login_id) 
                VALUES (%s, %s, %s)
            """, (admin_data['full_name'], access_id, login_id))
        conn.commit()
        print("\n✅ Все операции успешно выполнены!")
    
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