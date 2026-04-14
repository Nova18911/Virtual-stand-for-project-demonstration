from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from backend.core.connect import get_db_connection

admin_main = Blueprint('admin_main', __name__, url_prefix='/admin')


def rows_to_dicts(cursor, rows):
    if rows is None:
        return None
    cols = [desc[0] for desc in cursor.description]
    return [dict(zip(cols, row)) for row in rows]


def row_to_dict(cursor, row):
    if row is None:
        return None
    cols = [desc[0] for desc in cursor.description]
    return dict(zip(cols, row))


def get_courses(cur):
    cur.execute('SELECT course_id, name, teacher, teacher_id FROM courses ORDER BY course_id')
    rows = cur.fetchall()
    return [{'course_id': r[0], 'name': r[1], 'teacher': r[2], 'teacher_id': r[3]} for r in rows]


def get_teachers(cur):
    cur.execute("""
        SELECT u.user_id, u.full_name
        FROM users u
        JOIN roles r ON u.access_id = r.access_id
        WHERE r.access_rights = 'teacher'
        ORDER BY u.full_name
    """)
    rows = cur.fetchall()
    return [{'user_id': r[0], 'full_name': r[1]} for r in rows]


def require_admin():
    return 'user_id' not in session or session.get('user_role') != 'admin'


@admin_main.route('/admin_main')
def index():
    if require_admin():
        return redirect(url_for('adminlogin.admin_login_page'))

    conn = get_db_connection()
    cur = conn.cursor()
    courses = get_courses(cur)
    teachers = get_teachers(cur)
    cur.close()
    conn.close()

    return render_template('admin_main.html',
                           courses=courses,
                           teachers=teachers,
                           selected=None,
                           user_name=session.get('user_name', 'Админ'))


@admin_main.route('/course/<int:course_id>')
def course_detail(course_id):
    if require_admin():
        return redirect(url_for('adminlogin.admin_login_page'))

    conn = get_db_connection()
    cur = conn.cursor()
    courses = get_courses(cur)
    teachers = get_teachers(cur)

    cur.execute('SELECT course_id, name, teacher, teacher_id FROM courses WHERE course_id = %s', (course_id,))
    row = cur.fetchone()
    selected = {'course_id': row[0], 'name': row[1], 'teacher': row[2], 'teacher_id': row[3]} if row else None

    cur.close()
    conn.close()

    return render_template('admin_main.html',
                           courses=courses,
                           teachers=teachers,
                           selected=selected,
                           user_name=session.get('user_name', 'Админ'))


@admin_main.route('/course/save', methods=['POST'])
def course_save():
    if require_admin():
        return redirect(url_for('adminlogin.admin_login_page'))

    name = request.form.get('name', '').strip()
    teacher_id = request.form.get('teacher_id', '').strip()
    course_id = request.form.get('course_id', '').strip()

    if not name or not teacher_id:
        flash('Заполните название и выберите преподавателя.', 'error')
        return redirect(url_for('admin_main.index'))

    conn = get_db_connection()
    try:
        cur = conn.cursor()

        # Получаем имя преподавателя по его user_id
        cur.execute('SELECT full_name FROM users WHERE user_id = %s', (int(teacher_id),))
        row = cur.fetchone()
        teacher_name = row[0] if row else ''

        if course_id:
            cur.execute(
                'UPDATE courses SET name=%s, teacher=%s, teacher_id=%s WHERE course_id=%s',
                (name, teacher_name, int(teacher_id), int(course_id))
            )
        else:
            cur.execute(
                'INSERT INTO courses (name, teacher, teacher_id) VALUES (%s, %s, %s)',
                (name, teacher_name, int(teacher_id))
            )
        conn.commit()
        cur.close()
    finally:
        conn.close()

    flash(f'Курс «{name}» сохранён.', 'success')
    return redirect(url_for('admin_main.index'))


@admin_main.route('/course/delete', methods=['POST'])
def course_delete():
    if require_admin():
        return redirect(url_for('adminlogin.admin_login_page'))

    course_id = request.form.get('course_id', '').strip()
    if not course_id:
        return redirect(url_for('admin_main.index'))

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM courses WHERE course_id=%s', (int(course_id),))
        conn.commit()
        cur.close()
    finally:
        conn.close()

    flash('Курс удалён.', 'success')
    return redirect(url_for('admin_main.index'))