import pg8000
import os
from core.connect import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS


def create_database():
    conn = None
    try:
        conn = pg8000.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASS,
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        if cursor.fetchone():
            print(f"База данных '{DB_NAME}' уже существует")
        else:
            cursor.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"База данных '{DB_NAME}' создана")

        cursor.close()
    except Exception as e:
        print(f"Ошибка создания БД: {e}")
    finally:
        if conn:
            conn.close()


def run_sql_file(filepath):
    if not os.path.exists(filepath):
        print(f"Файл не найден: {filepath}")
        return

    conn   = None
    cursor = None
    try:
        conn   = pg8000.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASS,
            database=DB_NAME
        )
        cursor = conn.cursor()

        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()

        queries = [q.strip() for q in sql.split(';') if q.strip()]
        total   = len(queries)
        errors  = 0

        for i, query in enumerate(queries, 1):
            try:
                cursor.execute(query)
            except Exception as e:
                errors += 1
                print(f"Запрос {i}/{total} — ошибка: {e}")
                conn.rollback()
                cursor.close()
                cursor = conn.cursor()
                continue

        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
    finally:
        if cursor: cursor.close()
        if conn:
            conn.close()


if __name__ == '__main__':
    create_database()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_path = os.path.join(base_dir, 'backend', 'database.sql')

    run_sql_file(sql_path)