(function () {
    let allStudents    = [];
    let currentStudent = null;

    // --- Загрузка списка студентов ---
    async function loadStudents() {
        const response = await fetch(`/api/task/${LAB_ID}/students`);
        allStudents    = await response.json();
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
        const data     = await response.json();

        if (!data.ok) return;

        currentStudent = data;

        // Подсветка активного студента
        document.querySelectorAll('.student-item').forEach(li => {
            li.classList.toggle('active', parseInt(li.dataset.userId) === userId);
        });

        document.getElementById('hintText').style.display    = 'none';
        document.getElementById('studentDetail').style.display = 'flex';
        document.getElementById('studentDetail').style.flexDirection = 'column';

        document.getElementById('githubLink').value   = data.github_link || '';
        document.getElementById('commentInput').value = data.teacher_comment || '';
        document.getElementById('containerLink').value =
            data.container?.status === 'running' ? data.container.link : '';

        // Оценки
        document.querySelectorAll('.grade-btn').forEach(btn => {
            btn.classList.toggle('selected', parseInt(btn.dataset.grade) === data.grade);
        });

        // Docker кнопка
        const dockerBlock = document.getElementById('dockerBlock');
        if (data.container?.status === 'running') {
            dockerBlock.innerHTML = `
                <a href="${data.container.link}" target="_blank" class="btn-docker">
                    Открыть проект
                </a>`;
        } else {
            dockerBlock.innerHTML = `
                <button class="btn-docker" id="buildBtn">Осуществить сборку</button>`;
            document.getElementById('buildBtn').addEventListener('click', () => buildContainer(userId));
        }
    };

    // --- Сборка контейнера ---
    async function buildContainer(userId) {
        const btn = document.getElementById('buildBtn');
        btn.disabled   = true;
        btn.textContent = 'Сборка...';

        try {
            const response = await fetch(
                `/api/task/${LAB_ID}/student/${userId}/build`,
                { method: 'POST' }
            );
            const data = await response.json();

            if (data.ok) {
                loadStudentDetail(userId);
            } else {
                alert(data.error || 'Ошибка при сборке');
                btn.disabled    = false;
                btn.textContent = 'Осуществить сборку';
            }
        } catch (err) {
            alert('Ошибка соединения с сервером');
            btn.disabled    = false;
            btn.textContent = 'Осуществить сборку';
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
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ grade })
            }
        );
        const data = await response.json();

        if (data.ok) {
            document.querySelectorAll('.grade-btn').forEach(btn => {
                btn.classList.toggle('selected', parseInt(btn.dataset.grade) === grade);
            });
            currentStudent.grade = grade;
        }
    });

    // --- Комментарий ---
    document.getElementById('saveCommentBtn').addEventListener('click', async () => {
        if (!currentStudent) return;

        const comment  = document.getElementById('commentInput').value;
        const response = await fetch(
            `/api/task/${LAB_ID}/student/${currentStudent.user_id}/comment`,
            {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ comment })
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
        const query    = document.getElementById('searchInput').value.toLowerCase();
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