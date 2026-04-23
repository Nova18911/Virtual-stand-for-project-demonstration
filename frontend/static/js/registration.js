document.addEventListener('DOMContentLoaded', () => {
    const form          = document.querySelector('form');
    const emailInput    = document.getElementById('email');
    const fioInput      = document.getElementById('fio');
    const passwordInput = document.getElementById('password');
    const roleSelect    = document.getElementById('role');
    const consentBox    = document.getElementById('consent');
    const consentError  = document.getElementById('consent-error');

    function isValidEmail(email) { return /^[\w.\-]+@[\w.\-]+\.\w{2,}$/.test(email.trim()); }
    function isValidFio(fio) {
        const parts = fio.trim().split(/\s+/);
        return parts.length >= 2 && parts.every(p => /^[А-ЯЁа-яё\-]+$/.test(p));
    }
    function isValidPassword(password) { return password.length >= 4; }

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

    consentBox.addEventListener('change', () => {
        consentError.style.display = consentBox.checked ? 'none' : 'block';
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        let valid = true;

        if (!isValidEmail(emailInput.value)) { showError(emailInput, 'Введите корректный email'); valid = false; }
        if (!isValidFio(fioInput.value)) { showError(fioInput, 'Минимум два слова, только кириллица'); valid = false; }
        if (!isValidPassword(passwordInput.value)) { showError(passwordInput, 'Минимум 4 символа'); valid = false; }
        if (!consentBox.checked) { consentError.style.display = 'block'; valid = false; }

        if (!valid) return;

        // Fetch API логика остается без изменений
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
            if (data.redirect) window.location.href = data.redirect;
        } catch (err) { console.error('Ошибка:', err); }
    });
});