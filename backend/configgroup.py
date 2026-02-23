import pg8000

print("Проверка таблиц")

conn = pg8000.connect(
    host="127.0.0.1",
    port=5432,
    database="course_management",
    user="postgres",
    password="endermen"
)
cursor = conn.cursor()

cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public'
    ORDER BY table_name
""")
tables = cursor.fetchall()

if tables:
    print(f"Найдено таблиц: {len(tables)}")
    print("-" * 30)
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table[0]}")
    print("Количество записей в таблицах:")
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"{table_name}: {count} записей")
else:
    print("Таблицы не найдены")

cursor.close()
conn.close()
