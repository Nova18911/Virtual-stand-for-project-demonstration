from flask import Flask,redirect, render_template, url_for
from auth import auth_bp
from core.registration import register_bp
from core.mainpage import mainpage_bp

# Указываем Flask, где искать папки со страницами и стилями
app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

app.register_blueprint(auth_bp)
app.register_blueprint(register_bp)
app.register_blueprint(mainpage_bp)

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/reg')
def register():
    return redirect(url_for('register_page'))

@app.route('/registertion')
def register_page():
    return render_template('registration.html')

@app.route('/regist')
def register_redirect():
    return redirect(url_for('login_page'))

@app.route('/main')
def main_page():
    return render_template('mainpage.html')

@app.route('/mainpage')
def main_redirect():
    return redirect(url_for('main_page'))

if __name__ == '__main__':
    app.run(debug=True)