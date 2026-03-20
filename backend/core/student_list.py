import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Blueprint, render_template, request, redirect, url_for
import pg8000
from docker.runner import run_container, get_container_info

task_detail_bp = Blueprint('task_detail', __name__)  #хз никак docker.runner в Blueprint-е не смог передать ошибку выдаёт


def get_db_connection():
    return pg8000.connect(
        host="localhost",
        port=5432,
        database="course_management",
        user="postgres",
        password="12345678"
    )


@task_detail_bp.route('/task/<int:lab_id>')
def task_detail(lab_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем данные задания
    cursor.execute("""
        SELECT lab_id, name
        FROM labs
        WHERE lab_id = %s
    """, (lab_id,))
    lab_row = cursor.fetchone()

    if not lab_row:
        cursor.close()
        conn.close()
        return "Задание не найдено", 404

    lab = {'lab_id': lab_row[0], 'name': lab_row[1]}

    # Получаем список студентов записанных на этот курс
    cursor.execute("""
        SELECT u.user_id, u.full_name
        FROM users u
        JOIN course_user cu ON cu.user_id = u.user_id
        JOIN labs l ON l.course_id = cu.course_id
        JOIN roles r ON r.access_id = u.access_id
        WHERE l.lab_id = %s
          AND r.access_rights = 'student'
        ORDER BY u.full_name
    """, (lab_id,))
    students_rows = cursor.fetchall()

    students = [{'user_id': row[0], 'full_name': row[1]} for row in students_rows]

    cursor.close()
    conn.close()

    # Открываем первого студента по умолчанию
    first_student = None
    if students:
        return redirect(url_for('task_detail.task_detail_student',
                                lab_id=lab_id,
                                student_id=students[0]['user_id']))

    return render_template('student_list.html',
                           lab=lab,
                           students=students,
                           selected_student=first_student,
                           selected_student_id=None)


@task_detail_bp.route('/task/<int:lab_id>/student/<int:student_id>')
def task_detail_student(lab_id, student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем данные задания
    cursor.execute("""
        SELECT lab_id, name
        FROM labs
        WHERE lab_id = %s
    """, (lab_id,))
    lab_row = cursor.fetchone()

    if not lab_row:
        cursor.close()
        conn.close()
        return "Задание не найдено", 404

    lab = {'lab_id': lab_row[0], 'name': lab_row[1]}

    # Получаем список всех студентов курса
    cursor.execute("""
        SELECT u.user_id, u.full_name
        FROM users u
        JOIN course_user cu ON cu.user_id = u.user_id
        JOIN labs l ON l.course_id = cu.course_id
        JOIN roles r ON r.access_id = u.access_id
        WHERE l.lab_id = %s
          AND r.access_rights = 'student'
        ORDER BY u.full_name
    """, (lab_id,))
    students_rows = cursor.fetchall()
    students = [{'user_id': row[0], 'full_name': row[1]} for row in students_rows]

    # Получаем работу выбранного студента
    cursor.execute("""
        SELECT sp.github_link,
               sp.grade,
               sp.teacher_comment
        FROM student_projects sp
        WHERE sp.lab_id = %s
          AND sp.user_id = %s
    """, (lab_id, student_id))
    project_row = cursor.fetchone()

    # Получаем имя выбранного студента
    cursor.execute("""
        SELECT full_name FROM users WHERE user_id = %s
    """, (student_id,))
    student_name_row = cursor.fetchone()

    cursor.execute("""
                SELECT project_id FROM student_projects
                WHERE lab_id = %s AND user_id = %s
            """, (lab_id, student_id))
    project_id_row = cursor.fetchone()
    project_id = project_id_row[0] if project_id_row else None

    cursor.close()
    conn.close()

    if not student_name_row:
        return "Студент не найден", 404

    selected_student = {
        'user_id': student_id,
        'full_name': student_name_row[0],
        'github_link': project_row[0] if project_row else '',
        'docker_link': '',  # будет добавлено позже
        'grade': project_row[1] if project_row else None,
        'teacher_comment': project_row[2] if project_row else ''
    }

    # Получаем информацию о контейнере
    container_info = get_container_info(project_id) if project_id else None

    return render_template('student_list.html',
                           lab=lab,
                           students=students,
                           selected_student=selected_student,
                           selected_student_id=student_id,
                           container_info=container_info)


@task_detail_bp.route('/task/<int:lab_id>/student/<int:student_id>/build', methods=['POST'])
def build_container(lab_id, student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT project_id, github_link
        FROM student_projects
        WHERE lab_id = %s AND user_id = %s
    """, (lab_id, student_id))
    project_row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not project_row:
        return "Работа студента не найдена", 404

    project_id = project_row[0]
    github_link = project_row[1]
    image_name = f"student_{student_id}_lab_{lab_id}"

    container, link = run_container(image_name, project_id)

    if not container:
        return "Ошибка при запуске контейнера", 500

    return redirect(url_for('task_detail.task_detail_student',
                            lab_id=lab_id,
                            student_id=student_id))

@task_detail_bp.route('/task/<int:lab_id>/student/<int:student_id>/grade', methods=['POST'])
def set_grade(lab_id, student_id):
    grade = int(request.form.get('grade'))
    conn = get_db_connection()
    cursor = conn.cursor()

    # Обновляем оценку если запись уже есть
    cursor.execute("""
        UPDATE student_projects
        SET grade = %s,
            grade_date = CURRENT_TIMESTAMP
        WHERE lab_id = %s AND user_id = %s
    """, (grade, lab_id, student_id))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('task_detail.task_detail_student',
                            lab_id=lab_id,
                            student_id=student_id))


@task_detail_bp.route('/task/<int:lab_id>/student/<int:student_id>/comment', methods=['POST'])
def set_comment(lab_id, student_id):
    comment = request.form.get('teacher_comment')
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

    return redirect(url_for('task_detail.task_detail_student',
                            lab_id=lab_id,
                            student_id=student_id))


if __name__ == '__main__':
    from flask import Flask
    import os

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    templates = os.path.join(base_dir, 'frontend', 'templates')
    static = os.path.join(base_dir, 'frontend', 'static')

    app = Flask(__name__,
                template_folder=templates,
                static_folder=static)
    app.config['SECRET_KEY'] = 'test-secret-key-12345'
    app.register_blueprint(task_detail_bp)
    app.run(debug=True)