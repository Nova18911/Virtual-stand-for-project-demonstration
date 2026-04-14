from project_analyzer import analyze_project
import os
import tempfile

# Создаём тестовую папку с файлами вручную
test_dir = tempfile.mkdtemp(prefix='test_project_')

# Тест 1 — проект с requirements.txt и Flask
print("=== Тест 1: Flask проект с requirements.txt ===")
with open(os.path.join(test_dir, 'main.py'), 'w') as f:
    f.write("from flask import Flask\napp = Flask(__name__)\n")
with open(os.path.join(test_dir, 'requirements.txt'), 'w') as f:
    f.write("flask==2.3.0\nrequests>=2.28.0\n")

info = analyze_project(test_dir)
print(f"Основной файл: {info['main_file']}")        # main.py
print(f"Тип проекта: {info['project_type']}")       # web
print(f"Источник: {info['requirements_source']}")   # file
print(f"Зависимости: {info['requirements']}")

# Тест 2 — проект без requirements.txt (импорты через AST)
print("\n=== Тест 2: Консольный проект без requirements.txt ===")
test_dir2 = tempfile.mkdtemp(prefix='test_project2_')
with open(os.path.join(test_dir2, 'app.py'), 'w') as f:
    f.write("import requests\nimport pandas\nprint('hello')\n")

info2 = analyze_project(test_dir2)
print(f"Основной файл: {info2['main_file']}")       # app.py
print(f"Тип проекта: {info2['project_type']}")      # console
print(f"Источник: {info2['requirements_source']}")  # imports
print(f"Зависимости: {info2['requirements']}")      # ['pandas', 'requests']

# Тест 3 — GUI проект
print("\n=== Тест 3: GUI проект ===")
test_dir3 = tempfile.mkdtemp(prefix='test_project3_')
with open(os.path.join(test_dir3, 'run.py'), 'w') as f:
    f.write("import tkinter as tk\nroot = tk.Tk()\n")

info3 = analyze_project(test_dir3)
print(f"Основной файл: {info3['main_file']}")       # run.py
print(f"Тип проекта: {info3['project_type']}")      # gui

# Тест 4 — пустая папка
print("\n=== Тест 4: Пустая папка ===")
test_dir4 = tempfile.mkdtemp(prefix='test_project4_')
info4 = analyze_project(test_dir4)
print(f"Основной файл: {info4['main_file']}")       # None
print(f"Зависимости: {info4['requirements']}")      # []

print("\nВсе тесты завершены.")