import pg8000
import os

# Подключение к системной бд для создания бд сайта
conn = pg8000.connect(
    user='postgres',
    password='12345678',
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
        print("✅ База данных 'course_management' создана")
    else:
        print("ℹ️  База данных 'course_management' уже существует")
    conn.autocommit = False
conn.close()


def run_sql_file(filepath):
    conn = None
    cursor = None
    try:
        conn = pg8000.connect(
            user='postgres',
            password='12345678',
            host='localhost',
            port=5432,
            database='course_management'
        )
        cursor = conn.cursor()

        # Читаем sql файл
        with open(filepath, 'r', encoding='utf-8') as f:
            sql = f.read()

        # Разбиваем на отдельные запросы по ;
        queries = [q.strip() for q in sql.split(';') if q.strip()]

        for i, query in enumerate(queries, 1):
            try:
                cursor.execute(query)
                print(f"✅ Запрос {i} выполнен")
            except Exception as e:
                print(f"⚠️  Запрос {i} — ошибка: {e}")
                conn.rollback()
                conn = pg8000.connect(
                    user='postgres',
                    password='12345678',
                    host='localhost',
                    port=5432,
                    database='course_management'
                )
                cursor = conn.cursor()
                continue

        conn.commit()
        print("\n✅ Все операции выполнены успешно!")

    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("🔌 Соединение закрыто")


if __name__ == '__main__':
    # Путь до schema.sql относительно этого файла
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_path = os.path.join(base_dir, 'backend', 'database.sql')

    print(f"📄 Читаю файл: {sql_path}")
    run_sql_file(sql_path)