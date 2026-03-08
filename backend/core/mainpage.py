from flask import Blueprint, jsonify
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
        course_id, course_name, teacher = course

        cursor.execute("""
                    SELECT 
                        name,
                        task,
                        end_date
                    FROM labs
                    WHERE course_id = %s
                    ORDER BY start_date DESC
                """, (course_id,))

        labs = cursor.fetchall()

        if labs:
            for lab in labs:
                lab_name, task, end_date = lab

                deadline_str = end_date.strftime('%Y-%m-%d') if end_date else None

                course_item = {
                    "course": course_name,
                    "work": lab_name,
                    "teacher": teacher
                }

                if task:
                    course_item["description"] = task
                if deadline_str:
                    course_item["deadline"] = deadline_str

                formatted_courses.append(course_item)
        else:
            course_item = {
                "course": course_name,
                "work": "Нет работ",
                "teacher": teacher
            }
            formatted_courses.append(course_item)
            cursor.close()
            conn.close()
    return jsonify(formatted_courses)















