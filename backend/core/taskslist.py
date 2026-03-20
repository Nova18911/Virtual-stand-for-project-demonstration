from flask import Flask, Blueprint, render_template, session, request, redirect, url_for


tasks_bp = Blueprint('tasks', __name__)


MOCK_LABS_TEACHER = [
    {'lab_id': 1, 'name': 'Лабораторная работа №1', 'course': ''},
    {'lab_id': 2, 'name': 'Лабораторная работа №2', 'course': ''},
    {'lab_id': 3, 'name': 'Лабораторная работа №3', 'course': ''},
    {'lab_id': 4, 'name': 'Лабораторная работа №4', 'course': ''},
]

_next_lab_id = 5

MOCK_LABS_STUDENT = [
    {'lab_id': 1, 'name': 'Лабораторная работа №1', 'submitted': True},
    {'lab_id': 2, 'name': 'Лабораторная работа №2', 'submitted': True},
    {'lab_id': 3, 'name': 'Лабораторная работа №3', 'submitted': False},
    {'lab_id': 4, 'name': 'Лабораторная работа №4', 'submitted': False},
]


@tasks_bp.route('/tasks')
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

@tasks_bp.route('/task/add', methods=['GET', 'POST'])
def task_add():
    global _next_lab_id
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        course = request.form.get('course', '').strip()
        deadline = request.form.get('deadline', '')
        description = request.form.get('description', '')

        if name:
            display_name = f"{name} ({course})" if course else name
            MOCK_LABS_TEACHER.append({
                'lab_id': _next_lab_id,
                'name': display_name,
                'course': course,
                'deadline': deadline,
                'description': description,
            })
            _next_lab_id += 1

        return redirect(url_for('tasks.tasks_teacher'))
    return redirect(url_for('tasks.tasks_teacher') + '?add=1')


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