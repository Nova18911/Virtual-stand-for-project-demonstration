import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Flask, redirect, render_template, url_for
from auth import auth_bp
from core.registration import register_bp
from core.mainpage import mainpage_bp
from core.adminlogin import logadm_bp
from core.adminexport import admexp_bp
from core.taskslist import taskslist_bp
from core.task import task_bp
from core.tasks import tasks_bp
from core.admin_main import admin_main
from backend.student_list import task_detail_bp
from core.docker.streamer import streamer_bp
from core.admin_import import admin_import
from admin_notify import admin_notify_bp  

app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

app.config['SECRET_KEY'] = 'any-simple-string-here-12345'

app.register_blueprint(auth_bp)
app.register_blueprint(register_bp)
app.register_blueprint(mainpage_bp)
app.register_blueprint(logadm_bp)
app.register_blueprint(admexp_bp)
app.register_blueprint(taskslist_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(task_bp)
app.register_blueprint(admin_main)
app.register_blueprint(task_detail_bp)
app.register_blueprint(admin_import)
app.register_blueprint(streamer_bp)
app.register_blueprint(admin_notify_bp)  




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

@app.route('/main_page')
def main_redirect():
    return redirect(url_for('main_page'))



if __name__ == '__main__':
    app.run(debug=True)