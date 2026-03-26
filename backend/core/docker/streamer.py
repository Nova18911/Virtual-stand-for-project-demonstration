# backend/core/docker/streamer.py - альтернативная версия с поддержкой ввода

import docker
from flask import Blueprint, Response, render_template, request, jsonify
from backend.core.connect import get_db_connection
import select
import threading
import queue

streamer_bp = Blueprint('streamer', __name__)

# Хранилище для активных сессий
active_sessions = {}


def get_container_id_by_project(project_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT container_id FROM docker_containers
            WHERE project_id = %s AND status = 'running'
            ORDER BY started_at DESC
            LIMIT 1
        """, (project_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def get_main_file_from_db(project_id):
    """Получает имя основного файла из БД"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT teacher_comment FROM student_projects
            WHERE project_id = %s
        """, (project_id,))
        row = cursor.fetchone()

        if row and row[0]:
            for line in row[0].split('\n'):
                if '[ОСНОВНОЙ ФАЙЛ]' in line:
                    return line.split(']')[1].strip()
        return 'test.py'
    except Exception as e:
        print(f"❌ Ошибка получения main_file: {e}")
        return 'test.py'
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def stream_container_logs_with_input(container_id, project_id):
    """Потоковая передача логов с поддержкой ввода"""
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)

        main_file = get_main_file_from_db(project_id)
        yield f"data: 🚀 Запуск программы {main_file}...\n\n"

        # Создаем сокет для ввода
        sock = container.attach_socket(params={'stdin': True, 'stream': True})

        # Запускаем процесс с интерактивным режимом
        exec_id = container.client.api.exec_create(
            container.id,
            ['python', '-u', main_file],
            stdin=True,
            stdout=True,
            stderr=True,
            tty=True,
            workdir='/app'
        )['Id']

        # Подключаемся к процессу
        exec_sock = container.client.api.exec_start(exec_id, socket=True)

        # Создаем очередь для ввода
        input_queue = queue.Queue()
        active_sessions[project_id] = {
            'exec_id': exec_id,
            'socket': exec_sock,
            'queue': input_queue
        }

        # Функция для чтения вывода
        def read_output():
            while True:
                try:
                    data = exec_sock.recv(4096)
                    if not data:
                        break
                    yield data
                except:
                    break

        # Читаем и отправляем вывод
        for data in read_output():
            try:
                decoded = data.decode('utf-8', errors='replace')
                for line in decoded.split('\n'):
                    if line.strip():
                        yield f"data: {line}\n\n"
            except:
                pass

        yield "data: \n✅ Программа завершила работу\n\n"
        yield "event: close\ndata: done\n\n"

    except Exception as e:
        yield f"data: ❌ Ошибка: {str(e)}\n\n"
        yield "event: close\ndata: done\n\n"
    finally:
        if project_id in active_sessions:
            del active_sessions[project_id]


@streamer_bp.route('/container/<int:project_id>/logs')
def container_logs(project_id):
    """Эндпоинт для получения логов через Server-Sent Events"""
    container_id = get_container_id_by_project(project_id)
    if not container_id:
        return "Контейнер не найден", 404

    return Response(
        stream_container_logs_with_input(container_id, project_id),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@streamer_bp.route('/container/<int:project_id>/input', methods=['POST'])
def container_input(project_id):
    """Отправка ввода в контейнер"""
    user_input = request.form.get('input', '')

    if project_id not in active_sessions:
        return "Сессия не найдена", 404

    try:
        session = active_sessions[project_id]
        sock = session['socket']
        sock.send(f"{user_input}\n".encode('utf-8'))
        return "OK", 200
    except Exception as e:
        print(f"❌ Ошибка отправки ввода: {e}")
        return f"Ошибка: {str(e)}", 500


@streamer_bp.route('/container/<int:project_id>/stop', methods=['POST'])
def stop_container(project_id):
    """Остановка контейнера"""
    container_id = get_container_id_by_project(project_id)
    if not container_id:
        return jsonify({'error': 'Контейнер не найден'}), 404

    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        container.stop()
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

        # Очищаем сессию
        if project_id in active_sessions:
            del active_sessions[project_id]

        return jsonify({'success': True})

    except Exception as e:
        print(f"❌ Ошибка остановки: {e}")
        return jsonify({'error': str(e)}), 500


@streamer_bp.route('/container/<int:project_id>/view')
def container_view(project_id):
    """Страница просмотра консоли"""
    return render_template('container_view.html', project_id=project_id)