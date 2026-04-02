#backend/core/docker/create_docker_file.py
import os
import subprocess

def create_dockerfile(repo_path: str, project_type: str, main_file: str) -> dict:
    if not os.path.exists(repo_path):
        return {'success': False, 'path': None, 'error': 'Папка репозитория не найдена'}

    if not main_file:
        return {'success': False, 'path': None, 'error': 'Не найден основной файл запуска'}

    dockerfile_content = f'''
FROM python:3.12

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt || true

COPY . .
'''

    if project_type == 'gui':
        dockerfile_content += '''
    RUN apt-get update && apt-get install -y \\
    python3-tk \\
    python3-pyqt5 \\
    x11-apps \\
    libx11-xcb1 \\
    libxcb-icccm4 \\
    libxcb-image0 \\
    libxcb-keysyms1 \\
    libxcb-randr0 \\
    libxcb-render-util0 \\
    libxcb-shape0 \\
    libxcb-xinerama0 \\
    libxcb-xfixes0 \\
    libxcb-xkb1 \\
    libxkbcommon-x11-0 \\
    && rm -rf /var/lib/apt/lists/*

ENV DISPLAY=host.docker.internal:0
ENV QT_X11_NO_MITSHM=1

'''

        dockerfile_content += f'''
CMD ["python", "{main_file}"]
        '''
    else:
        dockerfile_content += f'''
CMD ["python", "{main_file}"]
'''
    dockerfile_path = os.path.join(repo_path, 'Dockerfile')

    try:
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
        return {'success': True, 'path': dockerfile_path, 'error': None}
    except Exception as e:
        return {'success': False, 'path': None, 'error': f'Ошибка сохранения Dockerfile: {str(e)}'}


def save_requirements_file(repo_path: str, dependencies: list) -> dict:

    if not os.path.exists(repo_path):
        return {'success': False, 'path': None, 'error': 'Папка репозитория не найдена'}

    req_path = os.path.join(repo_path, 'requirements.txt')

    if os.path.exists(req_path):
        return {'success': True, 'path': req_path, 'error': None}

    if not dependencies:
        dependencies = ['python']

    try:
        with open(req_path, 'w', encoding='utf-8') as f:
            for dep in sorted(set(dependencies)):
                if dep and not dep.startswith('_'):
                    f.write(f"{dep}\n")
        return {'success': True, 'path': req_path, 'error': None}
    except Exception as e:
        return {'success': False, 'path': None, 'error': f'Ошибка сохранения requirements.txt: {str(e)}'}


def create_dockerignore(repo_path: str) -> dict:

    dockerignore_content = '''# Git
.git/
.gitignore
.gitattributes

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
venv*/
.env
.venv
.venv*/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/

# Docker
Dockerfile
.dockerignore
'''

    dockerignore_path = os.path.join(repo_path, '.dockerignore')

    try:
        with open(dockerignore_path, 'w', encoding='utf-8') as f:
            f.write(dockerignore_content)
        return {'success': True, 'path': dockerignore_path, 'error': None}
    except Exception as e:
        return {'success': False, 'path': None, 'error': f'Ошибка сохранения .dockerignore: {str(e)}'}

def check_docker_available() -> dict:
    result = {
        'available': False,
        'version': None,
        'error': None
    }

    try:
        version_result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if version_result.returncode == 0:
            result['available'] = True
            result['version'] = version_result.stdout.strip()
        else:
            result['error'] = 'Docker установлен, но не отвечает'
            return result

    except FileNotFoundError:
        result['error'] = 'Docker не установлен. Установите Docker: sudo apt install docker.io'
        return result
    except Exception as e:
        result['error'] = f'Ошибка при проверке Docker: {str(e)}'
        return result

    try:
        ps_result = subprocess.run(
            ['docker', 'ps'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if ps_result.returncode != 0:
            error_msg = ps_result.stderr.lower()

            if "permission denied" in error_msg:
                result['error'] = 'Нет прав доступа к Docker. Выполните: sudo usermod -aG docker $USER'
                result['available'] = False
            elif "cannot connect to the docker daemon" in error_msg:
                result['error'] = 'Docker демон не запущен. Выполните: sudo systemctl start docker'
                result['available'] = False
            else:
                result['error'] = f'Docker недоступен: {ps_result.stderr}'
                result['available'] = False

    except Exception as e:
        result['error'] = f'Ошибка при подключении к Docker: {str(e)}'
        result['available'] = False

    return result

def build_docker_image(repo_path: str, image_name: str) -> dict:

    docker_check = check_docker_available()
    if not docker_check['available']:
        return {
            'success': False,
            'error': docker_check['error']
        }

    print(f"Образ {image_name}...")
    print(f"Путь: {repo_path}")

    try:
        result = subprocess.run(
            ['docker', 'build', '-t', image_name, repo_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 минут на сборку
        )

        if result.returncode == 0:
            inspect_result = subprocess.run(
                ['docker', 'inspect', image_name, '--format', '{{.Size}}'],
                capture_output=True,
                text=True
            )

            size_bytes = int(inspect_result.stdout.strip()) if inspect_result.stdout else 0
            size_mb = size_bytes / 1024 / 1024

            print(f"Образ {image_name}  собран (размер: {size_mb:.2f} MB)")

            return {
                'success': True,
                'output': result.stdout,
                'error': None,
                'image_size': size_mb,
                'image_name': image_name
            }
        else:
            error_msg = result.stderr
            if "no such file or directory" in error_msg:
                error_msg = "Dockerfile не найден. Проверьте путь."
            elif "COPY failed" in error_msg:
                error_msg = "Ошибка копирования файлов. Проверьте структуру проекта."
            elif "pip install" in error_msg and "error" in error_msg:
                error_msg = "Ошибка установки зависимостей. Проверьте requirements.txt."

            print(f"❌ Ошибка сборки: {error_msg}")

            return {
                'success': False,
                'output': result.stdout,
                'error': error_msg
            }

    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Превышено время сборки (5 минут). Возможно, проект слишком большой.'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Ошибка при выполнении Docker: {str(e)}'
        }