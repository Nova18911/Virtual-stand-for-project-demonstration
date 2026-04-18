from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import pg8000
from backend.core.connect import get_db_connection
from datetime import datetime

task_bp = Blueprint('task', __name__, url_prefix='/tasks')

def ensure_datetime(date_val):
    if not date_val:
        return datetime.now()
    
    if isinstance(date_val, datetime):
        return date_val
    
    if isinstance(date_val, str):
        date_str = date_val.strip()
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d'
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str[:19] if len(date_str) > 19 else date_str, fmt)
            except (ValueError, TypeError):
                continue

    return datetime.now()

def dict_fetchone(cursor):
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))

def dict_fetchall(cursor):
    rows = cursor.fetchall()
    if not rows:
        return []
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


@task_bp.route('/<int:lab_id>')
def index(lab_id):
    role = session.get('user_role', 'student')
    user_id = session.get('user_id')

    conn = get_db_connection()
    try:
        cur = conn.cursor()

        cur.execute('''
            SELECT l.lab_id, l.name, l.task, l.start_date, l.end_date, l.course_id
            FROM labs l
            WHERE l.lab_id = %s
        ''', (lab_id,))
        lab = dict_fetchone(cur)

        if lab is None:
            return 'Задание не найдено', 404

        lab['start_date'] = ensure_datetime(lab.get('start_date'))
        lab['end_date'] = ensure_datetime(lab.get('end_date'))

        course_id = lab.get('course_id')
        if course_id:
            session['current_course_id'] = course_id
        else:
            course_id = session.get('current_course_id', 1)

        project = None
        if role == 'student' and user_id:
            cur.execute('''
                SELECT project_id, github_link, grade, teacher_comment, submission_date
                FROM student_projects
                WHERE lab_id = %s AND user_id = %s
            ''', (lab_id, user_id))
            project = dict_fetchone(cur)
            if project:
                project['submission_date'] = ensure_datetime(project.get('submission_date'))

        students = None
        if role == 'teacher':
            cur.execute('''
                SELECT sp.project_id, sp.github_link, sp.grade,
                       sp.teacher_comment, sp.submission_date,
                       u.full_name
                FROM student_projects sp
                JOIN users u ON sp.user_id = u.user_id
                WHERE sp.lab_id = %s
                ORDER BY sp.submission_date DESC
            ''', (lab_id,))
            students = dict_fetchall(cur)
            for s in students:
                s['submission_date'] = ensure_datetime(s.get('submission_date'))

    finally:
        conn.close()

    return render_template('task.html',
                           lab=lab,
                           project=project,
                           students=students,
                           role=role,
                           course_id=course_id)

@task_bp.route('/<int:lab_id>/submit', methods=['POST'])
def submit(lab_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    github_link = request.form.get('answer_url', '').strip()
    if not github_link:
        flash('Введите ссылку на репозиторий.', 'error')
        return redirect(url_for('task.index', lab_id=lab_id))

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT project_id FROM student_projects WHERE lab_id = %s AND user_id = %s', (lab_id, user_id))
        existing = dict_fetchone(cur)

        if existing:
            cur.execute('''
                UPDATE student_projects
                SET github_link = %s, submission_date = CURRENT_TIMESTAMP
                WHERE lab_id = %s AND user_id = %s
            ''', (github_link, lab_id, user_id))
        else:
            cur.execute('''
                INSERT INTO student_projects (user_id, lab_id, github_link)
                VALUES (%s, %s, %s)
            ''', (user_id, lab_id, github_link))

        conn.commit()
        flash('Ссылка сохранена.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Ошибка: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('task.index', lab_id=lab_id))

@task_bp.route('/<int:lab_id>/grade', methods=['POST'])
def grade(lab_id):
    if session.get('user_role') != 'teacher':
        flash('Недостаточно прав.', 'error')
        return redirect(url_for('task.index', lab_id=lab_id))

    project_id = request.form.get('project_id')
    grade_val = request.form.get('grade', '').strip()
    comment = request.form.get('comment', '').strip()

    if grade_val:
        try:
            g = int(grade_val)
            if g < 2 or g > 5:
                flash('Оценка от 2 до 5.', 'error')
                return redirect(url_for('task.index', lab_id=lab_id))
        except ValueError:
            flash('Оценка должна быть числом.', 'error')
            return redirect(url_for('task.index', lab_id=lab_id))

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            UPDATE student_projects
            SET grade = %s, teacher_comment = %s, grade_date = CURRENT_TIMESTAMP
            WHERE project_id = %s
        ''', (int(grade_val) if grade_val else None, comment, project_id))
        conn.commit()
        flash('Оценка сохранена.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Ошибка: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('task.index', lab_id=lab_id))