# backend/core/docker/create_dockerfile.py

import os
import subprocess


def create_dockerfile(repo_path: str, project_type: str, main_file: str) -> dict:
    """Создаёт Dockerfile для консольного проекта (с поддержкой pandas и др.)"""
    try:
        dockerfile_content = f'''# Dockerfile для консольного Python проекта
FROM python:3.11-slim

# Устанавливаем системные зависимости для сборки тяжёлых пакетов (pandas, numpy и т.д.)
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc \\
    python3-dev \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Сначала копируем только requirements.txt — чтобы кэшировать установку зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
COPY . .

# Запускаем программу
CMD ["python", "-u", "{main_file}"]
'''

        dockerfile_path = os.path.join(repo_path, "Dockerfile")
        with open(dockerfile_path, "w", encoding="utf-8") as f:
            f.write(dockerfile_content)

        print("✅ Создан Dockerfile с поддержкой тяжёлых пакетов (pandas и др.)")
        return {'success': True}

    except Exception as e:
        print(f"❌ Ошибка создания Dockerfile: {e}")
        return {'success': False, 'error': str(e)}


def save_requirements_file(repo_path: str, requirements: list):
    """Создаёт requirements.txt"""
    req_path = os.path.join(repo_path, "requirements.txt")
    try:
        with open(req_path, "w", encoding="utf-8") as f:
            if requirements:
                f.write("\n".join(requirements) + "\n")
            else:
                f.write("# Нет дополнительных зависимостей\n")
        print("✅ requirements.txt создан")
    except Exception as e:
        print(f"⚠️ Ошибка создания requirements.txt: {e}")


def create_dockerignore(repo_path: str):
    """Создаёт .dockerignore"""
    content = """__pycache__/
*.pyc
*.pyo
.git
.gitignore
README.md
*.md
.vscode/
.idea/
.env
"""
    try:
        with open(os.path.join(repo_path, ".dockerignore"), "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ .dockerignore создан")
    except:
        pass


def build_docker_image(repo_path: str, image_name: str) -> dict:
    """Улучшенная сборка с выводом логов в реальном времени"""
    print(f"🔨 Начинаем сборку образа {image_name}...")

    try:
        # Важно: используем shell=True + --progress=plain для Windows
        cmd = f'cd /d "{repo_path}" && docker build --progress=plain -t {image_name} .'

        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        output_lines = []
        for line in process.stdout:
            line = line.strip()
            if line:
                print("   " + line)          # ← выводим в консоль в реальном времени
                output_lines.append(line)

        process.wait()

        if process.returncode == 0:
            print(f"✅ Образ {image_name} успешно собран!")
            return {'success': True, 'output': '\n'.join(output_lines)}
        else:
            error_text = '\n'.join(output_lines[-30:])  # последние 30 строк
            print(f"❌ Сборка завершилась с ошибкой (код {process.returncode})")
            return {'success': False, 'error': error_text}

    except Exception as e:
        print(f"❌ Критическая ошибка при сборке: {e}")
        return {'success': False, 'error': str(e)}