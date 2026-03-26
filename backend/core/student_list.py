from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from core.connect import get_db_connection
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from backend.core.runner import run_container, get_container_info

task_detail_bp = Blueprint('task_detail', __name__)


@task_detail_bp.route('/task/<int:lab_id>')
def task_detail(lab_id):
    conn   = get_db_connection()
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
    conn   = get_db_connection()
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
    conn   = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sp.project_id, sp.github_link, sp.grade, sp.teacher_comment
        FROM student_projects sp
        WHERE sp.lab_id = %s AND sp.user_id = %s
    """, (lab_id, student_id))
    project_row = cursor.fetchone()

    cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (student_id,))
    name_row = cursor.fetchone()

    project_id     = project_row[0] if project_row else None
    container_info = get_container_info(project_id) if project_id else None

    cursor.close()
    conn.close()

    if not name_row:
        return jsonify({'ok': False, 'error': 'Студент не найден'}), 404

    return jsonify({
        'ok':             True,
        'user_id':        student_id,
        'full_name':      name_row[0],
        'github_link':    project_row[1] if project_row else '',
        'grade':          project_row[2] if project_row else None,
        'teacher_comment':project_row[3] if project_row else '',
        'project_id':     project_id,
        'container': {
            'status': container_info['status'] if container_info else None,
            'link':   container_info['link']   if container_info else None,
        } if container_info else None,
    })


# --- API: сборка контейнера ---
@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/build', methods=['POST'])
def build_container(lab_id, student_id):
    conn   = get_db_connection()
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

    project_id  = project_row[0]
    image_name  = f"student_{student_id}_lab_{lab_id}"
    container, link = run_container(image_name, project_id)

    if not container:
        return jsonify({'ok': False, 'error': 'Ошибка при запуске контейнера'}), 500

    return jsonify({'ok': True, 'link': link})


# --- API: выставить оценку ---
@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/grade', methods=['POST'])
def set_grade(lab_id, student_id):
    data  = request.get_json()
    grade = data.get('grade')

    if grade not in [2, 3, 4, 5]:
        return jsonify({'ok': False, 'error': 'Недопустимая оценка'}), 400

    conn   = get_db_connection()
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
    data    = request.get_json()
    comment = data.get('comment', '')

    conn   = get_db_connection()
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