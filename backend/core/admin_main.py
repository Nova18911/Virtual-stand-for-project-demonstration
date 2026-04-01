from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import pg8000

admin_main = Blueprint('admin_main', __name__, url_prefix='/admin')


def get_db():
    conn = pg8000.connect(
        host='127.0.0.1',
        port=5432,
        database='course_management',
        user='admin',
        password='12345678'
    )
    return conn


def rows_to_dicts(cursor, rows):
    """Converts a list of pg8000 row tuples to a list of dicts using cursor.description."""
    if rows is None:
        return None
    cols = [desc[0] for desc in cursor.description]
    return [dict(zip(cols, row)) for row in rows]


def row_to_dict(cursor, row):
    """Converts a single pg8000 row tuple to a dict."""
    if row is None:
        return None
    cols = [desc[0] for desc in cursor.description]
    return dict(zip(cols, row))

@admin_main.route('/admin/main')
def admin_main_page():
    return render_template('admin_main.html')

@admin_main.route('/admin_main')
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT course_id, name, teacher FROM courses ORDER BY course_id')
    courses = rows_to_dicts(cur, cur.fetchall())

    cur.execute('''
                SELECT u.user_id, u.full_name
                FROM users u
                JOIN roles r ON u.access_id = r.access_id
                WHERE r.access_rights = %s
                ORDER BY u.full_name
            ''', ('teacher',))
    teachers = rows_to_dicts(cur, cur.fetchall())
    conn.close()

    return render_template('admin_main.html',
                       courses=courses,
                       teachers=teachers,
                       selected=None,
                       user_name=session.get('user_name', 'Админ'))



@admin_main.route('/course/<int:course_id>')
def course_detail(course_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT course_id, name, teacher FROM courses ORDER BY course_id')
    courses = rows_to_dicts(cur, cur.fetchall())

    cur.execute('SELECT course_id, name, teacher FROM courses WHERE course_id = %s', (course_id,))
    selected = row_to_dict(cur, cur.fetchone())

    cur.execute('''
                SELECT u.user_id, u.full_name
                FROM users u
                JOIN roles r ON u.access_id = r.access_id
                WHERE r.access_rights = %s
                ORDER BY u.full_name
            ''', ('teacher',))
    teachers = rows_to_dicts(cur, cur.fetchall())
    conn.close()

    return render_template('admin_main.html',
                           courses=courses,
                           teachers=teachers,
                           selected=selected,
                           user_name=session.get('user_name', 'Админ'))


@admin_main.route('/course/save', methods=['POST'])
def course_save():
    name = request.form.get('name', '').strip()
    teacher = request.form.get('teacher', '').strip()
    course_id = request.form.get('course_id', '').strip()

    if not name or not teacher:
        flash('Заполните название и преподавателя.', 'error')
        return redirect(url_for('admin_main.index'))

    conn = get_db()
    try:
        cur = conn.cursor()
        if course_id:
            # Обновляем существующий курс
            cur.execute('UPDATE courses SET name = %s, teacher = %s WHERE course_id = %s',
                        (name, teacher, course_id))
        else:
            # Создаём новый курс
            cur.execute('INSERT INTO courses (name, teacher) VALUES (%s, %s)', (name, teacher))
        conn.commit()
    finally:
        conn.close()

    flash(f'Курс «{name}» сохранён.', 'success')
    return redirect(url_for('admin_main.index'))


@admin_main.route('/course/delete', methods=['POST'])
def course_delete():
    course_id = request.form.get('course_id', '').strip()
    if not course_id:
        return redirect(url_for('admin_main.index'))

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM courses WHERE course_id = %s', (course_id,))
        conn.commit()
    finally:
        conn.close()

    flash('Курс удалён.', 'success')
    return redirect(url_for('admin_main.index'))