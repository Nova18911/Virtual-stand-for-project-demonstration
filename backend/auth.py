from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from backend.core.connect import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@auth_bp.route('/api/login', methods=['POST'])
def login_api():
    data     = request.get_json()
    email    = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'ok': False, 'error': 'Заполните все поля.'}), 400

    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("""
            SELECT u.user_id, u.full_name, r.access_rights, p.password
            FROM users u
            JOIN passwords p ON p.login_id = u.login_id
            JOIN roles     r ON r.access_id = u.access_id
            WHERE p.login = %s
        """, (email,))
        row = cur.fetchone()
        conn.close()

    except Exception as e:
        return jsonify({'ok': False, 'error': f'Ошибка подключения к БД: {e}'}), 500

    if row is None or row[3] != password:
        return jsonify({'ok': False, 'error': 'Неверный логин или пароль.'}), 401

    user_id, full_name, role, _ = row

    if role == 'admin':
        return jsonify({'ok': False, 'error': 'Для входа администратора используйте специальную страницу.'}), 403

    session['user_id']   = user_id
    session['user_role'] = role
    session['user_name'] = full_name

    if role == 'teacher':
        redirect_url = url_for('mainpage.courses_page')
    else:
        redirect_url = url_for('mainpage.courses_page')

    return jsonify({'ok': True, 'redirect': redirect_url})

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))