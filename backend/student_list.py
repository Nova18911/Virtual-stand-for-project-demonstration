from flask import Blueprint, render_template, request, jsonify
from backend.core.connect import get_db_connection
from backend.core.runner import run_container, get_container_info, stop_container_by_project
import docker
from datetime import datetime

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

    return jsonify([{'user_id': row[0], 'full_name': row[1]} for row in students])


@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>', methods=['GET'])
def get_student_detail(lab_id, student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT project_id, github_link, grade, teacher_comment, build_info
        FROM student_projects 
        WHERE lab_id = %s AND user_id = %s
    """, (lab_id, student_id))
    project_row = cursor.fetchone()

    cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (student_id,))
    name_row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not name_row:
        return jsonify({'ok': False, 'error': 'Студент не найден'}), 404

    build_info = project_row[4] if project_row else ''

    build_success = bool(build_info and '[ОБРАЗ СОЗДАН]' in build_info)

    image_name = None
    main_file = 'main.py'

    if build_success:
        for line in build_info.split('\n'):
            if '[ИМЯ ОБРАЗА]' in line:
                image_name = line.split(']')[1].strip()
            elif '[ОСНОВНОЙ ФАЙЛ]' in line:
                main_file = line.split(']')[1].strip()

    return jsonify({
        'ok': True,
        'user_id': student_id,
        'full_name': name_row[0],
        'github_link': project_row[1] if project_row else '',
        'grade': project_row[2] if project_row else None,
        'teacher_comment': project_row[3] if project_row else '',
        'build_info': build_info,
        'project_id': project_row[0] if project_row else None,
        'build_success': build_success,
        'project_type': 'console',
        'main_file': main_file,
        'image_name': image_name
    })


def image_exists(image_name):
    try:
        client = docker.from_env()
        client.images.get(image_name)
        return True
    except docker.errors.ImageNotFound:
        return False
    except Exception as e:
        print(f"Ошибка проверки образа: {e}")
        return False


@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/build', methods=['POST'])
def build_container_compat(lab_id, student_id):
    from backend.core.docker.build_pipeline import build_and_run

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

    force_rebuild = request.args.get('force', 'false') == 'true'

    if force_rebuild:
        from backend.core.docker.build_pipeline import rebuild_project
        result = rebuild_project(github_url, project_id, image_name)
    else:
        result = build_and_run(github_url, project_id, image_name)

    if not result['ok']:
        return jsonify({'ok': False, 'error': result['error']}), 500

    return jsonify({'ok': True, 'link': result['link']})


@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/run', methods=['POST'])
def run_container_api(lab_id, student_id):
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

    build_info = project_row[1] or ''
    project_id = project_row[0]

    image_name = None
    main_file = 'main.py'

    for line in build_info.split('\n'):
        if '[ИМЯ ОБРАЗА]' in line:
            image_name = line.split(']')[1].strip()
        elif '[ОСНОВНОЙ ФАЙЛ]' in line:
            main_file = line.split(']')[1].strip()

    if not image_name:
        return jsonify({'ok': False, 'error': 'Образ не найден. Сначала соберите проект.'}), 404

    if not image_exists(image_name):
        return jsonify({'ok': False, 'error': f'Образ {image_name} не найден. Требуется пересборка.'}), 404

    container, link = run_container(image_name, project_id, 'console', main_file)

    if not container:
        return jsonify({'ok': False, 'error': 'Не удалось запустить контейнер'}), 500

    return jsonify({'ok': True, 'link': link, 'message': 'Контейнер запущен'})


@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/stop', methods=['POST'])
def stop_container_api(lab_id, student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT project_id FROM student_projects WHERE lab_id = %s AND user_id = %s",
                   (lab_id, student_id))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return jsonify({'ok': False, 'error': 'Проект не найден'}), 404

    success, message = stop_container_by_project(row[0])
    return jsonify({'ok': success, 'message': message})


@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/container-status', methods=['GET'])
def get_container_status(lab_id, student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT project_id FROM student_projects WHERE lab_id = %s AND user_id = %s",
                   (lab_id, student_id))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return jsonify({'ok': False, 'error': 'Проект не найден'}), 404

    container_info = get_container_info(row[0])
    return jsonify({'ok': True, 'container': container_info})


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


@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/comment', methods=['POST'])
def set_comment(lab_id, student_id):
    data = request.get_json()
    comment = data.get('comment', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE student_projects SET teacher_comment = %s
        WHERE lab_id = %s AND user_id = %s
    """, (comment, lab_id, student_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'ok': True})


@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/rebuild', methods=['POST'])
def rebuild_container(lab_id, student_id):
    from backend.core.docker.build_pipeline import rebuild_project

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT project_id, github_link FROM student_projects WHERE lab_id = %s AND user_id = %s",
                   (lab_id, student_id))
    project_row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not project_row:
        return jsonify({'ok': False, 'error': 'Работа студента не найдена'}), 404

    result = rebuild_project(project_row[1], project_row[0], f"student_{student_id}_lab_{lab_id}")
    if not result['ok']:
        return jsonify({'ok': False, 'error': result['error']}), 500

    return jsonify({'ok': True, 'link': result['link']})

@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/github', methods=['POST'])
def update_github_link(lab_id, student_id):
    data = request.get_json()
    new_github_link = data.get('github_link', '').strip()

    if not new_github_link:
        return jsonify({'ok': False, 'error': 'Ссылка на GitHub не может быть пустой'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE student_projects 
        SET github_link = %s, 
            build_info = NULL,      
            grade = NULL            
        WHERE lab_id = %s AND user_id = %s
    """, (new_github_link, lab_id, student_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'ok': True, 'message': 'Ссылка обновлена. При следующей сборке будет использована новая версия.'})