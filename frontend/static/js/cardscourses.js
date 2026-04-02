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

function renderCards() {
    const container = document.getElementById('cardsContainer');
    container.innerHTML = '';

    cardsData.forEach(item => {
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

document.addEventListener('DOMContentLoaded', loadCoursesFromServer);