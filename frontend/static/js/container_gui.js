document.getElementById('stopBtn').addEventListener('click', async () => {
    if (!confirm('Остановить контейнер?')) return;

    try {
        await fetch(`/container/${PROJECT_ID}/stop`, { method: 'POST' });
        window.close();
    } catch (err) {
        alert('Ошибка при остановке контейнера.');
    }
});