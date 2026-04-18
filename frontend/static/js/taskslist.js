(function () {

    async function loadTasks() {
        const response = await fetch(`/api/course/${COURSE_ID}/labs`);
        const labs     = await response.json();
        renderTasks(labs);
    }

    function renderTasks(labs) {
        const list = document.getElementById('taskList');
        list.innerHTML = '';

        if (labs.length === 0) {
            list.innerHTML = '<li class="task-item">Заданий пока нет.</li>';
            return;
        }

        labs.forEach(lab => {
            const li = document.createElement('li');
            li.className = 'task-item';

            let fileBtn = '';
            if (lab.has_file) {
                const fileName = lab.filename || 'Файл';
                fileBtn = `
                    <div class="task-file-info">
                        <a href="/api/task/${lab.id}/file" class="btn btn-file" download>
                            📎 ${escapeHtml(fileName)}
                        </a>
                    </div>
                `;
            }

            if (ROLE === 'teacher') {
                li.innerHTML = `
                    <a href="/task/${lab.id}" class="task-name">${escapeHtml(lab.name)}</a>
                    <div class="task-actions">
                        <span class="task-dates">${lab.start_date} — ${lab.end_date}</span>
                        ${fileBtn}
                        <button class="btn btn-edit" onclick="openEditModal(${lab.id})">Редактировать</button>
                    </div>
                `;
            } else {
                li.innerHTML = `
                    <a href="/tasks/${lab.id}" class="task-name">${escapeHtml(lab.name)}</a>
                    <div class="task-actions">
                        <span class="task-dates">${lab.start_date} — ${lab.end_date}</span>
                        ${fileBtn}
                        <span class="status ${lab.submitted ? 'status-done' : 'status-not-done'}">
                            ${lab.submitted ? '✔ Выполнено' : 'Не выполнено'}
                        </span>
                    </div>
                `;
            }
            list.appendChild(li);
        });
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>]/g, function(m) {
            if (m === '&') return '&amp;';
            if (m === '<') return '&lt;';
            if (m === '>') return '&gt;';
            return m;
        });
    }

    if (ROLE === 'teacher') {

        function setMinDeadline() {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const minDateStr = tomorrow.toISOString().split('T')[0];

            const addInput = document.getElementById('taskDeadline');
            const editInput = document.getElementById('editTaskDeadline');

            if (addInput) addInput.setAttribute('min', minDateStr);
            if (editInput) editInput.setAttribute('min', minDateStr);
        }

        const addModal   = document.getElementById('addTaskModal');
        const openBtn    = document.getElementById('openModalBtn');
        const closeBtn   = document.getElementById('closeModalBtn');
        const cancelBtn  = document.getElementById('cancelModalBtn');
        const submitBtn  = document.getElementById('submitTaskBtn');
        const modalError = document.getElementById('modalError');

        openBtn.addEventListener('click',   () => {
            setMinDeadline();
            addModal.style.display = 'flex';
        });
        closeBtn.addEventListener('click',  () => closeAddModal());
        cancelBtn.addEventListener('click', () => closeAddModal());
        addModal.addEventListener('click',  (e) => { if (e.target === addModal) closeAddModal(); });

        function closeAddModal() {
            addModal.style.display   = 'none';
            modalError.style.display = 'none';
            document.getElementById('taskName').value        = '';
            document.getElementById('taskDeadline').value    = '';
            document.getElementById('taskDescription').value = '';
            document.getElementById('fileName').textContent  = 'Файл не выбран';
            document.getElementById('taskFile').value = '';
        }

        submitBtn.addEventListener('click', async () => {
            const name        = document.getElementById('taskName').value.trim();
            const deadline    = document.getElementById('taskDeadline').value;
            const description = document.getElementById('taskDescription').value.trim();
            const fileInput   = document.getElementById('taskFile');

            if (!name)     { modalError.textContent = 'Введите название задания.'; modalError.style.display = 'block'; return; }
            if (!deadline) { modalError.textContent = 'Укажите срок сдачи.';       modalError.style.display = 'block'; return; }

            const formData = new FormData();
            formData.append('course_id',   COURSE_ID);
            formData.append('name',        name);
            formData.append('deadline',    deadline);
            formData.append('description', description);
            if (fileInput.files[0]) formData.append('file', fileInput.files[0]);

            try {
                const response = await fetch('/api/task/add', { method: 'POST', body: formData });
                const data     = await response.json();
                if (!data.ok) { modalError.textContent = data.error; modalError.style.display = 'block'; return; }
                closeAddModal();
                loadTasks();
                showNotification('Задание успешно добавлено', 'success');
            } catch (err) {
                modalError.textContent   = 'Ошибка соединения с сервером.';
                modalError.style.display = 'block';
            }
        });

        const editModal     = document.getElementById('editTaskModal');
        const editCloseBtn  = document.getElementById('editCloseBtn');
        const editCancelBtn = document.getElementById('editCancelBtn');
        const editSubmitBtn = document.getElementById('editSubmitBtn');
        const editError     = document.getElementById('editModalError');

        editCloseBtn.addEventListener('click',  () => closeEditModal());
        editCancelBtn.addEventListener('click', () => closeEditModal());
        editModal.addEventListener('click', (e) => { if (e.target === editModal) closeEditModal(); });

        function closeEditModal() {
            editModal.style.display = 'none';
            editError.style.display = 'none';
            document.getElementById('editTaskFile').value = '';
            document.getElementById('editFileName').textContent = 'Файл не выбран';
        }

        window.openEditModal = async function (labId) {
            try {
                const response = await fetch(`/api/task/${labId}`);
                const lab      = await response.json();

                setMinDeadline();

                document.getElementById('editLabId').value           = lab.id;
                document.getElementById('editTaskName').value        = lab.name;
                document.getElementById('editTaskDeadline').value    = lab.end_date_raw;
                document.getElementById('editTaskDescription').value = lab.task || '';

                const fileStatus = document.getElementById('editFileName');
                if (lab.has_file) {
                    const fileName = lab.filename || 'файл';
                    fileStatus.textContent = `✔ Файл прикреплён: ${fileName} (загрузите новый чтобы заменить)`;
                    fileStatus.style.color = '#2a7a2a';
                } else {
                    fileStatus.textContent = 'Файл не выбран';
                    fileStatus.style.color = '#999';
                }

                editError.style.display = 'none';
                editModal.style.display = 'flex';
            } catch (err) {
                alert('Не удалось загрузить данные задания.');
            }
        };

        editSubmitBtn.addEventListener('click', async () => {
            const labId       = document.getElementById('editLabId').value;
            const name        = document.getElementById('editTaskName').value.trim();
            const deadline    = document.getElementById('editTaskDeadline').value;
            const description = document.getElementById('editTaskDescription').value.trim();
            const fileInput   = document.getElementById('editTaskFile');

            if (!name)     { editError.textContent = 'Введите название.';   editError.style.display = 'block'; return; }
            if (!deadline) { editError.textContent = 'Укажите срок сдачи.'; editError.style.display = 'block'; return; }

            const formData = new FormData();
            formData.append('lab_id',      labId);
            formData.append('name',        name);
            formData.append('deadline',    deadline);
            formData.append('description', description);
            if (fileInput.files[0]) formData.append('file', fileInput.files[0]);

            try {
                const response = await fetch('/api/task/edit', { method: 'POST', body: formData });
                const data     = await response.json();
                if (!data.ok) { editError.textContent = data.error; editError.style.display = 'block'; return; }
                closeEditModal();
                loadTasks();
                showNotification('Задание успешно обновлено', 'success');
            } catch (err) {
                editError.textContent   = 'Ошибка соединения с сервером.';
                editError.style.display = 'block';
            }
        });

        const addStudentModal    = document.getElementById('addStudentModal');
        const openAddStudentBtn  = document.getElementById('openAddStudentBtn');
        const closeAddStudentBtn = document.getElementById('closeAddStudentBtn');
        const cancelAddStudentBtn= document.getElementById('cancelAddStudentBtn');
        const submitAddStudentBtn= document.getElementById('submitAddStudentBtn');
        const studentSelect      = document.getElementById('studentSelect');
        const studentSearch      = document.getElementById('studentSearch');
        const studentModalError  = document.getElementById('studentModalError');

        let allStudents = [];

        openAddStudentBtn.addEventListener('click', async () => {
            addStudentModal.style.display = 'flex';
            studentModalError.style.display = 'none';
            studentSearch.value = '';
            studentSelect.innerHTML = '<option disabled>Загрузка...</option>';

            try {
                const res  = await fetch(`/api/course/${COURSE_ID}/students-not-enrolled`);
                allStudents = await res.json();
                renderStudentOptions(allStudents);
            } catch (err) {
                studentSelect.innerHTML = '<option disabled>Ошибка загрузки</option>';
            }
        });

        function renderStudentOptions(students) {
            studentSelect.innerHTML = '';
            if (students.length === 0) {
                studentSelect.innerHTML = '<option disabled>Все студенты уже записаны</option>';
                return;
            }
            students.forEach(s => {
                const opt = document.createElement('option');
                opt.value       = s.user_id;
                opt.textContent = s.full_name;
                studentSelect.appendChild(opt);
            });
        }

        studentSearch.addEventListener('input', () => {
            const q = studentSearch.value.toLowerCase();
            const filtered = allStudents.filter(s => s.full_name.toLowerCase().includes(q));
            renderStudentOptions(filtered);
        });

        function closeStudentModal() {
            addStudentModal.style.display   = 'none';
            studentModalError.style.display = 'none';
            studentSearch.value = '';
        }

        closeAddStudentBtn.addEventListener('click',  () => closeStudentModal());
        cancelAddStudentBtn.addEventListener('click', () => closeStudentModal());
        addStudentModal.addEventListener('click', (e) => { if (e.target === addStudentModal) closeStudentModal(); });

        submitAddStudentBtn.addEventListener('click', async () => {
            const selected = studentSelect.value;
            if (!selected) {
                studentModalError.textContent   = 'Выберите студента из списка.';
                studentModalError.style.display = 'block';
                return;
            }

            try {
                const res  = await fetch(`/api/course/${COURSE_ID}/add-student`, {
                    method:  'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body:    JSON.stringify({ user_id: parseInt(selected) })
                });
                const data = await res.json();

                if (!data.ok) {
                    studentModalError.textContent   = data.error;
                    studentModalError.style.display = 'block';
                    return;
                }

                closeStudentModal();
                const name = studentSelect.options[studentSelect.selectedIndex].textContent;
                showNotification(`${name} добавлен на курс`, 'success');

            } catch (err) {
                studentModalError.textContent   = 'Ошибка соединения с сервером.';
                studentModalError.style.display = 'block';
            }
        });

        function showNotification(message, type = 'info') {
            const n = document.createElement('div');
            n.className   = `notification ${type}`;
            n.textContent = message;
            document.body.appendChild(n);
            setTimeout(() => {
                n.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => n.remove(), 300);
            }, 3000);
        }
    }

    loadTasks();

})();