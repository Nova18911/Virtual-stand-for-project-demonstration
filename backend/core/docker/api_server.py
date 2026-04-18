from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import threading
import docker
from datetime import datetime

app = Flask(__name__)
CORS(app)

from docker_lifecycle_manager import DockerLifecycleManager
manager = DockerLifecycleManager()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/containers', methods=['GET'])
def list_containers():
    try:
        cursor = manager.db_conn.cursor()
        cursor.execute("""
            SELECT * FROM docker_containers 
            ORDER BY started_at DESC
        """)
        columns = [desc[0] for desc in cursor.description]
        containers = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
       
        for container in containers:
            if container.get('started_at'):
                container['started_at'] = container['started_at'].isoformat()
        
        return jsonify({
            'success': True,
            'containers': containers
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/containers/start', methods=['POST'])
def start_container():
    try:
        data = request.json
        project_id = data['project_id']
        image_name = data['image_name']
        port = data['port']
        
        client = docker.from_env()
        container = client.containers.run(
            image=image_name,
            detach=True,
            ports={f'{port}/tcp': port},
            name=f"project_{project_id}_{datetime.now().timestamp()}"
        )
        
        manager.register_container(
            container_id=container.id,
            project_id=project_id,
            port=port,
            image_name=image_name
        )
        
        return jsonify({
            'success': True,
            'container_id': container.id,
            'message': 'Контейнер успешно запущен'
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/containers/<container_id>', methods=['DELETE'])
def remove_container(container_id):
    try:
        success = manager.manual_cleanup(container_id=container_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Контейнер удален'})
        else:
            return jsonify({'success': False, 'message': 'Контейнер не найден'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/projects/<int:project_id>/containers', methods=['DELETE'])
def remove_project_containers(project_id):
    try:
        success = manager.manual_cleanup(project_id=project_id)
        return jsonify({'success': success, 'message': 'Контейнеры проекта удалены'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        stats = manager.get_container_stats()
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def manage_settings():
    if request.method == 'GET':
        try:
            cursor = manager.db_conn.cursor()
            cursor.execute("""
                SELECT * FROM cleanup_settings 
                ORDER BY id DESC LIMIT 1
            """)
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            settings = dict(zip(columns, row)) if row else {}
            
            
            if settings.get('updated_at'):
                settings['updated_at'] = settings['updated_at'].isoformat()
            
            return jsonify({'success': True, 'settings': settings})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    else:
        try:
            data = request.json
            manager.update_settings(
                container_lifetime_hours=data.get('lifetime_hours', 24),
                image_cleanup_enabled=data.get('cleanup_images', True),
                check_interval_minutes=data.get('check_interval', 5)
            )
            return jsonify({'success': True, 'message': 'Настройки обновлены'})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cleanup/run', methods=['POST'])
def run_cleanup():
    try:
        thread = threading.Thread(target=manager.run_cleanup_cycle)
        thread.start()
        return jsonify({'success': True, 'message': 'Очистка запущена'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        lines = request.args.get('lines', 100, type=int)
        
        with open('docker_lifecycle.log', 'r') as f:
            logs = f.readlines()[-lines:]
        
        return jsonify({'success': True, 'logs': logs})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=manager.start_scheduler, daemon=True)
    scheduler_thread.start()
    
    app.run(host='0.0.0.0', port=5000, debug=False)