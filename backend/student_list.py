from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from backend.core.connect import get_db_connection
import sys
import os
from datetime import datetime
from backend.core.runner import run_container, get_container_info, stop_container_by_project
import docker

task_detail_bp = Blueprint('task_detail', __name__)


@task_detail_bp.route('/task/<int:lab_id>')
def task_detail(lab_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT lab_id, name FROM labs WHERE lab_id = %s", (lab_id,))
    lab_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not lab_row:
        return "Задание не найдено", 404

    lab = {'lab_id': lab_row[0], 'name': lab_row[1]}
    return render_template('student_list.html', lab=lab)


# --- API: список студентов ---
@task_detail_bp.route('/api/task/<int:lab_id>/students', methods=['GET'])
def get_students(lab_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.user_id, u.full_name
        FROM users u
        JOIN course_user cu ON cu.user_id = u.user_id
        JOIN labs l ON l.course_id = cu.course_id
        JOIN roles r ON r.access_id = u.access_id
        WHERE l.lab_id = %s AND r.access_rights = 'student'
        ORDER BY u.full_name
    """, (lab_id,))
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify([
        {'user_id': row[0], 'full_name': row[1]}
        for row in students
    ])


# --- API: данные конкретного студента ---
@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>', methods=['GET'])
def get_student_detail(lab_id, student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sp.project_id, sp.github_link, sp.grade, sp.teacher_comment, sp.build_info
        FROM student_projects sp
        WHERE sp.lab_id = %s AND sp.user_id = %s
    """, (lab_id, student_id))
    project_row = cursor.fetchone()

    cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (student_id,))
    name_row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not name_row:
        return jsonify({'ok': False, 'error': 'Студент не найден'}), 404

    comment = project_row[3] if project_row else ''
    build_info = project_row[4] if project_row else ''

    # Проверяем, был ли уже собран проект
    if build_info and '[ОБРАЗ СОЗДАН]' in build_info:
        build_success = True
    else:
        build_success = False

    project_type = None
    main_file = None
    image_name = None

    if build_success:
        for line in build_info.split('\n'):
            if '[ТИП ПРОЕКТА]' in line:
                project_type = line.split(']')[1].strip()
            elif '[ОСНОВНОЙ ФАЙЛ]' in line:
                main_file = line.split(']')[1].strip()
            elif '[ИМЯ ОБРАЗА]' in line:
                image_name = line.split(']')[1].strip()

    return jsonify({
        'ok': True,
        'user_id': student_id,
        'full_name': name_row[0],
        'github_link': project_row[1] if project_row else '',
        'grade': project_row[2] if project_row else None,
        'teacher_comment': comment,
        'build_info': build_info,
        'project_id': project_row[0] if project_row else None,
        'build_success': build_success,
        'project_type': project_type,
        'main_file': main_file,
        'image_name': image_name
    })


# --- Функция для проверки существования образа ---
def image_exists(image_name):
    """Проверяет, существует ли Docker образ"""
    try:
        client = docker.from_env()
        client.images.get(image_name)
        return True
    except docker.errors.ImageNotFound:
        return False
    except Exception as e:
        print(f"❌ Ошибка проверки образа: {e}")
        return False


