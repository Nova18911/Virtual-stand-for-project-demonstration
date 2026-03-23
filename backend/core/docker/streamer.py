import pg8000
import docker
from flask import Blueprint, Response, render_template, request

streamer_bp = Blueprint('streamer', __name__)

def get_db_connection():
    return pg8000.connect(
        host="localhost",
        port=5432,
        database="course_management",
        user="postgres",
        password="12345678"
    )

def get_container_id_by_project(project_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT container_id FROM docker_containers
            WHERE project_id = %s
            AND status = 'running'
            ORDER BY started_at DESC
            LIMIT 1
        """, (project_id,))
        row = cursor.fentchone()
        return row[0] if row else None
    except Exception as e:
        print(f"❌ Ошибка получения container_id: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def stream_container_logs(container_id):
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)

        for line in container.logs(stream=True, follow=True):
            decoded = line.decode('utf-8', errors='replace').rstrip()
            yield  f"data: {decoded}\n\n"

        yield  "data: [Программа завершила работу]\n\n"
        yield "event: close\ndata: done\n\n"

    except docker.errors.NotFound:
        yield "data: ❌ Контейнер не найден\n\n"
        yield "event: close\ndata: done\n\n"

    except Exception as e:
        yield f"data: ❌ Ошибка: {str(e)}\n\n"
        yield "event: close\ndata: done\n\n"

@streamer_bp.route('/container/<int:project_id>/logs')
def container_logs(project_id):
    container_id = get_container_id_by_project(project_id)

    if not container_id:
        return  "Контейнер не найден", 404

    return Response(
        stream_container_logs(container_id),
        mimetype='text/event-stream',
        headers={
            'Cache-Control: no-cache',
            'X-Accel-Buffering: no'
        }
    )

@streamer_bp.route('/container/<int:project_id>/input', methods=['POST'])
def container_input(project_id):
    user_input = request.form.get('input', '')
    container_id = get_container_id_by_project(project_id)

    if not container_id:
        return "Контейнер не найден", 404

    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        socket = container.attach_socket(params={
            'stdin': True,
            'stream': True
        })
        socket._sock.send(f"{user_input}\n".encode('utf-8'))
        socket.close()

        return "OK", 200
    except Exception as e:
        return f"Ошибка: {str(e)}", 500

@streamer_bp.route('/container/<int:project_id>/view')
def container_view(project_id):
    return render_template('container_view.html', project_id=project_id)
