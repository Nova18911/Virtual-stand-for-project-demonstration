from flask import Flask, render_template, request, jsonify

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')


@app.route('/inputcode')
def inputcode_page():
    return render_template('input_code.html')


# Добавим обработчик POST запроса
@app.route('/inputcode', methods=['POST'])
def verify_code():
    # Собираем все поля кода
    code = ''.join([
        request.form.get('input_code1', ''),
        request.form.get('input_code2', ''),
        request.form.get('input_code3', ''),
        request.form.get('input_code4', ''),
        request.form.get('input_code5', ''),
        request.form.get('input_code6', '')
    ])

    print(f"Получен код: {code}")

    # Здесь будет логика проверки кода
    # Например, перенаправление на страницу смены пароля
    return jsonify({
        'success': True,
        'message': 'Код принят',
        'code': code,
        'redirect': '/change-password'  # URL для перенаправления
    })


# Добавим заглушку для страницы смены пароля
@app.route('/change-password')
def change_password():
    return "Страница смены пароля (в разработке)"


if __name__ == '__main__':
    app.run(debug=True)