from backend.core.connect import get_db_connection
from backend.core.docker.git_clone       import clone_repo, delete_repo
from backend.core.docker.project_analyzer import analyze_project
from backend.core.docker.create_dockerfile import (
    create_dockerfile, save_requirements_file,
    create_dockerignore, build_docker_image
)
from datetime import datetime
from backend.core.runner import run_container


def build_and_run(github_url: str, project_id: int, image_name: str) -> dict:
    """
    Полный pipeline:
    1. Клонировать репозиторий
    2. Проанализировать проект
    3. Создать Dockerfile + requirements
    4. Собрать Docker-образ
    5. Запустить контейнер и вернуть ссылку
    """

    # 1. Клонирование
    clone = clone_repo(github_url)
    if not clone['success']:
        return {'ok': False, 'error': clone['error']}
    repo_path = clone['path']

    try:
        # 2. Анализ проекта
        analysis = analyze_project(repo_path)
        if analysis['error']:
            return {'ok': False, 'error': analysis['error']}

        if not analysis['main_file']:
            return {'ok': False, 'error': 'Не найден основной файл запуска (main.py, app.py и т.д.)'}

        # Сохраняем информацию о проекте
        _save_project_analysis(project_id, analysis, image_name, repo_path)

        # 3. Создаём вспомогательные файлы
        save_requirements_file(repo_path, analysis['requirements'])
        create_dockerignore(repo_path)

        dockerfile = create_dockerfile(
            repo_path,
            analysis['project_type'],
            analysis['main_file']
        )
        if not dockerfile['success']:
            return {'ok': False, 'error': dockerfile['error']}

        # 4. Сборка образа
        build = build_docker_image(repo_path, image_name)
        if not build['success']:
            return {'ok': False, 'error': build['error']}

        # 5. Запуск контейнера с учетом типа проекта
        container, link = run_container(
            image_name,
            project_id,
            analysis['project_type']  # Передаем тип проекта
        )

        if not container:
            return {'ok': False, 'error': 'Ошибка при запуске контейнера'}

        return {'ok': True, 'link': link, 'container_id': container.id}

    finally:
        # Удаляем временную папку в любом случае
        delete_repo(repo_path)


def _save_project_analysis(project_id: int, analysis: dict, image_name: str, repo_path: str):
    """Сохраняет анализ проекта в БД"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверяем размер образа
        import subprocess
        size_mb = "Unknown"
        try:
            result = subprocess.run(
                ['docker', 'inspect', image_name, '--format', '{{.Size}}'],
                capture_output=True,
                text=True
            )
            if result.stdout:
                size_bytes = int(result.stdout.strip())
                size_mb = f"{size_bytes / 1024 / 1024:.2f} MB"
        except:
            pass

        comment = f"""
[СКЛОНИРОВАНО {datetime.now()}] {repo_path}
[ТИП ПРОЕКТА] {analysis['project_type']}
[ОСНОВНОЙ ФАЙЛ] {analysis['main_file']}
[ЗАВИСИМОСТИ] {', '.join(analysis['requirements'][:10])}
[СОБРАН ОБРАЗ] {image_name}
[РАЗМЕР ОБРАЗА] {size_mb}
[DOCKERFILE] {repo_path}/Dockerfile
        """.strip()

        cursor.execute("""
            UPDATE student_projects
            SET build_info = %s
            WHERE project_id = %s
        """, (comment, project_id))
        conn.commit()
    except Exception as e:
        print(f"⚠️ Не удалось сохранить информацию: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()