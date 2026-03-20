from flask import Blueprint, render_template, request, redirect, url_for,jsonify

changepassword_bp = Blueprint('changepassword', __name__)


@changepassword_bp.route('/changepassword')
def newpassword():
    return render_template('change_password.html')


@changepassword_bp.route('/newpassword', methods=['POST'])
def change_password():
    new_password = request.form.get('newpassword')
    password_ver = request.form.get('passwrdver')

    print(f"Новый пароль: {new_password}")
    print(f"Подтверждение: {password_ver}")

    if new_password != password_ver:
        return jsonify({'success': False, 'message': 'Пароли не совпадают'}), 400

    # Здесь будет логика сохранения пароля в БД

    return redirect(url_for('main_page'))
