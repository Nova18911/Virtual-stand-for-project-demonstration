from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import pg8000

logadm_bp = Blueprint('adminlogin', __name__)


def get_db_connection():
    return pg8000.connect(
        host="127.0.0.1",
        port=5432,
        database="course_management",
        user="postgres",
        password="12345678"
    )


@logadm_bp.route('/loginadmin', methods=['GET', 'POST'])
def admin_login_page():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Заполните все поля.', 'error')
            return redirect(url_for('adminlogin.admin_login_page'))

        conn = None
        cursor = None

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT u.user_id, u.full_name, u.access_id, 
                       p.login, p.password,
                       r.access_rights
                FROM users u
                JOIN passwords p ON u.login_id = p.login_id
                JOIN roles r ON u.access_id = r.access_id
                WHERE p.login = %s AND r.access_rights = 'admin'
            """, (email,))

            user = cursor.fetchone()

            if user is None:
                flash('Неверный логин или пароль.', 'error')
                return redirect(url_for('adminlogin.admin_login_page'))

            user_id, full_name, access_id, db_login, db_password, role = user

            if password != db_password:
                flash('Неверный пароль.', 'error')
                return redirect(url_for('adminlogin.admin_login_page'))

            session.clear()
            session['user_id'] = user_id
            session['user_role'] = role
            session['user_name'] = full_name
            session['user_login'] = email
            session.permanent = True

            session.pop('_flashes', None)
            return redirect(url_for('admin_main.index'))

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template('adminlogin.html')