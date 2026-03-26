# backend/core/docker/runner.py

import socket
import docker
import pg8000
from datetime import datetime
from backend.core.connect import get_db_connection


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def run_container(image_name, project_id, project_type=None):
    conn = None
    cursor = None
    try:
        print(f"🔧 Запуск контейнера: image={image_name}, project_id={project_id}, type={project_type}")

        client = docker.from_env()

        # Проверяем, существует ли образ
        try:
            client.images.get(image_name)
            print(f"✅ Образ {image_name} найден")
        except docker.errors.ImageNotFound:
            print(f"❌ Образ {image_name} не найден")
            return None, None

        if project_type == 'web':
            print("🌐 Запуск как веб-приложение")
            port = find_free_port()
            container = client.containers.run(
                image_name,
                detach=True,
                ports={'5000/tcp': port},
                mem_limit='512m'
            )
            link = f"http://localhost:{port}"
            port_value = port
            print(f"✅ Веб-контейнер запущен на порту {port}")

        else:
            print("💻 Запуск как консольное приложение")
            container = client.containers.run(
                image_name,
                detach=True,
                stdin_open=True,
                tty=True,
                mem_limit='512m',
                command=["tail", "-f", "/dev/null"]
            )
            link = f"/container/{project_id}/view"
            port_value = None  # Для консольных приложений порт не нужен
            print(f"✅ Консольный контейнер запущен: {container.id[:12]}")

            # Проверяем, что контейнер работает
            container.reload()
            print(f"📊 Статус контейнера: {container.status}")

        # Сохраняем в БД
        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверяем, существует ли таблица
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'docker_containers'
            );
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("❌ Таблица docker_containers не существует! Создайте её в БД.")
            # Создаем таблицу на лету
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS docker_containers (
                    id SERIAL PRIMARY KEY,
                    container_id VARCHAR(64) NOT NULL UNIQUE,
                    project_id INTEGER NOT NULL,
                    port INTEGER,
                    image_name VARCHAR(255) NOT NULL,
                    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    stopped_at TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'running'
                );
            """)
            conn.commit()
            print("✅ Таблица docker_containers создана")

        # Вставляем данные
        cursor.execute("""
            INSERT INTO docker_containers (container_id, project_id, port, image_name, started_at, status)
            VALUES (%s, %s, %s, %s, %s, 'running')
        """, (container.id, project_id, port_value, image_name, datetime.now()))
        conn.commit()
        print(f"💾 Информация сохранена в БД")

        return container, link

    except Exception as e:
        print(f"❌ Ошибка в run_container: {e}")
        import traceback
        traceback.print_exc()
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

        link = None
        if row[4] == 'running':
            if row[1]:  # Если есть порт
                link = f"http://localhost:{row[1]}"
            else:
                link = f"/container/{project_id}/view"

        return {
            'container_id': row[0],
            'port': row[1],
            'image_name': row[2],
            'started_at': row[3],
            'status': row[4],
            'link': link
        }

    except Exception as e:
        print(f"❌ Ошибка получения данных контейнера: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _run_web_container(image_name, project_id, client):
    """Запуск веб-приложения"""
    port = find_free_port()

    container = client.containers.run(
        image_name,
        detach=True,
        ports={'5000/tcp': port},
        mem_limit='512m'
    )

    # Сохраняем в БД
    _save_container_info(container.id, project_id, port, image_name)

    link = f"http://localhost:{port}"
    return container, link


def _run_console_container(image_name, project_id, client):
    """Запуск консольного приложения с возможностью ввода"""
    # Для консольных приложений используем интерактивный режим
    container = client.containers.run(
        image_name,
        detach=True,
        stdin_open=True,  # Открыть stdin
        tty=True,  # Выделить псевдо-TTY
        mem_limit='256m',
        command=["python", "-u", "test.py"]  # -u для unbuffered output
    )

    # Для консольных приложений порт не нужен
    _save_container_info(container.id, project_id, None, image_name)

    # Ссылка для консольного приложения - это WebSocket для ввода/вывода
    link = f"ws://localhost/console/{container.id}"
    return container, link


def _save_container_info(container_id, project_id, port, image_name):
    """Сохраняет информацию о контейнере в БД"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO docker_containers (container_id, project_id, port, image_name, started_at, status)
        VALUES (%s, %s, %s, %s, %s, 'running')
    """, (container_id, project_id, port, image_name, datetime.now()))
    conn.commit()
    cursor.close()
    conn.close()