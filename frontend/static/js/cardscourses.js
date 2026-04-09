let cardsData = [];

async function loadCoursesFromServer() {
    try {
        const response = await fetch('/api/courses');
        cardsData = await response.json();
        renderCards(cardsData); // ✅ передаём cardsData явно
    } catch (error) {
        console.error('Ошибка при загрузке курсов:', error);
        // Скрипт не падает — кнопки и события продолжают работать
    }
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

        if (!item.is_enrolled) {
            article.classList.add('course-locked');
        }

        const courseLink = document.createElement('a');

        if (item.is_enrolled) {
            courseLink.href = `/tasks/course/${item.id}`;
            courseLink.className = 'course-link';
        } else {
            courseLink.href = '#';
            courseLink.className = 'course-link locked';
            courseLink.onclick = (e) => {
                e.preventDefault();
                alert('У вас нет доступа к этому курсу. Обратитесь к преподавателю.');
            };
        }

        courseLink.textContent = item.is_enrolled ? item.course : `🔒 ${item.course}`;

        const teacherP = document.createElement('p');
        teacherP.textContent = `Преподаватель: ${item.teacher}`;
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

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        filterCourses(input.value);
    });

    input.addEventListener('input', () => {
        filterCourses(input.value);
    });
});