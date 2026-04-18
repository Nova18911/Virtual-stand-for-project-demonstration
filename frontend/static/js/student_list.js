(function () {
    let allStudents = [];
    let currentStudent = null;

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

    window.loadStudentDetail = async function (userId) {
        const response = await fetch(`/api/task/${LAB_ID}/student/${userId}`);
        const data = await response.json();

        if (!data.ok) return;

        currentStudent = data;

        document.querySelectorAll('.student-item').forEach(li => {
            li.classList.toggle('active', parseInt(li.dataset.userId) === userId);
        });

        document.getElementById('hintText').style.display = 'none';
        document.getElementById('studentDetail').style.display = 'flex';
        document.getElementById('studentDetail').style.flexDirection = 'column';

        document.getElementById('githubLink').value = data.github_link || '';
        document.getElementById('commentInput').value = data.teacher_comment || '';

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

        document.querySelectorAll('.grade-btn').forEach(btn => {
            btn.classList.toggle('selected', parseInt(btn.dataset.grade) === data.grade);
        });

        const dockerBlock = document.getElementById('dockerBlock');

        if (data.build_success) {
            dockerBlock.innerHTML = `
                <span class="build-success">✅ Проект собран</span>
            `;
        } else {
            dockerBlock.innerHTML = `
                <button class="btn-docker" id="buildBtn">Осуществить сборку</button>
            `;
            document.getElementById('buildBtn').addEventListener('click', () => buildContainer(userId));
        }
    };

    async function buildContainer(userId) {
        const btn = document.getElementById('buildBtn');
        if (!btn) return;

        btn.disabled = true;
        btn.textContent = 'Проверка...';

        try {
            const detailResponse = await fetch(`/api/task/${LAB_ID}/student/${userId}`);
            const currentData = await detailResponse.json();

            if (!currentData.ok) {
                alert('Не удалось получить данные студента');
                resetBuildButton(btn);
                return;
            }

            const currentGithubLink = currentData.github_link || '';

            const shouldForceRebuild = !currentData.build_success ||
                                      (currentData.github_link && currentData.github_link !== currentGithubLink);

            let url = `/api/task/${LAB_ID}/student/${userId}/build`;

            if (shouldForceRebuild) {
                url += '?force=true';
                showNotification('Обнаружена новая ссылка на GitHub → выполняется пересборка...', 'info');
            } else {
                showNotification('Сборка проекта...', 'info');
            }

            const response = await fetch(url, { method: 'POST' });
            const data = await response.json();

            if (!data.ok) {
                alert(data.error || 'Ошибка при сборке');
                resetBuildButton(btn);
                return;
            }

            showNotification('Сборка запущена...', 'info');

            setTimeout(() => {
                loadStudentDetail(userId);
            }, 2000);

        } catch (err) {
            console.error('Ошибка:', err);
            alert('Ошибка соединения с сервером');
            resetBuildButton(btn);
        }
    }

    function resetBuildButton(btn) {
        btn.disabled = false;
        btn.textContent = 'Осуществить сборку';
    }

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
            btn.textContent = 'Сохранено';
            setTimeout(() => btn.textContent = 'Сохранить', 2000);
        }
    });

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