const cardsData = [
    {
        course: "МДК 07.02",
        work: "Лабораторная работа №2",
        description: "Задание смотреть в прикреплённом файле",
        teacher: "Самоделкин П.А. Преподаватель университета"
    },
    {
        course: "Информационные системы и технологии",
        work: "Практическая №1",
        deadline: "Сдать до 05.02.26!",
        teacher: "Жилова Ю.А. Преподаватель университета"
    }
];

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

document.addEventListener('DOMContentLoaded', renderCards);