from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from core.connect import get_db_connection
import sys
import os
from datetime import datetime

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from backend.core.docker.git_clone import clone_repo
from backend.core.docker.project_analyzer import analyze_project, update_requirements_file
from backend.core.docker.create_dockerfile import (create_dockerfile,create_dockerignore,build_docker_image,save_requirements_file)
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
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sp.project_id, sp.github_link, sp.grade, sp.teacher_comment
        FROM student_projects sp
        WHERE sp.lab_id = %s AND sp.user_id = %s
    """, (lab_id, student_id))
    project_row = cursor.fetchone()

    cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (student_id,))
    name_row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not name_row:
        return jsonify({'ok': False, 'error': 'Студент не найден'}), 404

    # Извлекаем информацию из комментария
    comment = project_row[3] if project_row else ''
    build_success = '[СКЛОНИРОВАНО' in comment
    project_type = None
    main_file = None

    if build_success:
        for line in comment.split('\n'):
            if '[ТИП ПРОЕКТА]' in line:
                project_type = line.split(']')[1].strip()
            elif '[ОСНОВНОЙ ФАЙЛ]' in line:
                main_file = line.split(']')[1].strip()

    return jsonify({
        'ok': True,
        'user_id': student_id,
        'full_name': name_row[0],
        'github_link': project_row[1] if project_row else '',
        'grade': project_row[2] if project_row else None,
        'teacher_comment': comment,
        'project_id': project_row[0] if project_row else None,
        'build_success': build_success,
        'project_type': project_type,
        'main_file': main_file
    })


# --- API: сборка контейнера ---
@task_detail_bp.route('/api/task/<int:lab_id>/student/<int:student_id>/build', methods=['POST'])
def build_container(lab_id, student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT project_id, github_link FROM student_projects
            WHERE lab_id = %s AND user_id = %s
        """, (lab_id, student_id))
        project_row = cursor.fetchone()

        if not project_row:
            return jsonify({'ok': False, 'error': 'Работа студента не найдена'}), 404

        project_id = project_row[0]
        github_url = project_row[1]

        if not github_url:
            return jsonify({'ok': False, 'error': 'GitHub ссылка не указана'}), 400

        # 1. Клонируем репозиторий
        clone_result = clone_repo(github_url)

        if not clone_result['success']:
            return jsonify({'ok': False, 'error': clone_result['error']}), 500

        repo_path = clone_result['path']

        # 2. Анализируем проект
        analysis = analyze_project(repo_path)

        if analysis['error']:
            return jsonify({'ok': False, 'error': f'Ошибка анализа: {analysis["error"]}'}), 500

        # 3. СОЗДАЕМ requirements.txt
        req_path = os.path.join(repo_path, 'requirements.txt')
        if not os.path.exists(req_path):
            # Если файла нет - создаем из зависимостей
            if not update_requirements_file(repo_path, analysis['requirements']):
                return jsonify({'ok': False, 'error': 'Не удалось создать requirements.txt'}), 500
            print(f"✅ requirements.txt создан: {req_path}")
        else:
            # Если файл есть - обновляем, добавляя новые зависимости
            if not update_requirements_file(repo_path, analysis['requirements']):
                return jsonify({'ok': False, 'error': 'Не удалось обновить requirements.txt'}), 500
            print(f"✅ requirements.txt обновлен: {req_path}")

        # 4. Создаем .dockerignore
        dockerignore_result = create_dockerignore(repo_path)
        if not dockerignore_result['success']:
            return jsonify({'ok': False, 'error': dockerignore_result['error']}), 500

        # 5. Создаем Dockerfile
        dockerfile_result = create_dockerfile(
            repo_path,
            analysis['project_type'],
            analysis['main_file']
        )

        if not dockerfile_result['success']:
            return jsonify({'ok': False, 'error': dockerfile_result['error']}), 500

        image_name = f"student_{student_id}_lab_{lab_id}"
        build_result = build_docker_image(repo_path, image_name)

        if not build_result['success']:
            # Логируем ошибку для отладки
            print(f"Docker build error: {build_result['error']}")
            return jsonify({'ok': False, 'error': build_result['error']}), 500

        # 7. Формируем отчет (обновленная версия)
        report = f"""
        [СКЛОНИРОВАНО {datetime.now()}] {repo_path}
        [ТИП ПРОЕКТА] {analysis['project_type']}
        [ОСНОВНОЙ ФАЙЛ] {analysis['main_file'] if analysis['main_file'] else 'не найден'}
        [ЗАВИСИМОСТИ] {', '.join(analysis['requirements'][:10])}{'...' if len(analysis['requirements']) > 10 else ''}
        [СОБРАН ОБРАЗ] {image_name}
        [РАЗМЕР ОБРАЗА] {build_result.get('image_size', 0):.2f} MB
        [DOCKERFILE] {dockerfile_result['path']}
        """

        # 8. Сохраняем отчет в комментарий
        cursor.execute("""
            UPDATE student_projects
            SET teacher_comment = COALESCE(teacher_comment, '') || %s
            WHERE project_id = %s
        """, (report, project_id))
        conn.commit()

        return jsonify({
            'ok': True,
            'analysis': {
                'project_type': analysis.get('project_type'),
                'main_file': analysis.get('main_file'),
                'requirements_count': len(analysis.get('requirements', [])),
                'image_name': image_name
            }
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'ok': False, 'error': f'Ошибка: {str(e)}'}), 500

    finally:
        cursor.close()
        conn.close()


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