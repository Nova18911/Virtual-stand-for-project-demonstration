from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)

# Тестовые пользователи (заглушка вместо БД)
MOCK_USERS = {
    'student@mail.ru': {
        'id': 1,
        'full_name': 'Иван Студентов',
        'password_hash': generate_password_hash('student123'),
        'role': 'student',
        'is_approved': True,
    },
    'teacher@mail.ru': {
        'id': 2,
        'full_name': 'Пётр Преподавателев',
        'password_hash': generate_password_hash('teacher123'),
        'role': 'teacher',
        'is_approved': True,
    },
}


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Заполните все поля.', 'error')
            return render_template('login.html')

        user = MOCK_USERS.get(email)

        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Неверный логин или пароль.', 'error')
            return render_template('login.html')

        # Преподаватель без одобрения — не пускаем
        if user['role'] == 'teacher' and not user['is_approved']:
            flash('Ваша учётная запись ещё не одобрена администратором.', 'error')
            return render_template('login.html')

        session['user_id'] = user['id']
        session['user_role'] = user['role']
        session['user_name'] = user['full_name']

        if user['role'] == 'admin':
            return redirect(url_for('admin.index'))
        return redirect(url_for('main.index'))

    return render_template('login.html')


auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))