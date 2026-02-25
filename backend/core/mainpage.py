from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify

mainpage_bp = Blueprint('mainpage', __name__)

# Тестовые курсы (заглушка вместо БД)
courses = [
    {
        "id": 1,
        "course": "МДК 07.02",
        "work": "Лабораторная работа №2",
        "description": "Задание смотреть в прикреплённом файле",
        "teacher": "Самоделкин П.А. Преподаватель университета",
        "teacher_id": 2,
        "created_at": "2026-02-20",
        "attachments": ["file1.pdf", "file2.docx"]
    },
    {
        "id": 2,
        "course": "Информационные системы и технологии",
        "work": "Практическая №1",
        "deadline": "Сдать до 05.02.26!",
        "teacher": "Жилова Ю.А. Преподаватель университета",
        "teacher_id": 3,
        "created_at": "2026-02-21",
        "attachments": []
    }
]


@mainpage_bp.route('/api/courses')
def get_courses():

    formatted_courses = []
    for course in courses:
        formatted_course = {
            "course": course["course"],
            "work": course["work"],
            "teacher": course["teacher"]
        }

        if "description" in course:
            formatted_course["description"] = course["description"]
        if "deadline" in course:
            formatted_course["deadline"] = course["deadline"]

        formatted_courses.append(formatted_course)

    return jsonify(formatted_courses)