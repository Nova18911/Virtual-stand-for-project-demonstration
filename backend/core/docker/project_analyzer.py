import os
import ast

# Имена файлов которые считаются основными точками входа
MAIN_FILE_CANDIDATES = [
    'main.py', 'app.py', 'run.py', 'server.py',
    'start.py', 'index.py', 'manage.py', 'wsgi.py'
]

# Библиотеки по которым определяем тип проекта
WEB_LIBS    = {'flask', 'django', 'fastapi', 'tornado', 'aiohttp', 'bottle', 'starlette'}
GUI_LIBS    = {'tkinter', 'PyQt5', 'PyQt6', 'wx', 'kivy', 'pygame', 'PySide2', 'PySide6'}


def analyze_project(repo_path: str) -> dict:
    """
    Анализирует структуру клонированного репозитория.
    Возвращает словарь с результатами анализа.
    """
    result = {
        'main_file': None,        # основной файл запуска
        'requirements': [],       # список зависимостей
        'requirements_source': None,  # 'file' или 'imports'
        'project_type': 'console',    # console / web / gui
        'error': None
    }

    if not os.path.exists(repo_path):
        result['error'] = 'Папка репозитория не найдена.'
        return result

    # 1. Ищем основной файл
    result['main_file'] = _find_main_file(repo_path)

    # 2. Ищем зависимости
    req_path = os.path.join(repo_path, 'requirements.txt')
    if os.path.exists(req_path):
        result['requirements'] = _parse_requirements_file(req_path)
        result['requirements_source'] = 'file'
    else:
        # Собираем импорты из всех .py файлов
        result['requirements'] = _collect_imports(repo_path)
        result['requirements_source'] = 'imports'

    # 3. Определяем тип проекта по зависимостям
    deps_lower = {d.lower().split('==')[0].split('>=')[0].strip()
                  for d in result['requirements']}

    if deps_lower & WEB_LIBS:
        result['project_type'] = 'web'
    elif deps_lower & GUI_LIBS:
        result['project_type'] = 'gui'
    else:
        result['project_type'] = 'console'

    return result


def _find_main_file(repo_path: str) -> str | None:
    """Ищет основной файл запуска в корне репозитория."""
    for filename in MAIN_FILE_CANDIDATES:
        full_path = os.path.join(repo_path, filename)
        if os.path.exists(full_path):
            return filename

    # Если стандартных нет — берём первый .py файл в корне
    for entry in os.scandir(repo_path):
        if entry.is_file() and entry.name.endswith('.py'):
            return entry.name

    return None


def _parse_requirements_file(req_path: str) -> list:
    """Читает зависимости из requirements.txt."""
    deps = []
    try:
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Пропускаем комментарии и пустые строки
                if line and not line.startswith('#') and not line.startswith('-'):
                    deps.append(line)
    except Exception:
        pass
    return deps


def _collect_imports(repo_path: str) -> list:
    """Собирает все сторонние импорты из .py файлов через AST."""
    imports = set()
    stdlib = _get_stdlib_modules()

    for root, dirs, files in os.walk(repo_path):
        # Пропускаем скрытые папки и venv
        dirs[:] = [d for d in dirs if not d.startswith('.')
                   and d not in ('venv', 'env', '__pycache__', 'node_modules')]

        for filename in files:
            if not filename.endswith('.py'):
                continue
            filepath = os.path.join(root, filename)
            file_imports = _parse_imports_from_file(filepath)
            # Оставляем только сторонние библиотеки
            for imp in file_imports:
                if imp not in stdlib:
                    imports.add(imp)

    return sorted(imports)


def _parse_imports_from_file(filepath: str) -> set:
    """Извлекает имена импортов из одного файла через AST."""
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
    except Exception:
        pass
    return imports


def _get_stdlib_modules() -> set:
    """Возвращает набор стандартных модулей Python."""
    import sys
    stdlib = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else set()

    # Дополнительно на случай старых версий Python
    stdlib.update({
        'os', 'sys', 'io', 're', 'json', 'math', 'time', 'datetime',
        'collections', 'itertools', 'functools', 'pathlib', 'shutil',
        'tempfile', 'subprocess', 'threading', 'multiprocessing',
        'socket', 'http', 'urllib', 'email', 'html', 'xml',
        'sqlite3', 'csv', 'logging', 'unittest', 'typing',
        'abc', 'copy', 'enum', 'hashlib', 'hmac', 'secrets',
        'struct', 'string', 'textwrap', 'traceback', 'warnings',
        'ast', 'dis', 'inspect', 'importlib', 'pkgutil',
        'argparse', 'configparser', 'getpass', 'platform',
        'random', 'statistics', 'decimal', 'fractions',
        'base64', 'binascii', 'codecs', 'uuid', 'zipfile', 'tarfile',
    })
    return stdlib
