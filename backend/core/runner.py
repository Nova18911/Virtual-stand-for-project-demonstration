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
    conn   = None
    cursor = None
    try:
        client = docker.from_env()

        try:
            client.images.get(image_name)
        except docker.errors.ImageNotFound:
            print(f"❌ Образ {image_name} не найден")
            return None, None

        if project_type == 'gui':
            container, link, port_value = _run_gui_container(image_name, project_id, client)

        else:  # console
            container, link, port_value = _run_console_container(image_name, project_id, client)

        # Сохраняем в БД
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO docker_containers
                (container_id, project_id, port, image_name, started_at, status, project_type)
            VALUES (%s, %s, %s, %s, %s, 'running', %s)
        """, (container.id, project_id, port_value, image_name, datetime.now(), project_type or 'console'))
        conn.commit()

        return container, link

    except Exception as e:
        print(f"❌ Ошибка в run_container: {e}")
        return None, None
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()


def get_container_info(project_id):
    conn   = None
    cursor = None
    try:
        conn   = get_db_connection()
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
            if row[1]:
                # Если порт есть — определяем тип по image_name
                if 'gui' in row[2]:
                    link = f"http://localhost:{row[1]}/vnc.html?password=vstand&autoconnect=true"
                else:
                    link = f"http://localhost:{row[1]}"
            else:
                link = f"/container/{project_id}/view"

        return {
            'container_id': row[0],
            'port':         row[1],
            'image_name':   row[2],
            'started_at':   row[3],
            'status':       row[4],
            'link':         link
        }
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn:   conn.close()

def _run_console_container(image_name, project_id, client):
    container = client.containers.run(
        image_name,
        detach=True,
        stdin_open=True,
        tty=True,
        mem_limit='256m',
        command=["python", "-u", "main.py"]
    )
    return container, f"/container/{project_id}/view", None


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

def _run_gui_container(image_name, project_id, client):
    """
    Запуск GUI-приложения через VNC.
    Внутри контейнера запускается Xvfb + x11vnc,
    снаружи доступен VNC-порт и noVNC (веб-браузер).
    """
    vnc_port   = find_free_port()  # порт для VNC
    novnc_port = find_free_port()  # порт для noVNC (просмотр в браузере)

    container = client.containers.run(
        image_name,
        detach=True,
        stdin_open=True,
        tty=True,
        mem_limit='512m',
        environment={
            'DISPLAY':      ':99',
            'VNC_PASSWORD': 'vstand',
        },
        ports={
            '5900/tcp': vnc_port,    # стандартный VNC порт
            '6080/tcp': novnc_port,  # noVNC веб-интерфейс
        },
        # Запускаем Xvfb + x11vnc + приложение
        command=[
            '/bin/sh', '-c',
            'Xvfb :99 -screen 0 1280x720x24 & '
            'x11vnc -display :99 -passwd vstand -forever -rfbport 5900 & '
            'sleep 2 && python main.py'
        ]
    )

    # Ссылка открывает noVNC в браузере
    link      = f"http://localhost:{novnc_port}/vnc.html?password=vstand&autoconnect=true"
    port_value = novnc_port

    return container, link, port_value