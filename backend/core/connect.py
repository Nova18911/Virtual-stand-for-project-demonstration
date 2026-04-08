import pg8000
import os

def get_db_connection():
    return pg8000.connect(
        host="localhost",
        port=5432,
        database="course_management",
        user="postgres",
        #password="12345678"
        password="12345"
    )