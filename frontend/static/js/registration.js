document.addEventListener('DOMContentLoaded', () => {
    const form          = document.querySelector('form');
    const emailInput    = document.getElementById('email');
    const fioInput      = document.getElementById('fio');
    const passwordInput = document.getElementById('password');
    const roleSelect    = document.getElementById('role');

    // --- Валидаторы ---
    function isValidEmail(email) {
        return /^[\w.\-]+@[\w.\-]+\.\w{2,}$/.test(email.trim());
    }

    function isValidFio(fio) {
        const parts = fio.trim().split(/\s+/);
        return parts.length >= 2 && parts.every(p => /^[А-ЯЁа-яё\-]+$/.test(p));
    }

    function isValidPassword(password) {
        return password.length >= 4;
    }

    // --- Показ/скрытие ошибок ---
    function showError(input, message) {
        clearError(input);
        input.classList.add('input-error');
        const err = document.createElement('span');
        err.className = 'field-error';
        err.textContent = message;
        input.parentNode.appendChild(err);
    }

    function clearError(input) {
        input.classList.remove('input-error');
        const prev = input.parentNode.querySelector('.field-error');
        if (prev) prev.remove();
    }

    function showGlobalError(message) {
        let box = document.getElementById('global-error');
        if (!box) {
            box = document.createElement('div');
            box.id = 'global-error';
            box.className = 'flash danger';
            form.prepend(box);
        }
        box.textContent = message;
        box.style.display = 'block';
    }

    function showGlobalSuccess(message) {
        let box = document.getElementById('global-error');
        if (!box) {
            box = document.createElement('div');
            box.id = 'global-error';
            form.prepend(box);
        }
        box.className = 'flash success';
        box.textContent = message;
        box.style.display = 'block';
    }

    // --- Валидация при потере фокуса ---
    emailInput.addEventListener('blur', () => {
        if (!isValidEmail(emailInput.value)) {
            showError(emailInput, 'Введите корректный email (example@mail.ru)');
        } else {
            clearError(emailInput);
        }
    });

    fioInput.addEventListener('blur', () => {
        if (!isValidFio(fioInput.value)) {
            showError(fioInput, 'Минимум два слова, только кириллица');
        } else {
            clearError(fioInput);
        }
    });

    passwordInput.addEventListener('blur', () => {
        if (!isValidPassword(passwordInput.value)) {
            showError(passwordInput, 'Пароль должен содержать минимум 4 символа');
        } else {
            clearError(passwordInput);
        }
    });

    // --- Отправка формы ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        let valid = true;

        if (!isValidEmail(emailInput.value)) {
            showError(emailInput, 'Введите корректный email (example@mail.ru)');
            valid = false;
        }
        if (!isValidFio(fioInput.value)) {
            showError(fioInput, 'Минимум два слова, только кириллица');
            valid = false;
        }
        if (!isValidPassword(passwordInput.value)) {
            showError(passwordInput, 'Пароль должен содержать минимум 4 символа');
            valid = false;
        }

        if (!valid) return;

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email:    emailInput.value.trim(),
                    fio:      fioInput.value.trim(),
                    password: passwordInput.value,
                    role:     roleSelect.value
                })
            });

            const data = await response.json();

            if (!data.ok) {
                showGlobalError(data.error);
                return;
            }

            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                // Преподаватель — показываем сообщение, скрываем форму
                form.style.display = 'none';
                showGlobalSuccess(data.message);
            }

        } catch (err) {
            showGlobalError('Ошибка соединения с сервером.');
        }
    });
});