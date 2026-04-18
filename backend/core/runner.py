import docker
from datetime import datetime
from backend.core.connect import get_db_connection


def run_container(image_name, project_id, project_type='console', main_file='main.py'):
    try:
        client = docker.from_env()

        client.images.get(image_name)

        container = client.containers.run(
            image_name,
            detach=True,
            stdin_open=True,
            tty=True,
            mem_limit='512m',
            command=["tail", "-f", "/dev/null"]
        )

        print(f"Контейнер запущен: {container.id[:12]}")
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS docker_containers (
                container_id VARCHAR(64) PRIMARY KEY,
                project_id INTEGER NOT NULL,
                image_name VARCHAR(255) NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'running',
                project_type VARCHAR(20) DEFAULT 'console',
                main_file VARCHAR(255)
            )
        """)
        conn.commit()

        cursor.execute("""
            INSERT INTO docker_containers 
                (container_id, project_id, image_name, status, project_type, main_file)
            VALUES (%s, %s, %s, 'running', %s, %s)
        """, (container.id, project_id, image_name, project_type, main_file))
        conn.commit()

        cursor.close()
        conn.close()

        link = f"/container/{project_id}/view"
        return container, link

    except Exception as e:
        print(f"Ошибка запуска контейнера: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def get_container_info(project_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT container_id, status, project_type, main_file
            FROM docker_containers
            WHERE project_id = %s AND status = 'running'
            ORDER BY started_at DESC LIMIT 1
        """, (project_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return None

        return {
            'container_id': row[0],
            'status': row[1],
            'project_type': row[2],
            'main_file': row[3],
            'link': f"/container/{project_id}/view"
        }
    except Exception as e:
        print(f"Ошибка получения информации о контейнере: {e}")
        return None


def stop_container_by_project(project_id):
    try:
        container_info = get_container_info(project_id)
        if not container_info:
            return False, "Контейнер не найден"

        container_id = container_info['container_id']

        client = docker.from_env()
        container = client.containers.get(container_id)
        container.stop(timeout=5)
        container.remove()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE docker_containers 
            SET status = 'stopped', stopped_at = CURRENT_TIMESTAMP
            WHERE container_id = %s
        """, (container_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return True, "Контейнер остановлен"
    except Exception as e:
        print(f"Ошибка остановки: {e}")
        return False, str(e)


def image_exists(image_name):
    try:
        client = docker.from_env()
        client.images.get(image_name)
        return True
    except docker.errors.ImageNotFound:
        return False
    except Exception as e:
        print(f"Ошибка проверки образа: {e}")
        return False