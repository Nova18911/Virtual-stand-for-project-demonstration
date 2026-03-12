from flask import Flask, render_template, request

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')


# Главная страница
@app.route('/')
def index():
    return "Главная страница (в разработке)"


# Страница смены пароля
@app.route('/changepassword')
def newpassword():
    return render_template('change_password.html')


# Обработчик отправки формы
@app.route('/newpassword', methods=['POST'])
def change_password():
    # Получаем данные из формы
    new_password = request.form.get('newpassword')
    password_ver = request.form.get('passwrdver')

    print(f"Получен новый пароль: {new_password}")
    print(f"Подтверждение пароля: {password_ver}")

    # Здесь будет логика сохранения пароля
    return "Пароль получен. Перенаправление на главную..."


# Маршрут для перенаправления после сохранения
@app.route('/main')
def main_page():
    return "Главная страница после смены пароля"


if __name__ == '__main__':
    app.run(debug=True)