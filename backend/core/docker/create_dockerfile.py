# backend/core/docker/create_dockerfile.py

import os
import subprocess


# backend/core/docker/create_dockerfile.py

def create_dockerfile(repo_path: str, project_type: str, main_file: str, system_deps: list = None) -> dict:
    """Минимальный Dockerfile только для tkinter"""

    # Самый минимальный Dockerfile - только то, что нужно
    dockerfile_content = '''FROM python:3.9-slim

# Устанавливаем только минимально необходимое для tkinter
RUN apt-get update && apt-get install -y --no-install-recommends \\
    python3-tk \\
    xvfb \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Контейнер должен жить
CMD ["tail", "-f", "/dev/null"]
'''

    dockerfile_path = os.path.join(repo_path, 'Dockerfile')

    try:
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)

        print(f"✅ Создан минимальный Dockerfile")
        return {'success': True, 'path': dockerfile_path, 'error': None}
    except Exception as e:
        return {'success': False, 'path': None, 'error': str(e)}


def save_requirements_file(repo_path: str, dependencies: list) -> dict:
    """Создает requirements.txt если его нет"""
    req_path = os.path.join(repo_path, 'requirements.txt')

    if os.path.exists(req_path):
        return {'success': True, 'path': req_path, 'error': None}

    # tkinter не требует pip установки
    try:
        with open(req_path, 'w', encoding='utf-8') as f:
            f.write("# Только внешние зависимости (если есть)\n")
            f.write("# tkinter встроен в Python\n")
        return {'success': True, 'path': req_path, 'error': None}
    except Exception as e:
        return {'success': False, 'path': None, 'error': f'Ошибка: {str(e)}'}


def create_dockerignore(repo_path: str) -> dict:
    """Создает .dockerignore"""
    dockerignore_content = '''__pycache__
*.pyc
.git
.venv
venv
.DS_Store
'''
    dockerignore_path = os.path.join(repo_path, '.dockerignore')

    try:
        with open(dockerignore_path, 'w', encoding='utf-8') as f:
            f.write(dockerignore_content)
        return {'success': True, 'path': dockerignore_path, 'error': None}
    except Exception as e:
        return {'success': False, 'path': None, 'error': f'Ошибка: {str(e)}'}


# backend/core/docker/create_dockerfile.py

def build_docker_image(repo_path: str, image_name: str) -> dict:
    """Максимально простая сборка Docker образа"""
    print(f"🔨 Сборка образа {image_name}...")

    # Создаем команду
    cmd = f'cd /d "{repo_path}" && docker build -t {image_name} .'
    print(f"🔧 Команда: {cmd}")

    # Используем os.system для простоты
    result = os.system(cmd)

    if result == 0:
        print(f"✅ Образ {image_name} успешно собран!")
        return {'success': True}
    else:
        print(f"❌ Ошибка сборки (код: {result})")
        return {'success': False, 'error': f'Ошибка сборки (код: {result})'}