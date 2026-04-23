import os
import subprocess


def create_dockerfile(repo_path: str, project_type: str, main_file: str) -> dict:
    try:
        dockerfile_content = f'''FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "{main_file}"]
'''

        with open(os.path.join(repo_path, "Dockerfile"), "w", encoding="utf-8") as f:
            f.write(dockerfile_content)

        return {'success': True}

    except Exception as e:
        print(f"Ошибка создания Dockerfile: {e}")
        return {'success': False, 'error': str(e)}

def save_requirements_file(repo_path: str, requirements: list):
    req_path = os.path.join(repo_path, "requirements.txt")
    try:
        with open(req_path, "w", encoding="utf-8") as f:
            if requirements:
                f.write("\n".join(requirements) + "\n")
            else:
                f.write("# Нет дополнительных зависимостей\n")
    except Exception as e:
        print(f"Ошибка создания requirements.txt: {e}")


def create_dockerignore(repo_path: str):
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
        print(".dockerignore создан")
    except:
        pass


def build_docker_image(repo_path: str, image_name: str) -> dict:
    print(f"Cборка образа {image_name}...")

    try:
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
                print("   " + line)
                output_lines.append(line)

        process.wait()

        if process.returncode == 0:
            print(f"Образ {image_name} успешно собран!")
            return {'success': True, 'output': '\n'.join(output_lines)}
        else:
            error_text = '\n'.join(output_lines[-30:])
            print(f"Сборка завершилась с ошибкой (код {process.returncode})")
            return {'success': False, 'error': error_text}

    except Exception as e:
        print(f"Критическая ошибка при сборке: {e}")
        return {'success': False, 'error': str(e)}