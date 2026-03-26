from flask import Flask, Blueprint, render_template, request, jsonify
import pg8000
import os
import sys

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Создаем Blueprint
admin_notify_bp = Blueprint('admin_notify', __name__, url_prefix='/admin-notify')

def get_db_connection():
    """Подключение к базе данных PostgreSQL"""
    return pg8000.connect(
        host="localhost",
        port=5432,
        database="course_management",
        user="postgres",
        password="endermen"
    )

@admin_notify_bp.route('/', methods=['GET'])
def admin_notify_page():
    """Страница уведомлений администратора"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем пользователей со статусом pending
        cursor.execute("""
            SELECT u.user_id, u.full_name, p.login as email, u.status, u.is_approved, u.created_at
            FROM users u
            LEFT JOIN passwords p ON p.login_id = u.login_id
            WHERE u.status = 'pending' OR u.is_approved = false
            ORDER BY u.user_id DESC
        """)
        
        pending_users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        users_list = []
        for user in pending_users:
            users_list.append({
                'user_id': user[0],
                'full_name': user[1],
                'email': user[2] if user[2] else 'Нет email',
                'status': user[3],
                'is_approved': user[4],
                'created_at': user[5].strftime('%Y-%m-%d %H:%M:%S') if user[5] else 'Н/Д'
            })
        
        return render_template('admin_notify.html', users=users_list)
        
    except Exception as e:
        print(f"Error: {e}")
        return render_template('admin_notify.html', users=[], error=str(e))

@admin_notify_bp.route('/approve/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    """Одобрить пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Обновляем статус пользователя
        cursor.execute("""
            UPDATE users 
            SET status = 'approved', 
                is_approved = true,
                approved_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND (status = 'pending' OR is_approved = false)
            RETURNING user_id, full_name
        """, (user_id,))
        
        updated_user = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if updated_user:
            return jsonify({
                'success': True, 
                'message': f'Пользователь {updated_user[1]} успешно одобрен'
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Пользователь не найден или уже одобрен'
            }), 404
            
    except Exception as e:
        print(f"Error approving user: {e}")
        return jsonify({
            'success': False, 
            'error': f'Ошибка при одобрении: {str(e)}'
        }), 500

@admin_notify_bp.route('/reject/<int:user_id>', methods=['POST'])
def reject_user(user_id):
    """Отклонить пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Обновляем статус пользователя
        cursor.execute("""
            UPDATE users 
            SET status = 'rejected', 
                is_approved = false,
                rejected_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND (status = 'pending' OR is_approved = false)
            RETURNING user_id, full_name
        """, (user_id,))
        
        updated_user = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if updated_user:
            return jsonify({
                'success': True, 
                'message': f'Пользователь {updated_user[1]} отклонен'
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Пользователь не найден или уже обработан'
            }), 404
            
    except Exception as e:
        print(f"Error rejecting user: {e}")
        return jsonify({
            'success': False, 
            'error': f'Ошибка при отклонении: {str(e)}'
        }), 500

@admin_notify_bp.route('/users/pending', methods=['GET'])
def get_pending_users():
    """API для получения списка ожидающих пользователей"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.user_id, u.full_name, p.login as email, u.status, u.is_approved, u.created_at
            FROM users u
            LEFT JOIN passwords p ON p.login_id = u.login_id
            WHERE u.status = 'pending' OR u.is_approved = false
            ORDER BY u.user_id DESC
        """)
        
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                'user_id': user[0],
                'full_name': user[1],
                'email': user[2] if user[2] else 'Нет email',
                'status': user[3],
                'is_approved': user[4],
                'created_at': user[5].strftime('%Y-%m-%d %H:%M:%S') if user[5] else 'Н/Д'
            })
        
        return jsonify({'success': True, 'users': user_list})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_notify_bp.route('/users/all', methods=['GET'])
def get_all_users():
    """API для получения всех пользователей"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.user_id, u.full_name, p.login as email, u.status, u.is_approved, u.created_at
            FROM users u
            LEFT JOIN passwords p ON p.login_id = u.login_id
            ORDER BY u.user_id DESC
        """)
        
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        user_list = []
        for user in users:
            user_list.append({
                'user_id': user[0],
                'full_name': user[1],
                'email': user[2] if user[2] else 'Нет email',
                'status': user[3],
                'is_approved': user[4],
                'created_at': user[5].strftime('%Y-%m-%d %H:%M:%S') if user[5] else 'Н/Д'
            })
        
        return jsonify({'success': True, 'users': user_list})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= ЗАПУСК ПРИЛОЖЕНИЯ =============
if __name__ == '__main__':
    # Определяем пути
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(backend_dir)
    frontend_dir = os.path.join(root_dir, 'frontend')
    template_dir = os.path.join(frontend_dir, 'templates')
    static_dir = os.path.join(frontend_dir, 'static')
    
    print("=" * 50)
    print(f"Template dir: {template_dir}")
    print(f"Template exists: {os.path.exists(template_dir)}")
    print("=" * 50)
    
    # Создаем Flask приложение
    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)
    
    app.config['SECRET_KEY'] = 'your-secret-key-here-12345'
    
    # Регистрируем blueprint
    app.register_blueprint(admin_notify_bp)
    
    print("\n✅ Admin Notify приложение запущено!")
    print("🌐 Перейдите по адресу: http://127.0.0.1:5001/admin-notify")
    print("=" * 50)
    
    # Запускаем сервер
    app.run(debug=True, port=5001)