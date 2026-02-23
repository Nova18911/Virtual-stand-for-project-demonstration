from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

@app.route('/register', methods=['get', 'post'])
def register():
    if request.method == 'post':
        email = request.form.get('email')
        fio = request.form.get('fio')
        password = request.form.get('password')
        role = request.form.get('role')

        if role == 'teacher':
            return "<h3>Заявка отправлена. Ожидайте одобрения администратором.</h3>"
        else:
            return redirect(url_for('login_page'))

    return render_template('registration.html')