# backend/core/docker/streamer.py

import docker
from flask import Blueprint, Response, render_template, request, jsonify
from backend.core.connect import get_db_connection

streamer_bp = Blueprint('streamer', __name__)

# Хранилище для активных сессий
active_sessions = {}


def get_container_info_by_project(project_id):
    """Получает информацию о контейнере из БД"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT container_id, main_file, status
            FROM docker_containers
            WHERE project_id = %s AND status = 'running'
            ORDER BY started_at DESC
            LIMIT 1
        """, (project_id,))
        row = cursor.fetchone()

        if row:
            return {'container_id': row[0], 'main_file': row[1], 'status': row[2]}
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@streamer_bp.route('/container/<int:project_id>/logs')
def container_logs(project_id):
    """Эндпоинт для получения логов"""
    container_info = get_container_info_by_project(project_id)

    if not container_info:
        return "Контейнер не найден", 404

    container_id = container_info['container_id']
    main_file = container_info['main_file']

    def generate():
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)

            yield f"data: 🚀 Запуск программы {main_file}...\n\n"

            # Запускаем Python процесс внутри контейнера
            exec_instance = container.exec_run(
                ['python', '-u', main_file],
                stdout=True,
                stderr=True,
                stream=True,
                workdir='/app'
            )

            # Читаем вывод
            for line in exec_instance.output:
                try:
                    if isinstance(line, bytes):
                        decoded = line.decode('utf-8', errors='replace')
                    else:
                        decoded = str(line)

                    decoded = decoded.strip()
                    if decoded:
                        yield f"data: {decoded}\n\n"
                except:
                    pass

            yield "data: \n✅ Программа завершила работу\n\n"
            yield "event: close\ndata: done\n\n"

        except Exception as e:
            yield f"data: ❌ Ошибка: {str(e)}\n\n"
            yield "event: close\ndata: done\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@streamer_bp.route('/container/<int:project_id>/view')
def container_view(project_id):
    """Страница просмотра консоли"""
    return render_template('container_view.html', project_id=project_id)


@streamer_bp.route('/container/<int:project_id>/stop', methods=['POST'])
def stop_container(project_id):
    """Остановка контейнера"""
    try:
        from backend.core.runner import stop_container_by_project
        success, message = stop_container_by_project(project_id)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'error': str(e)}), 500