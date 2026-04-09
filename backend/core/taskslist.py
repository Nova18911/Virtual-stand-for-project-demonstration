from flask import Blueprint, jsonify, request, session, Response
from backend.core.connect import get_db_connection
from datetime import datetime, timedelta

taskslist_bp = Blueprint('taskslist', __name__)

def format_date(date_val):
    """Вспомогательная функция для безопасного форматирования даты, 
    даже если БД возвращает строку вместо объекта datetime"""
    if not date_val:
        return None
    if isinstance(date_val, datetime):
        return date_val.strftime('%d.%m.%Y')
    if isinstance(date_val, str):
        try:
            # Пробуем распарсить стандартный формат ISO YYYY-MM-DD
            dt = datetime.strptime(date_val[:10], '%Y-%m-%d')
            return dt.strftime('%d.%m.%Y')
        except:
            return date_val
    return str(date_val)

@taskslist_bp.route('/api/course/<int:course_id>/labs', methods=['GET'])
def get_course_labs(course_id):
    user_id = session.get('user_id')
    role    = session.get('user_role', 'student')

    conn   = get_db_connection()
    cursor = conn.cursor()

    if role == 'student' and user_id:
        cursor.execute("""
            SELECT
                l.lab_id,
                l.name,
                l.task,
                l.start_date,
                l.end_date,
                CASE WHEN sp.project_id IS NOT NULL THEN true ELSE false END AS submitted,
                CASE WHEN l.task_file IS NOT NULL AND length(l.task_file) > 0 THEN true ELSE false END AS has_file
            FROM labs l
            LEFT JOIN student_projects sp
                ON sp.lab_id = l.lab_id AND sp.user_id = %s
            WHERE l.course_id = %s
            ORDER BY l.lab_id
        """, (user_id, course_id))
    else:
        cursor.execute("""
            SELECT
                lab_id,
                name,
                task,
                start_date,
                end_date,
                false AS submitted,
                CASE WHEN task_file IS NOT NULL AND length(task_file) > 0 THEN true ELSE false END AS has_file
            FROM labs
            WHERE course_id = %s
            ORDER BY lab_id
        """, (course_id,))

    labs = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify([
        {
            'id':         lab[0],
            'name':       lab[1],
            'task':       lab[2],
            'start_date': format_date(lab[3]),
            'end_date':   format_date(lab[4]),
            'submitted':  lab[5],
            'has_file':   lab[6],
        }
        for lab in labs
    ])


@taskslist_bp.route('/api/task/<int:lab_id>', methods=['GET'])
def get_task(lab_id):
    role = session.get('user_role')
    if role != 'teacher':
        return jsonify({'ok': False, 'error': 'Недостаточно прав.'}), 403

    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lab_id, name, task, end_date,
               CASE WHEN task_file IS NOT NULL AND length(task_file) > 0 
                    THEN true ELSE false END AS has_file
        FROM labs WHERE lab_id = %s
    """, (lab_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return jsonify({'ok': False, 'error': 'Задание не найдено.'}), 404

    # Для input type="date" нужен формат YYYY-MM-DD
    raw_date = row[3]
    if isinstance(raw_date, datetime):
        formatted_raw = raw_date.strftime('%Y-%m-%d')
    elif isinstance(raw_date, str):
        formatted_raw = raw_date[:10]
    else:
        formatted_raw = ''

    return jsonify({
        'id':           row[0],
        'name':         row[1],
        'task':         row[2],
        'end_date_raw': formatted_raw,
        'has_file':     row[4],
    })


@taskslist_bp.route('/api/task/<int:lab_id>/file', methods=['GET'])
def download_task_file(lab_id):
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT task_file, name FROM labs WHERE lab_id = %s", (lab_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row or not row[0]:
        return jsonify({'ok': False, 'error': 'Файл не найден.'}), 404

    file_bytes = bytes(row[0])
    file_name  = f"{row[1]}"

    return Response(
        file_bytes,
        mimetype='application/octet-stream',
        headers={'Content-Disposition': f'attachment; filename="{file_name}"'}
    )


@taskslist_bp.route('/api/task/add', methods=['POST'])
def add_task():
    role = session.get('user_role')
    if role != 'teacher':
        return jsonify({'ok': False, 'error': 'Недостаточно прав.'}), 403

    course_id   = request.form.get('course_id', '').strip()
    name        = request.form.get('name', '').strip()
    deadline    = request.form.get('deadline', '').strip()
    description = request.form.get('description', '').strip()
    file        = request.files.get('file')

    if not name:      return jsonify({'ok': False, 'error': 'Введите название задания.'}), 400
    if not deadline:  return jsonify({'ok': False, 'error': 'Укажите срок сдачи.'}), 400
    if not course_id: return jsonify({'ok': False, 'error': 'Не указан курс.'}), 400

    try:
        selected_date = datetime.strptime(deadline, '%Y-%m-%d').date()
        min_date = datetime.now().date() + timedelta(days=1)
        if selected_date < min_date:
            return jsonify({'ok': False, 'error': f'Срок сдачи должен быть не раньше {min_date.strftime("%d.%m.%Y")}.'}), 400
    except ValueError:
        return jsonify({'ok': False, 'error': 'Некорректный формат даты.'}), 400

    file_bytes = file.read() if file and file.filename else b''

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO labs (name, course_id, task, task_file, end_date)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING lab_id
        """, (name, int(course_id), description, file_bytes, deadline))
        lab_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({'ok': False, 'error': f'Ошибка при добавлении: {e}'}), 500

    return jsonify({'ok': True, 'lab_id': lab_id})


@taskslist_bp.route('/api/task/edit', methods=['POST'])
def edit_task():
    role = session.get('user_role')
    if role != 'teacher':
        return jsonify({'ok': False, 'error': 'Недостаточно прав.'}), 403

    lab_id      = request.form.get('lab_id', '').strip()
    name        = request.form.get('name', '').strip()
    deadline    = request.form.get('deadline', '').strip()
    description = request.form.get('description', '').strip()
    file        = request.files.get('file')

    if not name:     return jsonify({'ok': False, 'error': 'Введите название.'}), 400
    if not deadline: return jsonify({'ok': False, 'error': 'Укажите срок сдачи.'}), 400

    try:
        selected_date = datetime.strptime(deadline, '%Y-%m-%d').date()
        min_date = datetime.now().date() + timedelta(days=1)
        if selected_date < min_date:
            return jsonify({'ok': False, 'error': f'Нельзя установить срок сдачи раньше {min_date.strftime("%d.%m.%Y")}.'}), 400
    except ValueError:
        return jsonify({'ok': False, 'error': 'Некорректный формат даты.'}), 400

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        if file and file.filename and len(file.filename) > 0:
            file_bytes = file.read()
            cursor.execute("""
                UPDATE labs SET name=%s, task=%s, end_date=%s, task_file=%s
                WHERE lab_id=%s
            """, (name, description, deadline, file_bytes, int(lab_id)))
        else:
            cursor.execute("""
                UPDATE labs SET name=%s, task=%s, end_date=%s
                WHERE lab_id=%s
            """, (name, description, deadline, int(lab_id)))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({'ok': False, 'error': f'Ошибка: {e}'}), 500

    return jsonify({'ok': True})