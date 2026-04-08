let cardsData = [];

async function loadCoursesFromServer() {
    try {
        const response = await fetch('/api/courses');
        cardsData = await response.json();
        renderCards();
    } catch (error) {
        console.error('Ошибка при загрузке курсов:', error);
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
        
        // Если студент не записан, добавляем класс для стилизации (серость/замок)
        if (!item.is_enrolled) {
            article.classList.add('course-locked');
        }

        const courseLink = document.createElement('a');
        
        if (item.is_enrolled) {
            // Если доступ есть — обычная ссылка
            courseLink.href = `/tasks/course/${item.id}`;
            courseLink.className = 'course-link';
        } else {
            // Если доступа нет — ссылка никуда не ведет и вешаем спец. класс
            courseLink.href = '#'; 
            courseLink.className = 'course-link locked';
            // Можно добавить уведомление при клике
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