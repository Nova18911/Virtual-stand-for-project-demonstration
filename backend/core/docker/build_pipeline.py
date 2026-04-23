from backend.core.connect import get_db_connection
from backend.core.docker.git_clone import clone_repo, delete_repo
from backend.core.docker.project_analyzer import analyze_project
from backend.core.docker.create_dockerfile import (
    create_dockerfile, save_requirements_file,
    create_dockerignore, build_docker_image
)
from datetime import datetime

from backend.core.runner import image_exists

def build_and_run(github_url: str, project_id: int, image_name: str) -> dict:
    print(f"\nСБОРКА КОНСОЛЬНОГО ПРОЕКТА {project_id}")

    clone = clone_repo(github_url)
    if not clone['success']:
        return {'ok': False, 'error': clone['error']}
    repo_path = clone['path']

    try:
        analysis = analyze_project(repo_path)
        if analysis['error']:
            return {'ok': False, 'error': analysis['error']}

        print(f"Основной файл: {analysis['main_file']}")

        save_requirements_file(repo_path, analysis['requirements'])
        create_dockerignore(repo_path)

        dockerfile_result = create_dockerfile(
            repo_path,
            'console',
            analysis['main_file']
        )
        if not dockerfile_result['success']:
            return {'ok': False, 'error': dockerfile_result['error']}

        build = build_docker_image(repo_path, image_name)
        if not build['success']:
            return {'ok': False, 'error': build['error']}

        _save_project_info(project_id, analysis, image_name)

        from backend.core.runner import run_container
        container, link = run_container(
            image_name, project_id, 'console', analysis['main_file']
        )

        if not container:
            return {'ok': False, 'error': 'Не удалось запустить контейнер'}

        return {'ok': True, 'link': link}

    except Exception as e:
        print(f"Ошибка сборки: {e}")
        return {'ok': False, 'error': str(e)}
    finally:
        delete_repo(repo_path)


def _save_project_info(project_id: int, analysis: dict, image_name: str):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        build_info = f"""[ОБРАЗ СОЗДАН] {datetime.now()}
[ИМЯ ОБРАЗА] {image_name}
[ТИП ПРОЕКТА] console
[ОСНОВНОЙ ФАЙЛ] {analysis['main_file']}
[ВРЕМЯ СБОРКИ] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        cursor.execute("""
            UPDATE student_projects SET build_info = %s WHERE project_id = %s
        """, (build_info, project_id))
        conn.commit()
    finally:
        if cursor: cursor.close()
        if conn: conn.close()