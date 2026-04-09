document.addEventListener('DOMContentLoaded', () => {
    const form          = document.querySelector('form');
    const emailInput    = document.getElementById('email');
    const passwordInput = document.getElementById('password');

    function isValidEmail(email) {
        return /^[\w.\-]+@[\w.\-]+\.\w{2,}$/.test(email.trim());
    }

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
            box.className = 'flash error';
            form.prepend(box);
        }
        box.textContent = message;
        box.style.display = 'block';
    }

    // Валидация при потере фокуса
    emailInput.addEventListener('blur', () => {
        if (!isValidEmail(emailInput.value)) {
            showError(emailInput, 'Введите корректный email');
        } else {
            clearError(emailInput);
        }
    });

    passwordInput.addEventListener('blur', () => {
        if (!passwordInput.value.trim()) {
            showError(passwordInput, 'Введите пароль');
        } else {
            clearError(passwordInput);
        }
    });

    // Обработка отправки формы
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        let valid = true;

        if (!isValidEmail(emailInput.value)) {
            showError(emailInput, 'Введите корректный email');
            valid = false;
        }

        if (!passwordInput.value.trim()) {
            showError(passwordInput, 'Введите пароль');
            valid = false;
        }

        if (!valid) return;

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email:    emailInput.value.trim(),
                    password: passwordInput.value
                })
            });

            const data = await response.json();

            if (!data.ok) {
                showGlobalError(data.error);
                return;
            }

            // Перенаправление при успехе
            window.location.href = data.redirect;

        } catch (err) {
            showGlobalError('Ошибка соединения с сервером.');
        }
    });
});