# backend/core/docker/build_pipeline.py

from backend.core.connect import get_db_connection
from backend.core.docker.git_clone import clone_repo, delete_repo
from backend.core.docker.project_analyzer import analyze_project
from backend.core.docker.create_dockerfile import (
    create_dockerfile, save_requirements_file,
    create_dockerignore, build_docker_image
)
from datetime import datetime
from backend.core.runner import run_container, image_exists


def build_and_run(github_url: str, project_id: int, image_name: str) -> dict:
    """
    Упрощенная сборка только для tkinter
    """
    print(f"\n🚀 СБОРКА TKINTER ПРОЕКТА {project_id}")

    # 1. Клонирование
    print(f"📥 Клонирование: {github_url}")
    clone = clone_repo(github_url)
    if not clone['success']:
        return {'ok': False, 'error': clone['error']}
    repo_path = clone['path']

    try:
        # 2. Анализ
        print(f"🔍 Анализ проекта...")
        analysis = analyze_project(repo_path)
        if analysis['error']:
            return {'ok': False, 'error': analysis['error']}

        print(f"📄 Файл: {analysis['main_file']}")
        print(f"🎨 Тип: GUI (tkinter)")

        # 3. Создаем файлы
        save_requirements_file(repo_path, [])
        create_dockerignore(repo_path)

        dockerfile = create_dockerfile(
            repo_path,
            'gui',
            analysis['main_file']
        )
        if not dockerfile['success']:
            return {'ok': False, 'error': dockerfile['error']}

        # 4. Сборка
        print(f"🔨 Сборка Docker образа...")
        build = build_docker_image(repo_path, image_name)
        if not build['success']:
            return {'ok': False, 'error': build['error']}

        # 5. Сохраняем в БД
        _save_project_info(project_id, analysis, image_name)

        # 6. Запуск
        print(f"🚀 Запуск контейнера...")
        container, link = run_container(
            image_name,
            project_id,
            'gui',
            analysis['main_file']
        )

        if not container:
            return {'ok': False, 'error': 'Ошибка запуска контейнера'}

        print(f"✅ УСПЕШНО! Ссылка: {link}\n")
        return {'ok': True, 'link': link}

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {'ok': False, 'error': str(e)}
    finally:
        delete_repo(repo_path)


def _save_project_info(project_id: int, analysis: dict, image_name: str):
    """Сохраняет информацию в БД"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        build_info = f"""[ОБРАЗ СОЗДАН] {datetime.now()}
[ИМЯ ОБРАЗА] {image_name}
[ТИП ПРОЕКТА] gui
[ОСНОВНОЙ ФАЙЛ] {analysis['main_file']}
[ВРЕМЯ СБОРКИ] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        cursor.execute("""
            UPDATE student_projects
            SET build_info = %s
            WHERE project_id = %s
        """, (build_info, project_id))
        conn.commit()
        print(f"✅ Информация сохранена в БД")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def rebuild_project(github_url: str, project_id: int, image_name: str) -> dict:
    """Пересборка - удаляем старый образ и собираем заново"""
    try:
        import docker
        client = docker.from_env()
        if image_exists(image_name):
            client.images.remove(image_name, force=True)
            print(f"🗑️ Старый образ удален")
    except Exception as e:
        print(f"⚠️ {e}")

    return build_and_run(github_url, project_id, image_name)