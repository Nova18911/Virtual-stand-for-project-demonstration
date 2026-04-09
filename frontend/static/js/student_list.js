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

        // === Docker блок ===
        const dockerBlock = document.getElementById('dockerBlock');

        if (data.build_success) {
            dockerBlock.innerHTML = `
                <button class="btn-docker" id="runBtn">▶️ Запустить</button>
                <button class="btn-docker" id="rebuildBtn">🔄 Пересобрать</button>
            `;

            document.getElementById('runBtn').addEventListener('click', () => runContainer(userId));
            document.getElementById('rebuildBtn').addEventListener('click', () => rebuildContainer(userId));

        } else {
            dockerBlock.innerHTML = `
                <button class="btn-docker" id="buildBtn">Осуществить сборку</button>
            `;
            document.getElementById('buildBtn').addEventListener('click', () => buildContainer(userId));
        }
    };

    // --- Сборка контейнера ---
    async function buildContainer(userId) {
        const btn = document.getElementById('buildBtn') || document.getElementById('rebuildBtn');
        if (!btn) return;

        btn.disabled = true;
        btn.textContent = '⏳ Сборка...';

        try {
            const response = await fetch(`/api/task/${LAB_ID}/student/${userId}/build`, {
                method: 'POST'
            });
            const data = await response.json();

            if (!data.ok) {
                alert(data.error || 'Ошибка при сборке');
                btn.disabled = false;
                btn.textContent = 'Осуществить сборку';
                return;
            }

            showNotification('Сборка началась...', 'info');

            // Обновляем информацию через небольшую задержку
            setTimeout(() => {
                loadStudentDetail(userId);
            }, 2000);

        } catch (err) {
            console.error('Ошибка:', err);
            alert('Ошибка соединения с сервером');
            btn.disabled = false;
            btn.textContent = 'Осуществить сборку';
        }
    }

    // --- Запуск контейнера ---
    async function runContainer(userId) {
        try {
            const res = await fetch(`/api/task/${LAB_ID}/student/${userId}/run`, {
                method: 'POST'
            });
            const data = await res.json();

            if (data.ok) {
                showNotification('Контейнер запущен!', 'success');
                loadStudentDetail(userId);
            } else {
                alert(data.error || 'Не удалось запустить контейнер');
            }
        } catch (e) {
            alert('Ошибка запуска контейнера');
        }
    }

    // --- Пересборка ---
    async function rebuildContainer(userId) {
        if (!confirm('Пересобрать проект? Старый образ будет удалён.')) return;

        const btn = document.getElementById('rebuildBtn');
        btn.disabled = true;
        btn.textContent = '🔄 Пересборка...';

        try {
            const res = await fetch(`/api/task/${LAB_ID}/student/${userId}/rebuild`, {
                method: 'POST'
            });
            const data = await res.json();

            if (data.ok) {
                showNotification('Пересборка началась...', 'success');
                setTimeout(() => loadStudentDetail(userId), 2500);
            } else {
                alert(data.error || 'Ошибка пересборки');
            }
        } catch (e) {
            alert('Ошибка соединения');
        } finally {
            btn.disabled = false;
            btn.textContent = '🔄 Пересобрать';
        }
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