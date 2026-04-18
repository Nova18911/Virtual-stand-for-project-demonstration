from flask import Blueprint, render_template, session, request, jsonify
from backend.core.connect import get_db_connection

tasks_bp = Blueprint('tasks', __name__)


def dict_fetchall(cursor):
    rows = cursor.fetchall()
    if not rows:
        return []
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


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

    course_name = row[0] if isinstance(row, (list, tuple)) else row['name']
    session['current_course_id']   = course_id
    session['current_course_name'] = course_name

    return render_template('tasks.html', role=role,
                           course_id=course_id, course_name=course_name)


@tasks_bp.route('/api/course/<int:course_id>/students-not-enrolled')
def students_not_enrolled(course_id):
    if session.get('user_role') != 'teacher':
        return jsonify({'error': 'Нет доступа'}), 403

    conn   = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.user_id, u.full_name
        FROM users u
        JOIN roles r ON r.access_id = u.access_id
        WHERE r.access_rights = 'student'
          AND u.user_id NOT IN (
              SELECT user_id FROM course_user WHERE course_id = %s
          )
        ORDER BY u.full_name
    """, (course_id,))

    students = dict_fetchall(cursor)
    cursor.close()
    conn.close()

    return jsonify(students)


@tasks_bp.route('/api/course/<int:course_id>/add-student', methods=['POST'])
def add_student_to_course(course_id):
    if session.get('user_role') != 'teacher':
        return jsonify({'ok': False, 'error': 'Нет доступа'}), 403

    data       = request.get_json()
    user_id    = data.get('user_id')

    if not user_id:
        return jsonify({'ok': False, 'error': 'Не указан студент'}), 400

    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT u.user_id FROM users u
            JOIN roles r ON r.access_id = u.access_id
            WHERE u.user_id = %s AND r.access_rights = 'student'
        """, (user_id,))

        if not cursor.fetchone():
            return jsonify({'ok': False, 'error': 'Студент не найден'}), 404

        cursor.execute("""
            SELECT 1 FROM course_user
            WHERE course_id = %s AND user_id = %s
        """, (course_id, user_id))

        if cursor.fetchone():
            return jsonify({'ok': False, 'error': 'Студент уже записан на курс'}), 409

        cursor.execute("""
            INSERT INTO course_user (course_id, user_id) VALUES (%s, %s)
        """, (course_id, user_id))
        conn.commit()

        return jsonify({'ok': True})

    except Exception as e:
        conn.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()