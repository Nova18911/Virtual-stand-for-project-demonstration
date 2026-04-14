# backend/core/docker/git_clone.py

import os
import shutil
import tempfile
import subprocess
import time
import urllib.request
from urllib.error import URLError

REPOS_BASE_DIR = tempfile.gettempdir()


def check_github_connectivity():
    """Проверяет доступность GitHub"""
    try:
        urllib.request.urlopen('https://github.com', timeout=5)
        return True
    except URLError:
        return False


def clone_repo(github_url: str, max_retries: int = 3) -> dict:
    """
    Клонирует репозиторий во временную папку с повторными попытками
    Использует subprocess вместо gitpython для лучшего контроля
    """
    # Проверяем доступность GitHub
    if not check_github_connectivity():
        return {
            'success': False,
            'path': None,
            'error': 'Нет доступа к GitHub. Проверьте интернет-соединение.'
        }

    # Нормализуем URL
    github_url = github_url.strip()

    # Убираем возможные пробелы и спецсимволы
    github_url = github_url.replace(' ', '')

    if not github_url.startswith('https://'):
        if github_url.startswith('git@'):
            github_url = github_url.replace('git@github.com:', 'https://github.com/')
        elif not github_url.startswith('http'):
            github_url = f'https://{github_url}'

    # Добавляем .git если нужно
    if not github_url.endswith('.git'):
        github_url += '.git'

    for attempt in range(max_retries):
        # Создаём уникальную временную директорию
        repo_dir = tempfile.mkdtemp(prefix='vstand_', dir=REPOS_BASE_DIR)

        try:
            print(f"📥 Попытка {attempt + 1}/{max_retries}: Клонирование {github_url}")

            # Используем subprocess вместо gitpython
            cmd = ['git', 'clone', '--depth', '1', github_url, repo_dir]

            print(f"🔧 Команда: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # Таймаут в subprocess, а не в git
            )

            if result.returncode == 0:
                print(f"✅ Репозиторий склонирован в {repo_dir}")
                return {'success': True, 'path': repo_dir, 'error': None}
            else:
                error_msg = result.stderr
                print(f"⚠️ Ошибка клонирования (попытка {attempt + 1}): {error_msg[:200]}")

                # Удаляем папку если клонирование не удалось
                shutil.rmtree(repo_dir, ignore_errors=True)

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1, 2, 4 секунды
                    print(f"⏳ Повтор через {wait_time} секунд...")
                    time.sleep(wait_time)
                    continue

                # Читаемое сообщение об ошибке
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
            print(f"⏰ Таймаут при клонировании (попытка {attempt + 1})")

            if attempt < max_retries - 1:
                time.sleep(2)
                continue

            return {'success': False, 'path': None, 'error': 'Превышено время ожидания при клонировании'}

        except Exception as e:
            shutil.rmtree(repo_dir, ignore_errors=True)
            print(f"❌ Ошибка: {e}")

            if attempt < max_retries - 1:
                time.sleep(2)
                continue

            return {'success': False, 'path': None, 'error': f'Ошибка: {str(e)}'}

    return {'success': False, 'path': None, 'error': 'Не удалось клонировать репозиторий после нескольких попыток'}


def delete_repo(repo_path: str) -> bool:
    """Удаляет временную папку с репозиторием"""
    try:
        if repo_path and os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)
            print(f"🗑️ Удалена временная папка: {repo_path}")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Ошибка удаления {repo_path}: {e}")
        return False


def test_clone(github_url: str):
    """Тестовая функция для проверки клонирования"""
    print(f"🧪 Тестируем клонирование: {github_url}")
    result = clone_repo(github_url)

    if result['success']:
        print(f"✅ Успешно! Папка: {result['path']}")
        delete_repo(result['path'])
    else:
        print(f"❌ Ошибка: {result['error']}")

    return result