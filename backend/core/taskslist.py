from flask import Flask, Blueprint, render_template, session, request, redirect

app = Flask(__name__,
            template_folder='../../frontend/templates',
            static_folder='../../frontend/static')

app.config['SECRET_KEY'] = 'test-secret-key-12345'

tasks_bp = Blueprint('tasks', __name__)


MOCK_LABS_TEACHER = [
    {'lab_id': 1, 'name': 'Лабораторная работа №1'},
    {'lab_id': 2, 'name': 'Лабораторная работа №2'},
    {'lab_id': 3, 'name': 'Лабораторная работа №3'},
    {'lab_id': 4, 'name': 'Лабораторная работа №4'},
]

MOCK_LABS_STUDENT = [
    {'lab_id': 1, 'name': 'Лабораторная работа №1', 'submitted': True},
    {'lab_id': 2, 'name': 'Лабораторная работа №2', 'submitted': True},
    {'lab_id': 3, 'name': 'Лабораторная работа №3', 'submitted': False},
    {'lab_id': 4, 'name': 'Лабораторная работа №4', 'submitted': False},
]


@tasks_bp.route('/')
def index():
    return '''
        <h2>Тестирование страницы заданий</h2>
        <ul>
            <li><a href="/test/set-teacher">Войти как преподаватель</a></li>
            <li><a href="/test/set-student">Войти как студент</a></li>
        </ul>
    '''


@tasks_bp.route('/tasks/teacher')
def tasks_teacher():
    return render_template('tasks_teacher.html', labs=MOCK_LABS_TEACHER)


@tasks_bp.route('/tasks/student')
def tasks_student():
    return render_template('tasks_student.html', labs=MOCK_LABS_STUDENT)


@tasks_bp.route('/tasks')
def tasks_page():
    role = session.get('role', 'student')
    if role == 'teacher':
        return render_template('tasks_teacher.html', labs=MOCK_LABS_TEACHER)
    else:
        return render_template('tasks_student.html', labs=MOCK_LABS_STUDENT)


@tasks_bp.route('/task/<int:lab_id>/edit')
def task_edit(lab_id):
    lab = next((l for l in MOCK_LABS_TEACHER if l['lab_id'] == lab_id), None)
    if not lab:
        return "Задание не найдено", 404
    return f'''
        <h2>Редактирование: {lab["name"]}</h2>
        <p>Здесь будет форма редактирования задания (id={lab_id})</p>
        <a href="/tasks">← Назад к заданиям</a>
    '''


@tasks_bp.route('/task/<int:lab_id>')
def task_detail(lab_id):
    lab = next((l for l in MOCK_LABS_STUDENT if l['lab_id'] == lab_id), None)
    if not lab:
        return "Задание не найдено", 404
    return f'''
        <h2>{lab["name"]}</h2>
        <p>Здесь будет страница задания с описанием и полем для ссылки на репозиторий</p>
        <a href="/tasks">← Назад к заданиям</a>
    '''


@tasks_bp.route('/task/add')
def task_add():
    return '''
        <h2>Добавление задания</h2>
        <p>Здесь будет форма добавления задания</p>
        <a href="/tasks">← Назад к заданиям</a>
    '''


@tasks_bp.route('/test/set-teacher')
def set_teacher():
    session['role'] = 'teacher'
    session['user_id'] = 1
    return '''
        <p>✅ Роль установлена: <b>преподаватель</b></p>
        <a href="/tasks">Перейти к заданиям</a>
    '''


@tasks_bp.route('/test/set-student')
def set_student():
    session['role'] = 'student'
    session['user_id'] = 2
    return '''
        <p>✅ Роль установлена: <b>студент</b></p>
        <a href="/tasks">Перейти к заданиям</a>
    '''


app.register_blueprint(tasks_bp)

if __name__ == '__main__':
    app.run(debug=True)