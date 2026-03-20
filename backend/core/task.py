from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import pg8000

task_bp = Blueprint('task', __name__, url_prefix='/tasks')


def get_db():
    conn = pg8000.connect(
        host='127.0.0.1',
        port=5432,
        database='course_management',
        user='postgres',
        password='12345'
    )
    def dict_row(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col.name] = row[idx]
        return d

    conn.row_factory = dict_row
    return conn

@task_bp.route('/<int:lab_id>')
def index(lab_id):
    role = session.get('user_role', 'student')
    user_id = session.get('user_id')

    conn = get_db()
    try:
        cur = conn.cursor()

        # Получаем данные задания из labs
        cur.execute('''
            SELECT l.lab_id, l.name, l.task, l.start_date, l.end_date
            FROM labs l
            WHERE l.lab_id = %s
        ''', (lab_id,))
        lab = cur.fetchone()

        if lab is None:
            return 'Задание не найдено', 404

        # Получаем ответ студента из student_projects
        project = None
        if role == 'student' and user_id:
            cur.execute('''
                SELECT project_id, github_link, grade, teacher_comment, submission_date
                FROM student_projects
                WHERE lab_id = %s AND user_id = %s
            ''', (lab_id, user_id))
            project = cur.fetchone()

        # Преподаватель видит все ответы студентов
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
            students = cur.fetchall()

    finally:
        conn.close()

    return render_template('task.html',
                           lab=lab,
                           project=project,
                           students=students,
                           role=role)


@task_bp.route('/<int:lab_id>/submit', methods=['POST'])
def submit(lab_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    github_link = request.form.get('answer_url', '').strip()
    if not github_link:
        flash('Введите ссылку на репозиторий.', 'error')
        return redirect(url_for('task.index', lab_id=lab_id))

    conn = get_db()
    try:
        cur = conn.cursor()

        # Если ответ уже есть — обновляем, иначе создаём
        cur.execute('''
            SELECT project_id FROM student_projects
            WHERE lab_id = %s AND user_id = %s
        ''', (lab_id, user_id))
        existing = cur.fetchone()

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
        flash(f'Ошибка при сохранении: {e}', 'error')
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

    # Проверка оценки: только 2-5 по структуре БД
    if grade_val:
        try:
            g = int(grade_val)
            if g < 2 or g > 5:
                flash('Оценка должна быть от 2 до 5.', 'error')
                return redirect(url_for('task.index', lab_id=lab_id))
        except ValueError:
            flash('Оценка должна быть числом.', 'error')
            return redirect(url_for('task.index', lab_id=lab_id))

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute('''
            UPDATE student_projects
            SET grade = %s,
                teacher_comment = %s,
                grade_date = CURRENT_TIMESTAMP
            WHERE project_id = %s
        ''', (int(grade_val) if grade_val else None, comment, project_id))
        conn.commit()
        flash('Оценка сохранена.', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Ошибка при сохранении оценки: {e}', 'error')
    finally:
        conn.close()

    return redirect(url_for('task.index', lab_id=lab_id))
