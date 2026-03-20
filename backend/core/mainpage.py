from flask import Blueprint, jsonify,redirect,url_for
import pg8000

mainpage_bp = Blueprint('mainpage', __name__)


def get_db_connection():
    return pg8000.connect(
        host="localhost",
        port=5432,
        database="course_management",
        user="postgres",
        password="12345"
    )


@mainpage_bp.route('/api/courses')
def get_courses():
    conn = None
    cursor = None

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
                SELECT 
                    course_id,
                    name,
                    teacher
                FROM courses
                ORDER BY course_id
            """)

    courses = cursor.fetchall()

    formatted_courses = []
    for course in courses:
        formatted_courses.append({
            'id': course[0],
            'course': course[1],
            'teacher': course[2]
        })
    cursor.close()
    conn.close()
    return jsonify(formatted_courses)

@mainpage_bp.route('/course/<int:course_id>')
def course_page(course_id):
    # Теперь перенаправляем на правильный маршрут в tasks
    return redirect(url_for('tasks.course_tasks', course_id=course_id))