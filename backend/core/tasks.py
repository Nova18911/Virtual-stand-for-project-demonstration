from flask import Blueprint, render_template, session
from backend.core.connect import get_db_connection

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/tasks/course/<int:course_id>')
def course_tasks(course_id):
    role = session.get('user_role', 'student')

    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM courses WHERE course_id = %s", (course_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return "Курс не найден", 404

    course_name = row[0]
    session['current_course_id']   = course_id
    session['current_course_name'] = course_name

    return render_template('tasks.html', role=role,
                           course_id=course_id, course_name=course_name)

