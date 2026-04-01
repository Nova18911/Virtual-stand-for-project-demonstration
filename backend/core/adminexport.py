from flask import Blueprint, render_template, request, jsonify, send_file, session, redirect, url_for, flash
import pg8000
import json
import io
import zipfile
from datetime import datetime

admexp_bp = Blueprint('adminexport', __name__)


def get_db_connection():
    return pg8000.connect(
        host="127.0.0.1",
        port=5432,
        database="course_management",
        user="postgres",
        password="12345678"
    )


def get_tables_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    cursor.close()
    conn.close()

    tables_list = []
    for index, table in enumerate(tables, start=1):
        tables_list.append({
            'id': index,
            'name': table[0]
        })
    return tables_list


def get_table_data(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f'SELECT * FROM "{table_name}"')
    rows = cursor.fetchall()

    col_names = [desc[0] for desc in cursor.description]

    cursor.close()
    conn.close()

    result = []
    for row in rows:
        result.append(dict(zip(col_names, row)))

    return result


def generate_sql_dump(table_name, data):
    sql_lines = []

    if not data:
        sql_lines.append(f"-- Table {table_name} is empty")
        return sql_lines

    columns = list(data[0].keys())
    columns_str = ', '.join([f'"{col}"' for col in columns])

    sql_lines.append(f'-- Data for table "{table_name}"')

    for row in data:
        values = []
        for col in columns:
            val = row[col]
            if val is None:
                values.append('NULL')
            elif isinstance(val, str):
                escaped_val = val.replace("'", "''")
                values.append(f"'{escaped_val}'")
            elif isinstance(val, (int, float)):
                values.append(str(val))
            elif isinstance(val, bool):
                values.append('TRUE' if val else 'FALSE')
            elif isinstance(val, datetime):
                values.append(f"'{val.isoformat()}'")
            else:
                values.append(f"'{str(val)}'")

        values_str = ', '.join(values)
        sql_lines.append(f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({values_str});')

    return sql_lines


def generate_json_backup(tables_data):
    backup = {
        'created_at': datetime.now().isoformat(),
        'version': '1.0',
        'tables': tables_data
    }
    return json.dumps(backup, ensure_ascii=False, indent=2, default=str)


@admexp_bp.route('/api/tables')
def get_tables():
    tables = get_tables_from_db()
    return jsonify(tables)


@admexp_bp.route('/api/backup', methods=['POST'])
def create_backup():
    data = request.json
    backup_type = data.get('type', 'partial')
    selected_tables = data.get('tables', [])
    file_format = data.get('format', 'PostgreSQL')
    need_zip = data.get('zip', False)
    filename = data.get('filename', f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    all_tables = get_tables_from_db()
    all_table_names = [t['name'] for t in all_tables]

    if backup_type == 'full':
        tables_to_backup = all_table_names
    else:
        tables_to_backup = [t for t in selected_tables if t in all_table_names]

    if not tables_to_backup:
        return jsonify({'error': 'Нет таблиц для бекапа'}), 400

    backup_data = {}
    for table_name in tables_to_backup:
        table_data = get_table_data(table_name)
        backup_data[table_name] = table_data

    if file_format == 'MySQL':
        sql_lines = [
            f"-- Database Backup",
            f"-- Created: {datetime.now().isoformat()}",
            f"-- Type: {backup_type} backup",
            f"-- Tables: {', '.join(tables_to_backup)}",
            ""
        ]

        for table_name, table_data in backup_data.items():
            sql_lines.extend(generate_sql_dump(table_name, table_data))
            sql_lines.append("")

        file_content = '\n'.join(sql_lines).encode('utf-8')
        file_extension = '.sql'
        mime_type = 'application/sql'
    else:
        backup_json = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'type': backup_type,
                'format': 'postgresql',
                'tables': tables_to_backup
            },
            'data': backup_data
        }
        file_content = json.dumps(backup_json, ensure_ascii=False, indent=2, default=str).encode('utf-8')
        file_extension = '.json'
        mime_type = 'application/json'

    if need_zip:
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{filename}{file_extension}", file_content)
        memory_file.seek(0)

        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{filename}.zip"
        )
    else:
        memory_file = io.BytesIO(file_content)
        memory_file.seek(0)

        return send_file(
            memory_file,
            mimetype=mime_type,
            as_attachment=True,
            download_name=f"{filename}{file_extension}"
        )

@admexp_bp.route('/admin/export')
def export_page():
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('adminlogin.admin_login_page'))
    return render_template('adminexport.html')