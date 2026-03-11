from flask import Flask, render_template, request, redirect, url_for, flash
import re
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
users_db = {
    "ivan@student.ru": {
        "name": "Иван Студентов",
        "registered": "2024-01-15",
        "reset_token": None,
        "token_expiry": None
    }
}


def is_valid_email(email):
    """Проверка корректности email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_reset_token():
    """Генерация уникального токена для сброса пароля"""
    return secrets.token_urlsafe(32)


@app.route('/')
def index():
    """Главная страница с формой восстановления пароля"""
    return render_template('index.html')


@app.route('/recovery', methods=['POST'])
def recovery():
    """Обработка запроса на восстановление пароля"""
    email = request.form.get('email', '').strip().lower()

    if not email:
        flash('Пожалуйста, введите email', 'error')
        return redirect(url_for('index'))

    if not is_valid_email(email):
        flash('Пожалуйста, введите корректный email адрес', 'error')
        return redirect(url_for('index'))
    if email in users_db:
        token = generate_reset_token()
        users_db[email]['reset_token'] = token
        users_db[email]['token_expiry'] = datetime.now() + timedelta(hours=24)

        reset_link = url_for('reset_password', token=token, _external=True)
        print(f"\n=== Ссылка для сброса пароля для {email} ===")
        print(f"Имя пользователя: {users_db[email]['name']}")
        print(f"Ссылка: {reset_link}")
        print(f"Срок действия: 24 часа\n")

        flash('Инструкции по восстановлению пароля отправлены на ваш email', 'success')
    else:
        flash('Если указанный email зарегистрирован, мы отправили на него инструкции', 'success')

    return redirect(url_for('index'))


@app.route('/reset/<token>')
def reset_password(token):
    """Страница сброса пароля (переход по ссылке из письма)"""
    for email, user_data in users_db.items():
        if user_data.get('reset_token') == token:
            if user_data.get('token_expiry') and datetime.now() < user_data['token_expiry']:
                return f"""
                <h2>Сброс пароля для {user_data['name']}</h2>
                <p>Здесь должна быть форма для ввода нового пароля</p>
                <p>Email: {email}</p>
                <p><small>Токен действителен до: {user_data['token_expiry']}</small></p>
                <p><a href='/'>← Вернуться на главную</a></p>
                """
            else:
                return """
                <h2>Срок действия ссылки истек</h2>
                <p>Запросите восстановление пароля снова</p>
                <p><a href='/'>← Вернуться на главную</a></p>
                """, 400

    return """
    <h2>Недействительная ссылка</h2>
    <p>Запросите восстановление пароля снова</p>
    <p><a href='/'>← Вернуться на главную</a></p>
    """, 404


if __name__ == '__main__':
    print("=" * 50)
    print("Сервер запущен!")
    print("Для тестирования используйте email: ivan@student.ru")
    print("Ссылки для сброса пароля будут появляться в консоли")
    print("=" * 50)
    app.run(debug=True, port=5000)