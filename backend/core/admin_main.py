from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from core.connect import get_db_connection

admin_main = Blueprint('admin_main', __name__, url_prefix='/admin')


def get_courses(cur):
    cur.execute('SELECT course_id, name, teacher FROM courses ORDER BY course_id')
    rows = cur.fetchall()
    return [{'course_id': r[0], 'name': r[1], 'teacher': r[2]} for r in rows]


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


# /admin/admin_main — главная страница после входа
@admin_main.route('/admin_main')
def index():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('adminlogin.admin_login_page'))

    conn = get_db_connection()
    cur  = conn.cursor()
    courses  = get_courses(cur)
    teachers = get_teachers(cur)
    cur.close()
    conn.close()

    return render_template('admin_main.html',
                           courses=courses,
                           teachers=teachers,
                           selected=None,
                           user_name=session.get('user_name', 'Админ'))


# /admin/course/<id> — выбор курса
@admin_main.route('/course/<int:course_id>')
def course_detail(course_id):
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('adminlogin.admin_login_page'))

    conn = get_db_connection()
    cur  = conn.cursor()
    courses  = get_courses(cur)
    teachers = get_teachers(cur)

    cur.execute('SELECT course_id, name, teacher FROM courses WHERE course_id = %s', (course_id,))
    row      = cur.fetchone()
    selected = {'course_id': row[0], 'name': row[1], 'teacher': row[2]} if row else None

    cur.close()
    conn.close()

    return render_template('admin_main.html',
                           courses=courses,
                           teachers=teachers,
                           selected=selected,
                           user_name=session.get('user_name', 'Админ'))


# /admin/course/save — сохранение курса
@admin_main.route('/course/save', methods=['POST'])
def course_save():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        return redirect(url_for('adminlogin.admin_login_page'))

    name      = request.form.get('name', '').strip()
    teacher   = request.form.get('teacher', '').strip()
    course_id = request.form.get('course_id', '').strip()

    if not name or not teacher:
        flash('Заполните название и преподавателя.', 'error')
        return redirect(url_for('admin_main.index'))

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if course_id:
            cur.execute(
                'UPDATE courses SET name=%s, teacher=%s WHERE course_id=%s',
                (name, teacher, int(course_id))
            )
        else:
            cur.execute(
                'INSERT INTO courses (name, teacher) VALUES (%s, %s)',
                (name, teacher)
            )
        conn.commit()
        cur.close()
    finally:
        conn.close()

    flash(f'Курс «{name}» сохранён.', 'success')
    return redirect(url_for('admin_main.index'))


# /admin/course/delete — удаление курса
@admin_main.route('/course/delete', methods=['POST'])
def course_delete():
    if 'user_id' not in session or session.get('user_role') != 'admin':
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