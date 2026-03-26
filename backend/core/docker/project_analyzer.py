import os
import ast

# Имена файлов которые считаются основными точками входа
MAIN_FILE_CANDIDATES = [
    'main.py', 'app.py', 'run.py', 'server.py',
    'start.py', 'index.py', 'manage.py', 'wsgi.py'
]

# Библиотеки по которым определяем тип проекта
WEB_LIBS = {'flask', 'django', 'fastapi', 'tornado', 'aiohttp', 'bottle', 'starlette'}
GUI_LIBS = {'tkinter', 'pyqt5', 'pyqt6', 'wx', 'kivy', 'pygame', 'pyside2', 'pyside6'}

# Папки которые пропускаем при сканировании
SKIP_DIRS = {
    'venv', 'env', '.venv', '__pycache__', 'node_modules',
    '.git', 'dist', 'build', '.eggs', '.tox',
    'docs', 'doc', 'documentation',
    'examples', 'example', 'samples', 'sample',
    'benchmarks', 'benchmark', 'tests', 'test',
}

# Файлы которые пропускаем
SKIP_FILE_PREFIXES = ('test_', 'conftest', 'setup', 'conf')

# Python 2 / compat модули которые выглядят как сторонние, но не являются ими
COMPAT_MODULES = {
    'StringIO', 'cStringIO', 'dummy_threading', 'UserDict',
    'UserList', 'UserString', 'ConfigParser', 'Queue',
    '__builtin__', '__future__', 'exceptions',
}


def analyze_project(repo_path: str) -> dict:
    """
    Анализирует структуру клонированного репозитория.
    Возвращает словарь с результатами анализа.
    """
    result = {
        'main_file': None,
        'requirements': [],
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
        result['requirements'] = _collect_imports(repo_path)
        result['requirements_source'] = 'imports'

    # 3. Определяем тип проекта по зависимостям + именам внутренних модулей
    # (нужно для случая когда сам репозиторий и есть веб-фреймворк, напр. Flask)
    internal_names = _get_internal_module_names(repo_path)
    all_names = {n.lower() for n in internal_names} | {d.lower().split('==')[0].split('>=')[0].strip()
                  for d in result["requirements"]}

    if all_names & WEB_LIBS:
        result['project_type'] = 'web'
    elif all_names & GUI_LIBS:
        result['project_type'] = 'gui'
    else:
        result['project_type'] = 'console'

    return result


def _find_main_file(repo_path: str) -> str | None:
    """Ищет основной файл запуска в корне репозитория."""
    for filename in MAIN_FILE_CANDIDATES:
        if os.path.exists(os.path.join(repo_path, filename)):
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
                if line and not line.startswith('#') and not line.startswith('-'):
                    deps.append(line)
    except Exception:
        pass
    return deps


def _collect_imports(repo_path: str) -> list:
    """
    Собирает сторонние импорты из .py файлов через AST.
    AST корректно игнорирует строки, docstring и комментарии.
    Фильтрует stdlib, внутренние модули проекта и compat-модули.
    """
    imports = set()
    stdlib = _get_stdlib_modules()

    # Собираем имена всех внутренних модулей рекурсивно
    internal = _get_internal_module_names(repo_path)

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith('.')
        ]

        for filename in files:
            if not filename.endswith('.py'):
                continue
            if filename.startswith(SKIP_FILE_PREFIXES):
                continue

            filepath = os.path.join(root, filename)
            raw = _parse_imports_via_ast(filepath)

            for name in raw:
                if (name
                        and name not in stdlib
                        and name not in internal
                        and name not in COMPAT_MODULES
                        and not name.startswith('_')):
                    imports.add(name)

    return sorted(imports)


def _get_internal_module_names(repo_path: str) -> set:
    """
    Рекурсивно собирает имена всех внутренних модулей проекта:
    каждое имя папки и каждое имя .py файла (без расширения).
    """
    names = set()
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for d in dirs:
            names.add(d)
        for f in files:
            if f.endswith('.py'):
                names.add(f[:-3])
    return names


def _parse_imports_via_ast(filepath: str) -> set:
    """
    Извлекает верхнеуровневые имена пакетов через AST.
    AST парсит только реальный Python-код, игнорируя
    строки, docstring и комментарии.
    """
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split('.')[0]
                    if top:
                        imports.add(top)
            elif isinstance(node, ast.ImportFrom):
                # level > 0 — относительный импорт (from . import ...), пропускаем
                if node.level == 0 and node.module:
                    top = node.module.split('.')[0]
                    if top:
                        imports.add(top)
    except Exception:
        pass
    return imports


def _get_stdlib_modules() -> set:
    """Возвращает набор стандартных модулей Python."""
    import sys
    stdlib = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else set()

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