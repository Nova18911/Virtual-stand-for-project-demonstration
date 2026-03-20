from flask import Flask, Blueprint, render_template, session, request, redirect, url_for

tasks_bp = Blueprint('tasks', __name__)

# Обновленные моковые данные с course_id
MOCK_LABS_TEACHER = [
    {'lab_id': 1, 'name': 'Лабораторная работа №1', 'course_id': 1, 'course_name': 'Курс 1'},
    {'lab_id': 2, 'name': 'Лабораторная работа №2', 'course_id': 1, 'course_name': 'Курс 1'},
    {'lab_id': 3, 'name': 'Лабораторная работа №3', 'course_id': 2, 'course_name': 'Курс 2'},
    {'lab_id': 4, 'name': 'Лабораторная работа №4', 'course_id': 2, 'course_name': 'Курс 2'},
]

_next_lab_id = 5

MOCK_LABS_STUDENT = [
    {'lab_id': 1, 'name': 'Лабораторная работа №1', 'course_id': 1, 'submitted': True},
    {'lab_id': 2, 'name': 'Лабораторная работа №2', 'course_id': 1, 'submitted': True},
    {'lab_id': 3, 'name': 'Лабораторная работа №3', 'course_id': 2, 'submitted': False},
    {'lab_id': 4, 'name': 'Лабораторная работа №4', 'course_id': 2, 'submitted': False},
]


@tasks_bp.route('/tasks')
def index():
    course_id = request.args.get('course_id')

    if course_id:
        return f'''
            <h2>Тестирование страницы заданий для курса {course_id}</h2>
            <p>Вы перешли по ссылке с курса ID: {course_id}</p>
            <ul>
                <li><a href="/test/set-teacher?course_id={course_id}">Войти как преподаватель</a></li>
                <li><a href="/test/set-student?course_id={course_id}">Войти как студент</a></li>
            </ul>
        '''
    else:
        return '''
            <h2>Тестирование страницы заданий</h2>
            <p>Выберите курс на главной странице</p>
            <ul>
                <li><a href="/">Назад к курсам</a></li>
            </ul>
        '''

@tasks_bp.route('/tasks/teacher')
def tasks_teacher():
    return render_template('tasks_teacher.html', labs=MOCK_LABS_TEACHER)


@tasks_bp.route('/tasks/student')
def tasks_student():
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
        course_id = request.form.get('course_id', '').strip()
        course_name = request.form.get('course_name', '').strip()
        deadline = request.form.get('deadline', '')
        description = request.form.get('description', '')

        if name:
            display_name = f"{name} ({course_name})" if course_name else name
            MOCK_LABS_TEACHER.append({
                'lab_id': _next_lab_id,
                'name': display_name,
                'course_id': int(course_id) if course_id else None,
                'course_name': course_name,
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
    course_id = request.args.get('course_id')

    if course_id:
        return redirect(url_for('tasks.course_tasks', course_id=course_id))
    else:
        return '''
            <p>❌ Ошибка: курс не выбран</p>
            <a href="/">Вернуться на главную</a>
        '''


@tasks_bp.route('/test/set-student')
def set_student():
    session['role'] = 'student'
    session['user_id'] = 2
    course_id = request.args.get('course_id')

    if course_id:
        return redirect(url_for('tasks.course_tasks', course_id=course_id))
    else:
        return '''
            <p>❌ Ошибка: курс не выбран</p>
            <a href="/">Вернуться на главную</a>
        '''

@tasks_bp.route('/tasks/course/<int:course_id>')
def course_tasks(course_id):
    role = session.get('role', 'student')
    course_name = f"Курс {course_id}"

    session['current_course_id'] = course_id
    session['current_course_name'] = course_name

    if role == 'teacher':
        course_labs = [lab for lab in MOCK_LABS_TEACHER if lab.get('course_id') == course_id]
        return render_template('tasks_teacher.html',
                               labs=course_labs,
                               course_id=course_id,
                               course_name=course_name)
    else:
        course_labs = [lab for lab in MOCK_LABS_STUDENT if lab.get('course_id') == course_id]
        return render_template('tasks_student.html',
                               labs=course_labs,
                               course_id=course_id,
                               course_name=course_name)