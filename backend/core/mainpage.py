from flask import Blueprint, jsonify, redirect, url_for, render_template, session, request
from backend.core.connect import get_db_connection

mainpage_bp = Blueprint('mainpage', __name__)

@mainpage_bp.route('/api/courses')
def get_courses():
    conn = get_db_connection()
    cursor = conn.cursor()

    role = session.get('user_role')
    user_id = session.get('user_id')

    if role == 'teacher':
        cursor.execute("""
            SELECT course_id, name, teacher,
                   CASE WHEN teacher_id = %s THEN true ELSE false END as is_enrolled
            FROM courses
            ORDER BY course_id
        """, (user_id,))
    elif role == 'student':
        cursor.execute("""
            SELECT c.course_id, c.name, c.teacher,
                   CASE WHEN cu.user_id IS NOT NULL THEN true ELSE false END as is_enrolled
            FROM courses c
            LEFT JOIN course_user cu ON c.course_id = cu.course_id AND cu.user_id = %s
            ORDER BY c.course_id
        """, (user_id,))
    else:
        is_admin = (role == 'admin')
        cursor.execute("""
            SELECT course_id, name, teacher, %s as is_enrolled
            FROM courses
            ORDER BY course_id
        """, (is_admin,))

    courses = cursor.fetchall()
    
    formatted_courses = [
        {
            'id': r[0], 
            'course': r[1], 
            'teacher': r[2],
            'is_enrolled': r[3]
        } for r in courses
    ]

    cursor.close()
    conn.close()
    return jsonify(formatted_courses)

@mainpage_bp.route('/courses')
def courses_page():
    return render_template('mainpage.html')

@mainpage_bp.route('/course/<int:course_id>')
def course_page(course_id):
    role = session.get('user_role')
    user_id = session.get('user_id')

    if not role or not user_id:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cur = conn.cursor()
    access_allowed = False

    try:
        if role == 'teacher':
            cur.execute('SELECT 1 FROM courses WHERE course_id = %s AND teacher_id = %s', (course_id, user_id))
            if cur.fetchone(): access_allowed = True
        elif role == 'student':
            cur.execute('SELECT 1 FROM course_user WHERE course_id = %s AND user_id = %s', (course_id, user_id))
            if cur.fetchone(): access_allowed = True
        elif role == 'admin':
            access_allowed = True

    finally:
        cur.close()
        conn.close()

    if access_allowed:
        return redirect(url_for('tasks.course_tasks', course_id=course_id))
    
    return redirect(url_for('mainpage.courses_page'))