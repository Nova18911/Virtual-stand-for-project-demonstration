(function () {
    let allStudents = [];
    let currentStudent = null;

    // Функция показа уведомлений
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // --- Загрузка списка студентов ---
    async function loadStudents() {
        const response = await fetch(`/api/task/${LAB_ID}/students`);
        allStudents = await response.json();
        renderStudents(allStudents);

        if (allStudents.length > 0) {
            loadStudentDetail(allStudents[0].user_id);
        }
    }

    function renderStudents(students) {
        const list = document.getElementById('studentList');
        list.innerHTML = '';

        students.forEach((student, index) => {
            const li = document.createElement('li');
            li.className = 'student-item';
            li.dataset.userId = student.user_id;
            li.innerHTML = `
                <a class="student-link" onclick="loadStudentDetail(${student.user_id}); return false;" href="#">
                    ${index + 1} ${student.full_name}
                </a>
            `;
            list.appendChild(li);
        });
    }

    // --- Загрузка данных студента ---
    window.loadStudentDetail = async function (userId) {
        const response = await fetch(`/api/task/${LAB_ID}/student/${userId}`);
        const data = await response.json();

        if (!data.ok) return;

        currentStudent = data;

        // Подсветка активного студента
        document.querySelectorAll('.student-item').forEach(li => {
            li.classList.toggle('active', parseInt(li.dataset.userId) === userId);
        });

        document.getElementById('hintText').style.display = 'none';
        document.getElementById('studentDetail').style.display = 'flex';
        document.getElementById('studentDetail').style.flexDirection = 'column';

        document.getElementById('githubLink').value = data.github_link || '';
        document.getElementById('commentInput').value = data.teacher_comment || '';

        // Получаем статус контейнера
        try {
            const statusResponse = await fetch(`/api/task/${LAB_ID}/student/${userId}/container-status`);
            const statusData = await statusResponse.json();

            if (statusData.ok && statusData.container && statusData.container.link) {
                let fullLink = statusData.container.link;
                if (fullLink.startsWith('/')) {
                    fullLink = window.location.origin + fullLink;
                }
                document.getElementById('containerLink').value = fullLink;

                // Добавляем кликабельную ссылку
                const containerLinkWrapper = document.getElementById('consoleLinkContainer');
                containerLinkWrapper.innerHTML = `
                    <a href="${fullLink}" target="_blank" class="console-link">
                        🔗 Открыть консоль
                    </a>
                `;
            } else {
                document.getElementById('containerLink').value = '';
                document.getElementById('consoleLinkContainer').innerHTML = '';
            }
        } catch (err) {
            console.error('Ошибка получения статуса контейнера:', err);
            document.getElementById('containerLink').value = '';
            document.getElementById('consoleLinkContainer').innerHTML = '';
        }

        // Оценки
        document.querySelectorAll('.grade-btn').forEach(btn => {
            btn.classList.toggle('selected', parseInt(btn.dataset.grade) === data.grade);
        });

        // Docker кнопка
        const dockerBlock = document.getElementById('dockerBlock');

        if (data.build_success) {
            // Образ уже собран — показываем кнопки запуска и пересборки
            const statusResponse2 = await fetch(`/api/task/${LAB_ID}/student/${userId}/container-status`);
            const statusData2 = await statusResponse2.json();

            if (statusData2.ok && statusData2.container?.status === 'running') {
                const isGui = statusData2.container.link?.includes('vnc.html');
                dockerBlock.innerHTML = `
                    <a href="${statusData2.container.link}" target="_blank" class="btn-docker">
                        ${isGui ? '🖥 Открыть GUI' : '💻 Открыть консоль'}
                    </a>
                    <button class="btn-docker" id="rebuildBtn">🔄 Пересобрать</button>
                `;
            } else {
                dockerBlock.innerHTML = `
                    <button class="btn-docker" id="buildBtn">▶️ Запустить</button>
                    <button class="btn-docker" id="rebuildBtn">🔄 Пересобрать</button>
                `;
                document.getElementById('buildBtn').addEventListener('click', () => buildContainer(userId));
            }

            // Обработчик пересборки
            document.getElementById('rebuildBtn')?.addEventListener('click', async () => {
                if (!confirm('Пересобрать проект? Старый образ будет удалён.')) return;
                const btn = document.getElementById('rebuildBtn');
                btn.disabled    = true;
                btn.textContent = '🔄 Сборка...';

                try {
                    const response = await fetch(
                        `/api/task/${LAB_ID}/student/${userId}/rebuild`,
                        { method: 'POST' }
                    );
                    const data = await response.json();
                    if (data.ok) {
                        showNotification('Проект пересобран!', 'success');
                        loadStudentDetail(userId);
                    } else {
                        alert(data.error);
                        btn.disabled    = false;
                        btn.textContent = '🔄 Пересобрать';
                    }
                } catch (err) {
                    alert('Ошибка соединения');
                    btn.disabled    = false;
                    btn.textContent = '🔄 Пересобрать';
                }
            });

        } else {
            // Образ ещё не собран
            dockerBlock.innerHTML = `
                <button class="btn-docker" id="buildBtn">Осуществить сборку</button>
            `;
            document.getElementById('buildBtn').addEventListener('click', () => buildContainer(userId));
        }
            };

    // --- Сборка контейнера ---
    async function buildContainer(userId) {
    const btn       = document.getElementById('buildBtn') || document.getElementById('rebuildBtn');
    btn.disabled    = true;
    btn.textContent = '⏳ Сборка...';

    try {
        const response = await fetch(
            `/api/task/${LAB_ID}/student/${userId}/build`,
            { method: 'POST' }
        );
        const data = await response.json();

        if (!data.ok && !data.status) {
            alert(data.error || 'Ошибка при сборке');
            btn.disabled    = false;
            btn.textContent = 'Осуществить сборку';
            return;
        }

        // Сборка запущена в фоне — опрашиваем статус
        const projectId = data.project_id;
        showNotification('Сборка запущена, ожидайте...', 'info');
        await pollBuildStatus(projectId, userId, btn);

    } catch (err) {
        console.error('Ошибка:', err);
        alert('Ошибка соединения с сервером');
        btn.disabled    = false;
        btn.textContent = 'Осуществить сборку';
    }
    }

    async function pollBuildStatus(projectId, userId, btn) {
        const maxAttempts = 60; // максимум 5 минут (каждые 5 секунд)
        let attempts = 0;

        const interval = setInterval(async () => {
            attempts++;

            try {
                const response = await fetch(`/api/build-status/${projectId}`);
                const data     = await response.json();

                if (data.status === 'done') {
                    clearInterval(interval);
                    showNotification('Контейнер успешно собран!', 'success');
                    loadStudentDetail(userId);
                } else if (data.status === 'error') {
                    clearInterval(interval);
                    alert(`Ошибка сборки: ${data.error}`);
                    btn.disabled    = false;
                    btn.textContent = 'Осуществить сборку';
                } else if (attempts >= maxAttempts) {
                    clearInterval(interval);
                    alert('Превышено время ожидания сборки');
                    btn.disabled    = false;
                    btn.textContent = 'Осуществить сборку';
                } else {
                    btn.textContent = `⏳ Сборка... (${attempts * 5}с)`;
                }
            } catch (err) {
                console.error('Ошибка опроса статуса:', err);
            }
        }, 5000); // опрашиваем каждые 5 секунд
    }

    // --- Оценки ---
    document.getElementById('gradeForm').addEventListener('click', async (e) => {
        if (!e.target.classList.contains('grade-btn')) return;
        if (!currentStudent) return;

        const grade = parseInt(e.target.dataset.grade);

        const response = await fetch(
            `/api/task/${LAB_ID}/student/${currentStudent.user_id}/grade`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ grade })
            }
        );
        const data = await response.json();

        if (data.ok) {
            document.querySelectorAll('.grade-btn').forEach(btn => {
                btn.classList.toggle('selected', parseInt(btn.dataset.grade) === grade);
            });
            currentStudent.grade = grade;
            showNotification(`Оценка ${grade} сохранена`, 'success');
        }
    });

    // --- Комментарий ---
    document.getElementById('saveCommentBtn').addEventListener('click', async () => {
        if (!currentStudent) return;

        const comment = document.getElementById('commentInput').value;
        const response = await fetch(
            `/api/task/${LAB_ID}/student/${currentStudent.user_id}/comment`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ comment })
            }
        );
        const data = await response.json();
        if (data.ok) {
            const btn = document.getElementById('saveCommentBtn');
            btn.textContent = 'Сохранено ✔';
            setTimeout(() => btn.textContent = 'Сохранить', 2000);
        }
    });

    // --- Поиск ---
    document.getElementById('searchBtn').addEventListener('click', () => {
        const query = document.getElementById('searchInput').value.toLowerCase();
        const filtered = allStudents.filter(s =>
            s.full_name.toLowerCase().includes(query)
        );
        renderStudents(filtered);
    });

    document.getElementById('searchInput').addEventListener('keyup', (e) => {
        if (e.key === 'Enter') document.getElementById('searchBtn').click();
    });

    loadStudents();
})();