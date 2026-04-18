import docker
from flask import Blueprint, Response, render_template, request, jsonify
from backend.core.connect import get_db_connection
import threading
import queue

streamer_bp = Blueprint('streamer', __name__)

active_sessions = {}


def get_container_info_by_project(project_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT container_id, main_file 
            FROM docker_containers 
            WHERE project_id = %s AND status = 'running'
            ORDER BY started_at DESC LIMIT 1
        """, (project_id,))
        row = cursor.fetchone()
        return {'container_id': row[0], 'main_file': row[1]} if row else None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@streamer_bp.route('/container/<int:project_id>/logs')
def container_logs(project_id):
    info = get_container_info_by_project(project_id)
    if not info:
        return "Контейнер не найден", 404

    container_id = info['container_id']
    main_file = info['main_file']

    def generate():
        try:
            client = docker.from_env()
            container = client.containers.get(container_id)

            yield f"data: Запуск программы {main_file}...\n\n"

            exec_id = container.client.api.exec_create(
                container.id,
                ['python', '-u', main_file],
                stdin=True,
                stdout=True,
                stderr=True,
                tty=True,
                workdir='/app'
            )['Id']

            socket = container.client.api.exec_start(exec_id, socket=True, tty=True)

            active_sessions[project_id] = {
                'exec_id': exec_id,
                'socket': socket,
                'input_queue': queue.Queue(),
                'running': True
            }

            def input_sender():
                while active_sessions.get(project_id, {}).get('running', False):
                    try:
                        user_input = active_sessions[project_id]['input_queue'].get(timeout=0.5)
                        socket.send((user_input + '\n').encode('utf-8'))
                    except queue.Empty:
                        continue
                    except:
                        break

            threading.Thread(target=input_sender, daemon=True).start()

            while True:
                try:
                    data = socket.recv(4096)
                    if not data:
                        break
                    decoded = data.decode('utf-8', errors='replace')
                    for line in decoded.splitlines():
                        if line.strip():
                            yield f"data: {line}\n\n"
                except:
                    break

            yield "data: \nПрограмма завершила работу\n\n"
            yield "event: close\ndata: done\n\n"

        except Exception as e:
            yield f"data: Ошибка: {str(e)}\n\n"
        finally:
            if project_id in active_sessions:
                active_sessions[project_id]['running'] = False
                if 'socket' in active_sessions[project_id]:
                    try:
                        active_sessions[project_id]['socket'].close()
                    except:
                        pass
                active_sessions.pop(project_id, None)

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@streamer_bp.route('/container/<int:project_id>/input', methods=['POST'])
def container_input(project_id):
    if project_id not in active_sessions:
        return jsonify({'error': 'Сессия не найдена'}), 404

    user_input = request.form.get('input', '').strip()
    if user_input:
        active_sessions[project_id]['input_queue'].put(user_input)

    return jsonify({'success': True})


@streamer_bp.route('/container/<int:project_id>/view')
def container_view(project_id):
    info = get_container_info_by_project(project_id)
    main_file = info['main_file'] if info else 'program.py'
    return render_template('container_view.html', project_id=project_id, main_file=main_file)


@streamer_bp.route('/container/<int:project_id>/stop', methods=['POST'])
def stop_container(project_id):
    try:
        from backend.core.runner import stop_container_by_project
        success, message = stop_container_by_project(project_id)
        if project_id in active_sessions:
            active_sessions[project_id]['running'] = False
            active_sessions.pop(project_id, None)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

