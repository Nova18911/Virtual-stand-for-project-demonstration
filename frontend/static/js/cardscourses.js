let cardsData = [];

// Функция загрузки данных с сервера
async function loadCoursesFromServer() {
    const response = await fetch('/api/courses');
    cardsData = await response.json();
    renderCards();
}

function handleAddAnswer(courseName, workName) {
    alert(`Добавить ответ для: ${courseName} - ${workName}`);
    console.log('Добавить ответ:', courseName, workName);
}

function renderCards() {
    const container = document.getElementById('cardsContainer');
    container.innerHTML = '';

    cardsData.forEach(item => {
        const article = document.createElement('article');
        const h3 = document.createElement('h3');
        const workP = document.createElement('p');
        const workStrong = document.createElement('strong');
        const descP = document.createElement('p');
        const teacherP = document.createElement('p');
        const teacherA = document.createElement('a');
        const answerDiv = document.createElement('div');
        const answerButton = document.createElement('button');

        h3.textContent = item.course;
        workStrong.textContent = item.work;
        workP.appendChild(workStrong);

        if (item.description) {
            descP.textContent = item.description;
        } else if (item.deadline) {
            descP.textContent = item.deadline;
        }

        teacherA.href = '#';
        teacherA.textContent = item.teacher;
        teacherP.appendChild(teacherA);

        answerButton.textContent = 'Добавить ответ';
        answerButton.type = 'button';
        answerButton.onclick = function() {
            handleAddAnswer(item.course, item.work);
        };

        answerButton.className = 'add-answer-btn';

        answerDiv.appendChild(answerButton);

        article.appendChild(h3);
        article.appendChild(workP);
        article.appendChild(descP);
        article.appendChild(teacherP);
        article.appendChild(answerDiv);

        container.appendChild(article);
    });
}

document.addEventListener('DOMContentLoaded', loadCoursesFromServer);