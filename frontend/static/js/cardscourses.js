let cardsData = [];

async function loadCoursesFromServer() {
    try {
        const response = await fetch('/api/courses');
        cardsData = await response.json();
        renderCards(cardsData); 
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

        if (!item.is_enrolled) {
            article.classList.add('course-locked');
        }

        const courseLink = document.createElement('a');

        if (item.is_enrolled) {
            courseLink.href = `/course/${item.id}`;
            courseLink.className = 'course-link';
            courseLink.textContent = item.course;
        } else {
            courseLink.href = '#';
            courseLink.className = 'course-link locked';
            courseLink.textContent = `🔒 ${item.course}`;
            courseLink.onclick = (e) => {
                e.preventDefault();
                alert('У вас нет доступа к этому курсу. Обратитесь к администратору или преподавателю для добавления.');
            };
        }

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

    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            filterCourses(input.value);
        });
    }

    if (input) {
        input.addEventListener('input', () => {
            filterCourses(input.value);
        });
    }
});