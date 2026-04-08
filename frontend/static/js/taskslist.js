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

            const fileBtn = lab.has_file
                ? `<a href="/api/task/${lab.id}/file" class="btn" download>📎 Файл</a>`
                : '';

            if (ROLE === 'teacher') {
                // Название ведёт на список студентов
                li.innerHTML = `
                    <a href="/task/${lab.id}" class="task-name">${lab.name}</a>
                    <div class="task-actions">
                        <span class="task-dates">${lab.start_date} — ${lab.end_date}</span>
                        ${fileBtn}
                        <button class="btn btn-edit"
                                onclick="openEditModal(${lab.id})">Редактировать</button>
                    </div>
                `;
            } else {
                // Название ведёт на страницу задания
                li.innerHTML = `
                    <a href="/tasks/${lab.id}" class="task-name">${lab.name}</a>
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

    if (ROLE === 'teacher') {

        // --- Модальное окно добавления ---
        const addModal   = document.getElementById('addTaskModal');
        const openBtn    = document.getElementById('openModalBtn');
        const closeBtn   = document.getElementById('closeModalBtn');
        const cancelBtn  = document.getElementById('cancelModalBtn');
        const submitBtn  = document.getElementById('submitTaskBtn');
        const modalError = document.getElementById('modalError');

        openBtn.addEventListener('click',  () => addModal.style.display = 'flex');
        closeBtn.addEventListener('click', () => closeAddModal());
        cancelBtn.addEventListener('click',() => closeAddModal());
        addModal.addEventListener('click', (e) => { if (e.target === addModal) closeAddModal(); });

        function closeAddModal() {
            addModal.style.display   = 'none';
            modalError.style.display = 'none';
            document.getElementById('taskName').value        = '';
            document.getElementById('taskDeadline').value    = '';
            document.getElementById('taskDescription').value = '';
            document.getElementById('fileName').textContent  = 'Файл не выбран';
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
            } catch (err) {
                modalError.textContent   = 'Ошибка соединения с сервером.';
                modalError.style.display = 'block';
            }
        });

        // --- Модальное окно редактирования ---
        const editModal    = document.getElementById('editTaskModal');
        const editCloseBtn = document.getElementById('editCloseBtn');
        const editCancelBtn= document.getElementById('editCancelBtn');
        const editSubmitBtn= document.getElementById('editSubmitBtn');
        const editError    = document.getElementById('editModalError');

        editCloseBtn.addEventListener('click',  () => closeEditModal());
        editCancelBtn.addEventListener('click', () => closeEditModal());
        editModal.addEventListener('click', (e) => { if (e.target === editModal) closeEditModal(); });

        function closeEditModal() {
            editModal.style.display = 'none';
            editError.style.display = 'none';
        }

        window.openEditModal = async function (labId) {
            try {
                const response = await fetch(`/api/task/${labId}`);
                const lab      = await response.json();

                document.getElementById('editLabId').value           = lab.id;
                document.getElementById('editTaskName').value        = lab.name;
                document.getElementById('editTaskDeadline').value    = lab.end_date_raw;
                document.getElementById('editTaskDescription').value = lab.task || '';

                // Показываем есть ли уже прикреплённый файл
                const fileStatus = document.getElementById('editFileName');
                if (lab.has_file) {
                    fileStatus.textContent  = '✔ Файл прикреплён (загрузите новый чтобы заменить)';
                    fileStatus.style.color  = '#2a7a2a';
                } else {
                    fileStatus.textContent  = 'Файл не выбран';
                    fileStatus.style.color  = '#999';
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

            if (!name)     { editError.textContent = 'Введите название.';    editError.style.display = 'block'; return; }
            if (!deadline) { editError.textContent = 'Укажите срок сдачи.';  editError.style.display = 'block'; return; }

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
            } catch (err) {
                editError.textContent   = 'Ошибка соединения с сервером.';
                editError.style.display = 'block';
            }
        });
    }

    loadTasks();

})();