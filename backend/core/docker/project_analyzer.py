# backend/core/docker/project_analyzer.py

import os


def analyze_project(repo_path: str) -> dict:
    """Анализ только консольных проектов"""
    result = {
        'main_file': None,
        'requirements': [],
        'project_type': 'console',
        'error': None
    }

    if not os.path.exists(repo_path):
        result['error'] = 'Папка репозитория не найдена'
        return result

    # Ищем основной файл
    main_candidates = ['main.py', 'app.py', 'run.py', 'start.py']

    for filename in main_candidates:
        if os.path.exists(os.path.join(repo_path, filename)):
            result['main_file'] = filename
            break

    # Если не нашли — берём первый .py файл в корне
    if not result['main_file']:
        for entry in os.scandir(repo_path):
            if entry.is_file() and entry.name.endswith('.py'):
                result['main_file'] = entry.name
                break

    if not result['main_file']:
        result['error'] = 'Не найден Python файл для запуска'
        return result

    # requirements.txt
    req_path = os.path.join(repo_path, 'requirements.txt')
    if os.path.exists(req_path):
        try:
            with open(req_path, 'r', encoding='utf-8') as f:
                result['requirements'] = [
                    line.strip() for line in f
                    if line.strip() and not line.startswith('#')
                ]
        except:
            pass

    print(f"✅ Консольный проект: {result['main_file']}")
    return result