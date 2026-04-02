from flask import Blueprint, jsonify, redirect, url_for, render_template, session
from backend.core.connect import get_db_connection

mainpage_bp = Blueprint('mainpage', __name__)

# Эту функцию мы добавили/переименовали, чтобы auth.py мог на неё ссылаться
@mainpage_bp.route('/courses')
def courses_page():
    return render_template('mainpage.html')

@mainpage_bp.route('/api/courses')
def get_courses():
    user_id = session.get('user_id')
    role = session.get('user_role', 'student')
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            c.course_id,
            c.name,
            c.teacher,
            (CASE WHEN cu.user_id IS NOT NULL THEN TRUE ELSE FALSE END) as is_enrolled
        FROM courses c
        LEFT JOIN course_user cu ON c.course_id = cu.course_id AND cu.user_id = %s
        ORDER BY c.course_id
    """, (user_id,))

    courses = cursor.fetchall()
    formatted_courses = []
    for course in courses:
        access_granted = True if role == 'teacher' else bool(course[3])
        formatted_courses.append({
            'id': course[0],
            'course': course[1],
            'teacher': course[2],
            'is_enrolled': access_granted
        })
    
    cursor.close()
    conn.close()
    return jsonify(formatted_courses)

@mainpage_bp.route('/course/<int:course_id>')
def course_page(course_id):
    user_id = session.get('user_id')
    role = session.get('user_role')

    if role == 'student':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM course_user WHERE course_id = %s AND user_id = %s", (course_id, user_id))
        enrolled = cur.fetchone()
        cur.close()
        conn.close()
        
        if not enrolled:
            return redirect(url_for('mainpage.courses_page'))

    return redirect(url_for('tasks.course_tasks', course_id=course_id))