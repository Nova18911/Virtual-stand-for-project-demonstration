import socket
import docker
import pg8000
from datetime import datetime

def get_db_connection():
    return pg8000.connect(
        host="localhost",
        port=5432,
        database="course_management",
        user="postgres",
        password="12345"
    )

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def run_container(image_name, project_id):
    conn = None
    cursor = None
    try:
        client = docker.from_env()
        port = find_free_port()

        container = client.containers.run(
            image_name,
            detach=True,
            ports={'5000/tcp': port}
        )

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO docker_containers (container_id, project_id, port, image_name, started_at, status)
            VALUES (%s, %s, %s, %s, %s, 'running')
        """, (container.id, project_id, port, image_name, datetime.now()))
        conn.commit()

        link = f"http://localhost:{port}"
        return container, link

    except docker.errors.ImageNotFound:
        print(f"❌ Образ '{image_name}' не найден")
        return None, None

    except docker.errors.APIError as e:
        print(f"❌ Ошибка Docker API: {e}")
        return None, None

    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")
        return None, None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_container_info(project_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT container_id, port, image_name, started_at, status
            FROM docker_containers
            WHERE project_id = %s
            ORDER BY started_at DESC
            LIMIT 1
        """, (project_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return {
            'container_id': row[0],
            'port': row[1],
            'image_name': row[2],
            'started_at': row[3],
            'status': row[4],
            'link': f"http://localhost:{row[1]}" if row[4] == 'running' else None
        }

    except Exception as e:
        print(f"❌ Ошибка получения данных контейнера: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()