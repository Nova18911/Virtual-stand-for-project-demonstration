import os
import re
import ast
from collections import defaultdict

PACKAGE_MAPPING = {
    # Основные для анализа данных
    'pandas': 'pandas',
    'numpy': 'numpy',

    # Визуализация
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'plotly': 'plotly',

    # Научные вычисления
    'scipy': 'scipy',
    'sympy': 'sympy',

    # Работа с файлами и данными
    'openpyxl': 'openpyxl',
    'requests': 'requests',
    'beautifulsoup4': 'beautifulsoup4',
    'pillow': 'pillow',

    # Удобства для консоли
    'tabulate': 'tabulate',
    'colorama': 'colorama',
    'tqdm': 'tqdm',

    # Стандартные библиотека Python
    'os': None,
    'sys': None,
    'math': None,
    'random': None,
    'datetime': None,
    'time': None,
    'json': None,
    'csv': None,
    'collections': None,
    'itertools': None,
}


def analyze_project(repo_path: str) -> dict:
    result = {
        'main_file': None,
        'requirements': [],
        'project_type': 'console',
        'error': None
    }

    if not os.path.exists(repo_path):
        result['error'] = 'Папка репозитория не найдена'
        return result

    main_candidates = ['main.py', 'app.py', 'run.py', 'start.py']
    py_files = []

    for entry in os.scandir(repo_path):
        if entry.is_file() and entry.name.endswith('.py'):
            py_files.append(entry.name)
            if entry.name in main_candidates:
                result['main_file'] = entry.name
                break

    if not result['main_file'] and py_files:
        result['main_file'] = py_files[0]

    if not result['main_file']:
        result['error'] = 'Не найден главный Python файл'
        return result

    print(f"✅ Главный файл: {result['main_file']}")

    dependencies = set()

    for py_file in py_files:
        file_path = os.path.join(repo_path, py_file)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()

            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        pkg = alias.name.split('.')[0]
                        if pkg in PACKAGE_MAPPING and PACKAGE_MAPPING[pkg]:
                            dependencies.add(PACKAGE_MAPPING[pkg])

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        pkg = node.module.split('.')[0]
                        if pkg in PACKAGE_MAPPING and PACKAGE_MAPPING[pkg]:
                            dependencies.add(PACKAGE_MAPPING[pkg])

        except Exception as e:
            print(f"Не удалось проанализировать {py_file}: {e}")

    result['requirements'] = sorted(list(dependencies))

    req_path = os.path.join(repo_path, "requirements.txt")
    try:
        with open(req_path, "w", encoding="utf-8") as f:
            if result['requirements']:
                f.write("\n".join(result['requirements']) + "\n")
                print(f"Создан requirements.txt: {result['requirements']}")
            else:
                f.write("# Нет автоматически обнаруженных зависимостей\n")
    except Exception as e:
        print(f"Не удалось создать requirements.txt: {e}")

    return result