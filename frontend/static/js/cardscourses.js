let cardsData = [];

async function loadCoursesFromServer() {
    const response = await fetch('/api/courses');
    cardsData = await response.json();
    renderCards();
}

function renderCards() {
    const container = document.getElementById('cardsContainer');
    container.innerHTML = '';

    cardsData.forEach(item => {
        const article = document.createElement('article');

        const courseLink = document.createElement('a');
        // Теперь ссылка ведет на тестовый маршрут с параметром course_id
        courseLink.href = `/tasks/course/${item.id}`;
        courseLink.textContent = item.course;
        courseLink.className = 'course-link';

        const teacherP = document.createElement('p');
        teacherP.textContent = item.teacher;
        teacherP.className = 'teacher-text';

        article.appendChild(courseLink);
        article.appendChild(teacherP);
        container.appendChild(article);
    });
}

document.addEventListener('DOMContentLoaded', loadCoursesFromServer);