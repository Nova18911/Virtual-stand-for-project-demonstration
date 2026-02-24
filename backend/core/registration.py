from flask import Flask, Blueprint, render_template, request, redirect, url_for

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['get', 'post'])
def register():
    if request.method == 'post':
        email = request.form.get('email')
        fio = request.form.get('fio')
        password = request.form.get('password')
        role = request.form.get('role')

        if role == 'teacher':
            return "<h3>Заявка отправлена. Ожидайте одобрения администратором.</h3>"
        else:
            return redirect(url_for('login'))

    return render_template('registration.html')