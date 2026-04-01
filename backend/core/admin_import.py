from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import pg8000
import io
import csv

admin_import = Blueprint('admin_import', __name__, url_prefix='/admin/import')


def get_db():
    return pg8000.connect(
        host='127.0.0.1',
        port=5432,
        database='course_management',
        user='admin',
        #password='12345678'
        password='12345'
    )


@admin_import.route('/uploaded')
def index():
    return render_template('admin_import.html',
                           user_name=session.get('user_name', 'Админ'))


@admin_import.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')

    if not file or file.filename == '':
        flash('Выберите файл для импорта.', 'error')
        return redirect(url_for('admin_import.index'))

    filename = file.filename.lower()

    if not (filename.endswith('.sql') or filename.endswith('.csv')):
        flash('Поддерживаются только файлы .sql и .csv.', 'error')
        return redirect(url_for('admin_import.index'))

    conn = get_db()
    try:
        cur = conn.cursor()

        if filename.endswith('.sql'):
            sql = file.read().decode('utf-8')
            cur.execute(sql)

        elif filename.endswith('.csv'):
            content = file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            for row in reader:
                cur.execute(
                    'INSERT INTO courses (name, teacher) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING',
                    (row['name'], row['teacher'])
                )

        conn.commit()
        flash(f'Файл «{file.filename}» успешно импортирован.', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Ошибка при импорте: {e}', 'error')
    finally:
        conn.close()

    return redirect(url_for('admin_import.index'))