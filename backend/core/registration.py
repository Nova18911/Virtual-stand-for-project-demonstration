from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from backend.core.connect import get_db_connection
import re

register_bp = Blueprint('register', __name__)

def is_valid_fio(fio: str) -> bool:
    parts = fio.strip().split()
    if len(parts) < 2:
        return False
    return all(re.match(r'^[А-ЯЁа-яё\-]+$', part) for part in parts)

def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email))

@register_bp.route('/register', methods=['GET'])
def register():
    return render_template('registration.html')

@register_bp.route('/api/register', methods=['POST'])
def register_api():
    data     = request.get_json()
    email    = data.get('email', '').strip()
    fio      = data.get('fio', '').strip()
    password = data.get('password', '').strip()
    role     = data.get('role', 'student')

    if not is_valid_fio(fio):
        return jsonify({'ok': False, 'error': 'ФИО должно содержать минимум два слова и только кириллические буквы.'}), 400

    if not is_valid_email(email):
        return jsonify({'ok': False, 'error': 'Введите корректный адрес электронной почты.'}), 400

    if len(password) < 4:
        return jsonify({'ok': False, 'error': 'Пароль должен содержать минимум 4 символа.'}), 400

    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("SELECT login_id FROM passwords WHERE login = %s", (email,))
        if cur.fetchone():
            conn.close()
            return jsonify({'ok': False, 'error': 'Пользователь с таким email уже зарегистрирован.'}), 400

        cur.execute("SELECT access_id FROM roles WHERE access_rights = %s", (role,))
        role_row = cur.fetchone()
        if not role_row:
            conn.close()
            return jsonify({'ok': False, 'error': 'Роль не найдена.'}), 400
        access_id = role_row[0]

        cur.execute(
            "INSERT INTO passwords (login, password) VALUES (%s, %s) RETURNING login_id",
            (email, password)
        )
        login_id = cur.fetchone()[0]

        if role == 'teacher':
            cur.execute(
                """INSERT INTO users (full_name, access_id, login_id, is_approved)
                   VALUES (%s, %s, %s, false) RETURNING user_id""",
                (fio, access_id, login_id)
            )
        else:
            cur.execute(
                """INSERT INTO users (full_name, access_id, login_id)
                   VALUES (%s, %s, %s) RETURNING user_id""",
                (fio, access_id, login_id)
            )

        conn.commit()
        conn.close()

    except Exception as e:
        return jsonify({'ok': False, 'error': f'Ошибка при регистрации: {e}'}), 500

    if role == 'teacher':
        return jsonify({'ok': True, 'redirect': None}), 200
    else:
        return jsonify({'ok': True, 'redirect': url_for('auth.login')}), 200