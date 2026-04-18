import os
import shutil
import tempfile
import subprocess
import time
import urllib.request
from urllib.error import URLError

REPOS_BASE_DIR = tempfile.gettempdir()


def check_github_connectivity():
    try:
        urllib.request.urlopen('https://github.com', timeout=5)
        return True
    except URLError:
        return False


def clone_repo(github_url: str, max_retries: int = 3) -> dict:
    if not check_github_connectivity():
        return {
            'success': False,
            'path': None,
            'error': 'Нет доступа к GitHub. Проверьте интернет-соединение.'
        }

    github_url = github_url.strip()

    github_url = github_url.replace(' ', '')

    if not github_url.startswith('https://'):
        if github_url.startswith('git@'):
            github_url = github_url.replace('git@github.com:', 'https://github.com/')
        elif not github_url.startswith('http'):
            github_url = f'https://{github_url}'

    if not github_url.endswith('.git'):
        github_url += '.git'

    for attempt in range(max_retries):
        repo_dir = tempfile.mkdtemp(prefix='vstand_', dir=REPOS_BASE_DIR)

        try:
            cmd = ['git', 'clone', '--depth', '1', github_url, repo_dir]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print(f"Репозиторий склонирован в {repo_dir}")
                return {'success': True, 'path': repo_dir, 'error': None}
            else:
                error_msg = result.stderr
                print(f"Ошибка клонирования (попытка {attempt + 1}): {error_msg[:200]}")

                shutil.rmtree(repo_dir, ignore_errors=True)

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue

                if 'Repository not found' in error_msg or '404' in error_msg:
                    error = 'Репозиторий не найден. Проверьте ссылку.'
                elif 'Authentication failed' in error_msg or '403' in error_msg:
                    error = 'Нет доступа к репозиторию. Возможно, он приватный.'
                elif 'Could not resolve host' in error_msg:
                    error = 'Не удаётся подключиться к GitHub. Проверьте интернет.'
                elif 'timeout' in error_msg.lower():
                    error = 'Превышено время ожидания. Попробуйте позже.'
                else:
                    error = f'Ошибка клонирования: {error_msg[:200]}'

                return {'success': False, 'path': None, 'error': error}

        except subprocess.TimeoutExpired:
            shutil.rmtree(repo_dir, ignore_errors=True)

            if attempt < max_retries - 1:
                time.sleep(2)
                continue

            return {'success': False, 'path': None, 'error': 'Превышено время ожидания при клонировании'}

        except Exception as e:
            shutil.rmtree(repo_dir, ignore_errors=True)
            print(f"Ошибка: {e}")

            if attempt < max_retries - 1:
                time.sleep(2)
                continue

            return {'success': False, 'path': None, 'error': f'Ошибка: {str(e)}'}

    return {'success': False, 'path': None, 'error': 'Не удалось клонировать репозиторий после нескольких попыток'}


def delete_repo(repo_path: str) -> bool:
    try:
        if repo_path and os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)
            print(f"Удалена временная папка: {repo_path}")
            return True
        return False
    except Exception as e:
        print(f"Ошибка удаления {repo_path}: {e}")
        return False


def test_clone(github_url: str):
    #Тестовая функция для проверки клонирования
    print(f"Тестируем клонирование: {github_url}")
    result = clone_repo(github_url)

    if result['success']:
        print(f"Успешно! Папка: {result['path']}")
        delete_repo(result['path'])
    else:
        print(f"Ошибка: {result['error']}")

    return result