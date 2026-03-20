import os
import shutil
import tempfile
import git  # pip install gitpython

# Папка для временных репозиториев
REPOS_BASE_DIR = tempfile.gettempdir()


def clone_repo(github_url: str) -> dict:
    """
    Клонирует репозиторий во временную папку.
    Возвращает словарь с результатом: success, path, error.
    """
    # Проверяем что ссылка похожа на GitHub
    if 'github.com' not in github_url:
        return {'success': False, 'path': None, 'error': 'Ссылка должна быть на GitHub репозиторий.'}

    # Создаём уникальную временную директорию
    repo_dir = tempfile.mkdtemp(prefix='vstand_', dir=REPOS_BASE_DIR)

    try:
        git.Repo.clone_from(github_url, repo_dir)
        return {'success': True, 'path': repo_dir, 'error': None}

    except git.exc.GitCommandError as e:
        # Удаляем папку если клонирование не удалось
        shutil.rmtree(repo_dir, ignore_errors=True)

        # Читаемое сообщение об ошибке
        if 'Repository not found' in str(e) or '404' in str(e):
            error = 'Репозиторий не найден. Проверьте ссылку или доступность репозитория.'
        elif 'Authentication failed' in str(e):
            error = 'Ошибка доступа. Репозиторий приватный.'
        elif 'not a git repository' in str(e):
            error = 'Указанный URL не является git-репозиторием.'
        else:
            error = f'Ошибка клонирования: {str(e)}'

        return {'success': False, 'path': None, 'error': error}

    except Exception as e:
        shutil.rmtree(repo_dir, ignore_errors=True)
        return {'success': False, 'path': None, 'error': f'Неожиданная ошибка: {str(e)}'}


def delete_repo(repo_path: str) -> bool:
    """Удаляет временную папку с репозиторием."""
    try:
        if repo_path and os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            return True
        return False
    except Exception:
        return False