# --- API: сборка контейнера (основной маршрут для фронтенда) ---
@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/build', methods=['POST'])
def build_container_compat(lab_id, student_id):
    """Собирает или запускает контейнер"""
    from backend.core.docker.build_pipeline import build_and_run, rebuild_project

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT project_id, github_link, build_info FROM student_projects
        WHERE lab_id = %s AND user_id = %s
    """, (lab_id, student_id))
    project_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not project_row:
        return jsonify({'ok': False, 'error': 'Работа студента не найдена'}), 404

    project_id = project_row[0]
    github_url = project_row[1]
    build_info = project_row[2] or ''
    image_name = f"student_{student_id}_lab_{lab_id}"

    # Проверяем параметр force_rebuild в запросе
    force_rebuild = request.args.get('force', 'false') == 'true'

    if force_rebuild:
        # Принудительная пересборка
        result = rebuild_project(github_url, project_id, image_name)
    else:
        # Обычная сборка (с проверкой существования образа)
        result = build_and_run(github_url, project_id, image_name)

    if not result['ok']:
        return jsonify({'ok': False, 'error': result['error']}), 500

    return jsonify({'ok': True, 'link': result['link']})


# --- API: запуск контейнера (без пересборки) ---
@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/run', methods=['POST'])
def run_container_api(lab_id, student_id):
    """Запускает контейнер из уже существующего образа"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT project_id, build_info FROM student_projects
        WHERE lab_id = %s AND user_id = %s
    """, (lab_id, student_id))
    project_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not project_row:
        return jsonify({'ok': False, 'error': 'Работа студента не найдена'}), 404

    project_id = project_row[0]
    build_info = project_row[1] or ''

    # Извлекаем имя образа из build_info
    image_name = None
    project_type = 'console'
    main_file = 'main.py'

    for line in build_info.split('\n'):
        if '[ИМЯ ОБРАЗА]' in line:
            image_name = line.split(']')[1].strip()
        elif '[ТИП ПРОЕКТА]' in line:
            project_type = line.split(']')[1].strip()
        elif '[ОСНОВНОЙ ФАЙЛ]' in line:
            main_file = line.split(']')[1].strip()

    if not image_name:
        return jsonify({'ok': False, 'error': 'Образ не найден. Сначала соберите проект.'}), 404

    # Проверяем, существует ли образ
    if not image_exists(image_name):
        return jsonify({'ok': False, 'error': f'Образ {image_name} не найден. Требуется пересборка.'}), 404

    # Запускаем контейнер
    container, link = run_container(image_name, project_id, project_type, main_file)

    if not container:
        return jsonify({'ok': False, 'error': 'Не удалось запустить контейнер'}), 500

    return jsonify({
        'ok': True,
        'link': link,
        'message': 'Контейнер запущен'
    })


# --- API: остановка контейнера ---
@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/stop', methods=['POST'])
def stop_container_api(lab_id, student_id):
    """Останавливает контейнер"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT project_id FROM student_projects
        WHERE lab_id = %s AND user_id = %s
    """, (lab_id, student_id))
    project_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not project_row:
        return jsonify({'ok': False, 'error': 'Проект не найден'}), 404

    project_id = project_row[0]
    success, message = stop_container_by_project(project_id)

    return jsonify({'ok': success, 'message': message})


# --- API: статус контейнера ---
@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/container-status', methods=['GET'])
def get_container_status(lab_id, student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT project_id FROM student_projects
        WHERE lab_id = %s AND user_id = %s
    """, (lab_id, student_id))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return jsonify({'ok': False, 'error': 'Проект не найден'}), 404

    project_id = row[0]
    container_info = get_container_info(project_id)

    return jsonify({
        'ok': True,
        'container': container_info
    })


# --- API: выставить оценку ---
@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/grade', methods=['POST'])
def set_grade(lab_id, student_id):
    data = request.get_json()
    grade = data.get('grade')

    if grade not in [2, 3, 4, 5]:
        return jsonify({'ok': False, 'error': 'Недопустимая оценка'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE student_projects
        SET grade = %s, grade_date = CURRENT_TIMESTAMP
        WHERE lab_id = %s AND user_id = %s
    """, (grade, lab_id, student_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'ok': True})


# --- API: сохранить комментарий ---
@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/comment', methods=['POST'])
def set_comment(lab_id, student_id):
    data = request.get_json()
    comment = data.get('comment', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE student_projects
        SET teacher_comment = %s
        WHERE lab_id = %s AND user_id = %s
    """, (comment, lab_id, student_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'ok': True})


# --- API: пересборка проекта ---
@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/rebuild', methods=['POST'])
def rebuild_container(lab_id, student_id):
    """Принудительная пересборка проекта"""
    from backend.core.docker.build_pipeline import rebuild_project

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT project_id, github_link FROM student_projects
        WHERE lab_id = %s AND user_id = %s
    """, (lab_id, student_id))
    project_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not project_row:
        return jsonify({'ok': False, 'error': 'Работа студента не найдена'}), 404

    project_id = project_row[0]
    github_url = project_row[1]
    image_name = f"student_{student_id}_lab_{lab_id}"

    result = rebuild_project(github_url, project_id, image_name)

    if not result['ok']:
        return jsonify({'ok': False, 'error': result['error']}), 500

    return jsonify({'ok': True, 'link': result['link']})