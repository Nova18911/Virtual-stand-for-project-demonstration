let projectId;
let eventSource = null;

document.addEventListener('DOMContentLoaded', () => {
    projectId = document.getElementById('container-view').dataset.projectId;

    const output = document.getElementById('output');
    const statusBadge = document.getElementById('status-badge');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const stopBtn = document.getElementById('stop-btn');

    function addLine(text, type = 'output') {
        const line = document.createElement('div');
        line.className = `output-line ${type}`;
        line.textContent = text;
        output.appendChild(line);
        output.scrollTop = output.scrollHeight;
    }

    function connectToLogs() {
        eventSource = new EventSource(`/container/${projectId}/logs`);

        eventSource.onopen = () => {
            addLine('Подключено к программе', 'info');
            statusBadge.textContent = 'Работает';
            statusBadge.className = 'status-badge running';
        };

        eventSource.onmessage = (event) => {
            if (event.data && event.data.trim()) {
                addLine(event.data, 'output');
            }
        };

        eventSource.addEventListener('close', () => {
            addLine('Программа завершила работу', 'info');
            statusBadge.textContent = 'Завершено';
            statusBadge.className = 'status-badge stopped';
            userInput.disabled = true;
            sendBtn.disabled = true;
            if (eventSource) eventSource.close();
        });

        eventSource.onerror = () => {
            if (eventSource.readyState === EventSource.CLOSED) {
                addLine('Соединение закрыто', 'error');
                statusBadge.className = 'status-badge stopped';
            }
        };
    }

    function sendInput() {
        const value = userInput.value.trim();
        if (!value) return;

        addLine(`> ${value}`, 'input');

        fetch(`/container/${projectId}/input`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `input=${encodeURIComponent(value)}`
        }).catch(err => {
            addLine(`Ошибка отправки ввода: ${err.message}`, 'error');
        });

        userInput.value = '';
    }

    async function stopContainer() {
        if (!confirm('Остановить программу?')) return;

        try {
            const res = await fetch(`/container/${projectId}/stop`, { method: 'POST' });
            const data = await res.json();

            if (data.success) {
                addLine('Программа остановлена', 'info');
                statusBadge.textContent = 'Остановлено';
                statusBadge.className = 'status-badge stopped';
                if (eventSource) eventSource.close();
            } else {
                addLine(`${data.message || 'Ошибка остановки'}`, 'error');
            }
        } catch (e) {
            addLine(`Ошибка остановки: ${e.message}`, 'error');
        }
    }

    sendBtn.addEventListener('click', sendInput);
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendInput();
    });
    stopBtn.addEventListener('click', stopContainer);

    connectToLogs();
});