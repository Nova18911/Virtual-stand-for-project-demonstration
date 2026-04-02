from flask import Blueprint, jsonify, redirect, url_for, render_template, session
from backend.core.connect import get_db_connection

mainpage_bp = Blueprint('mainpage', __name__)


@mainpage_bp.route('/api/courses')
def get_courses():
    conn = get_db_connection()
    cursor = conn.cursor()

    role = session.get('user_role')
    user_id = session.get('user_id')

    if role == 'teacher':
        # Преподаватель видит только свои курсы
        cursor.execute("""
            SELECT course_id, name, teacher
            FROM courses
            WHERE teacher_id = %s
            ORDER BY course_id
        """, (user_id,))
    elif role == 'student':
        # Студент видит курсы на которые записан
        cursor.execute("""
            SELECT c.course_id, c.name, c.teacher
            FROM courses c
            JOIN course_user cu ON c.course_id = cu.course_id
            WHERE cu.user_id = %s
            ORDER BY c.course_id
        """, (user_id,))
    else:
        # Все остальные (включая незалогиненных) — все курсы
        cursor.execute("""
            SELECT course_id, name, teacher
            FROM courses
            ORDER BY course_id
        """)

    courses = cursor.fetchall()
    formatted_courses = [{'id': r[0], 'course': r[1], 'teacher': r[2]} for r in courses]

    cursor.close()
    conn.close()
    return jsonify(formatted_courses)


@mainpage_bp.route('/courses')
def courses_page():
    return render_template('mainpage.html')


@mainpage_bp.route('/course/<int:course_id>')
def course_page(course_id):
    # Проверяем доступ преподавателя к конкретному курсу
    if session.get('user_role') == 'teacher':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT teacher_id FROM courses WHERE course_id = %s', (course_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row or row[0] != session.get('user_id'):
            return redirect(url_for('mainpage.courses_page'))

    return redirect(url_for('tasks.course_tasks', course_id=course_id))