# backend/core/docker/runner.py

import docker
from datetime import datetime
from backend.core.connect import get_db_connection
import os


def run_container(image_name, project_id, project_type, main_file='main.py'):
    """
    Запускает контейнер (как в рабочей версии)
    """
    try:
        print(f"🔧 Запуск контейнера: {image_name}")

        client = docker.from_env()

        # Проверяем образ
        try:
            client.images.get(image_name)
        except docker.errors.ImageNotFound:
            print(f"❌ Образ не найден")
            return None, None

        # КЛЮЧЕВОЙ МОМЕНТ: контейнер должен жить постоянно
        container = client.containers.run(
            image_name,
            detach=True,
            stdin_open=True,
            tty=True,
            mem_limit='512m',
            command=["tail", "-f", "/dev/null"]  # Контейнер живет!
        )

        print(f"✅ Контейнер запущен: {container.id[:12]}")

        # Сохраняем в БД
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS docker_containers (
                id SERIAL PRIMARY KEY,
                container_id VARCHAR(64) UNIQUE,
                project_id INTEGER,
                image_name VARCHAR(255),
                started_at TIMESTAMP,
                status VARCHAR(20),
                project_type VARCHAR(20),
                main_file VARCHAR(255)
            )
        """)
        conn.commit()

        cursor.execute("""
            INSERT INTO docker_containers 
                (container_id, project_id, image_name, started_at, status, project_type, main_file)
            VALUES (%s, %s, %s, %s, 'running', %s, %s)
        """, (container.id, project_id, image_name, datetime.now(), project_type, main_file))
        conn.commit()

        cursor.close()
        conn.close()

        link = f"/container/{project_id}/view"
        print(f"🔗 Ссылка: {link}")

        return container, link

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def get_container_info(project_id):
    """
    Получает информацию о запущенном контейнере из БД
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT container_id, status, project_type, main_file
            FROM docker_containers
            WHERE project_id = %s AND status = 'running'
            ORDER BY started_at DESC
            LIMIT 1
        """, (project_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return None

        container_id, status, project_type, main_file = row

        # Определяем ссылку в зависимости от типа
        if project_type == 'gui':
            link = f"/container/{project_id}/gui"
        else:
            link = f"/container/{project_id}/view"

        return {
            'container_id': container_id,
            'status': status,
            'project_type': project_type,
            'main_file': main_file,
            'link': link
        }

    except Exception as e:
        print(f"❌ Ошибка получения информации о контейнере: {e}")
        return None


def stop_container_by_project(project_id):
    """
    Останавливает контейнер по ID проекта
    """
    try:
        # Сначала получаем информацию о контейнере
        container_info = get_container_info(project_id)

        if not container_info:
            return False, "Контейнер не найден или уже остановлен"

        container_id = container_info['container_id']

        # Останавливаем и удаляем контейнер в Docker
        client = docker.from_env()
        container = client.containers.get(container_id)
        container.stop(timeout=5)
        container.remove()

        # Обновляем статус в БД
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

        print(f"✅ Контейнер {container_id[:12]} остановлен")
        return True, "Контейнер успешно остановлен"

    except docker.errors.NotFound:
        return False, "Контейнер не найден в Docker"
    except Exception as e:
        print(f"❌ Ошибка остановки контейнера: {e}")
        return False, str(e)


def image_exists(image_name):
    """
    Проверяет, существует ли Docker образ
    """
    try:
        client = docker.from_env()
        client.images.get(image_name)
        return True
    except docker.errors.ImageNotFound:
        return False
    except Exception as e:
        print(f"❌ Ошибка проверки образа: {e}")
        return False