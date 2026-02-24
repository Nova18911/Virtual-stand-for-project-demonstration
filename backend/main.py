from flask import Flask, render_template

# Указываем Flask, где искать папки со страницами и стилями
app = Flask(__name__,
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

@app.route('/mainpage')
def register_page():
    return render_template('mainpage.html')

if __name__ == '__main__':
    app.run(debug=True)