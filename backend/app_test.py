from flask import Flask
from auth import auth
from flask import session

app = Flask(__name__)
app.secret_key = 'dev-secret-key'
app.register_blueprint(auth)

@app.route('/')
def index():
    return f'Вы вошли как: {session.get("user_name")} ({session.get("user_role")})'

@app.route('/admin')
def admin_index():
    return 'Панель администратора'

app.add_url_rule('/', endpoint='main.index', view_func=index)
app.add_url_rule('/admin', endpoint='admin.index', view_func=admin_index)

if __name__ == '__main__':
    app.run(debug=True)