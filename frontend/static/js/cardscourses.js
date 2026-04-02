let cardsData = [];

async function loadCoursesFromServer() {
    const response = await fetch('/api/courses');
    cardsData = await response.json();
    renderCards(cardsData);
}

function renderCards(data) {
    const container = document.getElementById('cardsContainer');
    container.innerHTML = '';

    if (data.length === 0) {
        container.innerHTML = '<p class="no-results">Ничего не найдено</p>';
        return;
    }

    data.forEach(item => {
        const article = document.createElement('article');

        const courseLink = document.createElement('a');
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

function filterCourses(query) {
    const q = query.trim().toLowerCase();
    if (!q) {
        renderCards(cardsData);
        return;
    }
    const filtered = cardsData.filter(item =>
        item.course.toLowerCase().includes(q) ||
        item.teacher.toLowerCase().includes(q)
    );
    renderCards(filtered);
}

document.addEventListener('DOMContentLoaded', () => {
    loadCoursesFromServer();

    const form = document.getElementById('searchForm');
    const input = document.getElementById('searchInput');

    // Поиск при отправке формы (кнопка «Искать»)
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        filterCourses(input.value);
    });

    // Поиск в реальном времени по мере набора
    input.addEventListener('input', () => {
        filterCourses(input.value);
    });
});