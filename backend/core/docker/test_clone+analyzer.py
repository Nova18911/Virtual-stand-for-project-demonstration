from project_analyzer import analyze_project
from git_clone import clone_repo, delete_repo

def run_test(label: str, url: str):
    print(f"\n=== {label} ===")
    print(f"URL: {url}")

    # Клонируем репозиторий
    result = clone_repo(url)
    print(f"Клонирование: {'успешно' if result['success'] else 'ошибка'}")

    if not result['success']:
        print(f"Ошибка: {result['error']}")
        return

    print(f"Путь: {result['path']}")

    # Анализируем склонированный репозиторий
    info = analyze_project(result['path'])
    print(f"Основной файл: {info['main_file']}")
    print(f"Тип проекта:   {info['project_type']}")
    print(f"Источник зав.: {info['requirements_source']}")
    print(f"Зависимости:   {info['requirements']}")

    # Удаляем временную папку
    delete_repo(result['path'])
    print("Временная папка удалена.")


print("=" * 50)
print("  ТЕСТЫ: КЛОНИРОВАНИЕ + АНАЛИЗ")
print("=" * 50)

# Тест 1 — Flask (web-проект, есть requirements.txt)
run_test(
    "Тест 1: Flask (web, requirements.txt)",
    "https://github.com/pallets/flask"
)

# Тест 2 — консольный проект
run_test(
    "Тест 2: Requests (консольная библиотека)",
    "https://github.com/psf/requests"
)

# Тест 3 — несуществующий репозиторий
run_test(
    "Тест 3: Несуществующий репозиторий",
    "https://github.com/nonexistent/fakerepo999"
)

# Тест 4 — неверная ссылка (не GitHub)
run_test(
    "Тест 4: Неверная ссылка (не GitHub)",
    "https://google.com"
)

print("\n" + "=" * 50)
print("  ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
print("=" * 50)