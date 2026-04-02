import pg8000

DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'course_management'
DB_USER = 'postgres'
DB_PASS = '12345678'

def get_db_connection():
    return pg8000.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )