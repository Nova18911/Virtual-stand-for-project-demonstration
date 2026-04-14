from flask import Blueprint, render_template, jsonify
from backend.core.connect import get_db_connection

admin_notify_bp = Blueprint('admin_notify', __name__, url_prefix='/admin-notify')


@admin_notify_bp.route('/', methods=['GET'])
def admin_notify_page():
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.full_name, p.login, u.created_at
            FROM users u
            LEFT JOIN passwords p ON p.login_id = u.login_id
            JOIN roles r ON r.access_id = u.access_id
            WHERE r.access_rights = 'teacher' AND u.is_approved = false
            ORDER BY u.user_id DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        users_list = [
            {
                'user_id':   r[0],
                'full_name': r[1],
                'email':     r[2] if r[2] else 'Нет email',
                'created_at': r[3].strftime('%Y-%m-%d %H:%M:%S') if r[3] else '—'
            } for r in rows
        ]
        return render_template('admin_notify.html', users=users_list)

    except Exception as e:
        return render_template('admin_notify.html', users=[], error=str(e))


@admin_notify_bp.route('/users/pending', methods=['GET'])
def get_pending_users():
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.full_name, p.login, u.created_at
            FROM users u
            LEFT JOIN passwords p ON p.login_id = u.login_id
            JOIN roles r ON r.access_id = u.access_id
            WHERE r.access_rights = 'teacher' AND u.is_approved = false
            ORDER BY u.user_id DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'users': [
            {
                'user_id':   r[0],
                'full_name': r[1],
                'email':     r[2] if r[2] else 'Нет email',
                'created_at': r[3].strftime('%Y-%m-%d %H:%M:%S') if r[3] else '—'
            } for r in rows
        ]})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_notify_bp.route('/approve/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET is_approved = true, approved_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND is_approved = false
            RETURNING user_id, full_name
        """, (user_id,))
        updated = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        if updated:
            return jsonify({'success': True, 'message': f'Преподаватель {updated[1]} одобрен'})
        return jsonify({'success': False, 'error': 'Не найден или уже одобрен'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_notify_bp.route('/reject/<int:user_id>', methods=['POST'])
def reject_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        
        cursor.execute("SELECT full_name, login_id FROM users WHERE user_id = %s", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Преподаватель не найден'}), 404

        full_name, login_id = user_data

        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        
        
        if login_id:
            cursor.execute("DELETE FROM passwords WHERE login_id = %s", (login_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            'success': True, 
            'message': f'Преподаватель {full_name} был удален из системы'
        })

    except Exception as e:
        if conn:
            conn.rollback() 
        return jsonify({'success': False, 'error': str(e)}), 500