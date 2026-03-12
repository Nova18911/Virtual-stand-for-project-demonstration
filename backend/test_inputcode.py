from flask import Flask, render_template, request, jsonify, url_for

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')


# Добавьте этот маршрут для проверки статических файлов
@app.route('/test-static')
def test_static():
    css_url = url_for('static', filename='css/input_code.css')
    js_url = url_for('static', filename='js/input_code.js')
    return f'''
    CSS URL: {css_url}<br>
    JS URL: {js_url}<br>
    <a href="{css_url}">Проверить CSS</a><br>
    <a href="{js_url}">Проверить JS</a>
    '''


@app.route('/inputcode')
def inputcode_page():
    return render_template('input_code.html')


@app.route('/inputcode', methods=['POST'])
def verify_code():
    code = ''.join([
        request.form.get('input_code1', ''),
        request.form.get('input_code2', ''),
        request.form.get('input_code3', ''),
        request.form.get('input_code4', ''),
        request.form.get('input_code5', ''),
        request.form.get('input_code6', '')
    ])

    print(f"Получен код: {code}")

    # Проверяем код
    if code == '123456':
        return jsonify({
            'success': True,
            'message': 'Код верный',
            'redirect': '/change-password'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Неверный код'
        }), 400


@app.route('/change-password')
def change_password():
    return "Страница смены пароля"


if __name__ == '__main__':
    app.run(debug=True)