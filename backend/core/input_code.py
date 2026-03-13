from flask import Blueprint, render_template, request, jsonify, session
from bs4 import BeautifulSoup
import os

inputcode_bp = Blueprint('inputcode', __name__)


def get_code_from_letter():
    # Путь от backend/core/ до frontend/templates/letter.html
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    letter_path = os.path.join(base_dir, 'frontend', 'templates', 'letter.html')
    with open(letter_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    code_div = soup.find(class_='digit-code')
    return code_div.get_text(strip=True) if code_div else None


@inputcode_bp.route('/inputcode')
def inputcode_page():
    code = get_code_from_letter()
    if code:
        session['correct_code'] = code
    return render_template('input_code.html')


@inputcode_bp.route('/inputcode', methods=['POST'])
def verify_code():
    entered_code = ''.join([
        request.form.get('input_code1', ''),
        request.form.get('input_code2', ''),
        request.form.get('input_code3', ''),
        request.form.get('input_code4', ''),
        request.form.get('input_code5', ''),
        request.form.get('input_code6', '')
    ])

    correct_code = session.get('correct_code')
    print(f"Получен код: {entered_code}, правильный: {correct_code}")

    if correct_code and entered_code == correct_code:
        return jsonify({'success': True, 'message': 'Код верный', 'redirect': '/changepassword'})
    else:
        return jsonify({'success': False, 'message': 'Неверный код'}), 400