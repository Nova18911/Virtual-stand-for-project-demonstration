const API_BASE = 'http://127.0.0.1:5000';

document.addEventListener('DOMContentLoaded', () => {
    refreshData();
    setupNavigation();
    setupSettingsForm();
    loadSettings();
    
    setInterval(refreshData, 30000);
});

function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = link.dataset.tab;
            
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            if (tab === 'containers') {
                document.getElementById('containersTab').classList.add('active');
                loadContainers();
            } else if (tab === 'images') {
                document.getElementById('imagesTab').classList.add('active');
                loadImages();
            } else if (tab === 'settings') {
                document.getElementById('settingsTab').classList.add('active');
                loadSettings();
            } else if (tab === 'logs') {
                document.getElementById('logsTab').classList.add('active');
                loadLogs();
            }
        });
    });
}

function setupSettingsForm() {
    document.getElementById('settingsForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const settings = {
            lifetime_hours: parseInt(document.getElementById('lifetimeHours').value),
            cleanup_images: document.getElementById('cleanupImages').value === '1',
            check_interval: parseInt(document.getElementById('checkInterval').value),
            image_age_days: parseInt(document.getElementById('imageAgeDays').value)
        };
        
        try {
            const response = await fetch(`${API_BASE}/api/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });
            
            const result = await response.json();
            
            if (result.success) {
                showNotification('Успех', 'Настройки сохранены', 'success');
            } else {
                showNotification('Ошибка', result.error, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Ошибка', 'Не удалось сохранить настройки', 'error');
        }
    });
}

async function loadContainers() {
    try {
        const response = await fetch(`${API_BASE}/api/containers`);
        const data = await response.json();
        
        if (data.success) {
            displayContainers(data.containers);
            document.getElementById('runningCount').textContent = 
                data.containers.filter(c => c.status === 'running').length;
        } else {
            showNotification('Ошибка', data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        const container = document.getElementById('containersList');
        container.innerHTML = '<div class="empty-state"> Ошибка загрузки контейнеров</div>';
    }
}

// Display containers
function displayContainers(containers) {
    const container = document.getElementById('containersList');
    
    if (containers.length === 0) {
        container.innerHTML = '<div class="empty-state"> Нет контейнеров</div>';
        return;
    }
    
    let html = `
        <table>
            <thead>
                <tr>
                    <th>Container ID</th>
                    <th>Project ID</th>
                    <th>Порт</th>
                    <th>Образ</th>
                    <th>Запущен</th>
                    <th>Статус</th>
                    <th>Действия</th>
                </thead>
                <tbody>
    `;
    
    containers.forEach(container => {
        const date = new Date(container.started_at).toLocaleString('ru-RU');
        html += `
            <tr>
                <td><code>${container.container_id.substring(0, 12)}</code></td>
                <td>${container.project_id}</td>
                <td>${container.port}</td>
                <td><strong>${escapeHtml(container.image_name)}</strong></td>
                <td>${date}</td>
                <td><span class="status-${container.status}">${getStatusText(container.status)}</span></td>
                <td class="action-buttons">
                    <button class="action-btn btn-view" onclick="viewContainerDetails('${container.container_id}')">👁️ Детали</button>
                    ${container.status === 'running' ? 
                        `<button class="action-btn btn-delete" onclick="deleteContainer('${container.container_id}')">🗑 Удалить</button>` : ''}
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function loadImages() {
    try {
        const response = await fetch(`${API_BASE}/api/images`);
        const data = await response.json();
        
        if (data.success) {
            displayImages(data.images);
            document.getElementById('imagesCount').textContent = data.images.length;
        } else {
            showNotification('Ошибка', data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        const container = document.getElementById('imagesList');
        container.innerHTML = '<div class="empty-state"> Ошибка загрузки образов</div>';
    }
}

function displayImages(images) {
    const container = document.getElementById('imagesList');
    
    if (images.length === 0) {
        container.innerHTML = '<div class="empty-state">Нет образов</div>';
        return;
    }
    
    let html = `
        <table>
            <thead>
                <tr>
                    <th>Repository</th>
                    <th>Tag</th>
                    <th>Image ID</th>
                    <th>Размер</th>
                    <th>Создан</th>
                    <th>Используется</th>
                    <th>Действия</th>
                </thead>
                <tbody>
    `;
    
    images.forEach(image => {
        const size = formatBytes(image.size);
        const created = new Date(image.created).toLocaleString('ru-RU');
        html += `
            <tr>
                <td><strong>${escapeHtml(image.repository)}</strong></td>
                <td>${escapeHtml(image.tag)}</td>
                <td><code>${image.id.substring(0, 12)}</code></td>
                <td class="image-size">${size}</td>
                <td class="created-date">${created}</td>
                <td>${image.in_use ? ' Да' : ' Нет'}</td>
                <td>
                    ${!image.in_use ? 
                        `<button class="action-btn btn-delete" onclick="deleteImage('${image.id}')">🗑 Удалить</button>` : 
                        '<span style="color:#95a5a6;">Используется</span>'}
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function loadLogs() {
    const lines = document.getElementById('logLines').value;
    
    try {
        const response = await fetch(`${API_BASE}/api/logs?lines=${lines}`);
        const data = await response.json();
        
        if (data.success) {
            const logContainer = document.getElementById('logContainer');
            if (data.logs.length === 0) {
                logContainer.innerHTML = '<div class="empty-state">Логи отсутствуют</div>';
            } else {
                logContainer.innerHTML = data.logs.map(log => 
                    `<div class="log-entry">${escapeHtml(log)}</div>`
                ).join('');
                
                // Auto-scroll to bottom
                logContainer.scrollTop = logContainer.scrollHeight;
            }
        } else {
            showNotification('Ошибка', data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        const container = document.getElementById('logContainer');
        container.innerHTML = '<div class="empty-state"> Ошибка загрузки логов</div>';
    }
}

async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/api/settings`);
        const data = await response.json();
        
        if (data.success && data.settings) {
            document.getElementById('lifetimeHours').value = data.settings.container_lifetime_hours || 24;
            document.getElementById('cleanupImages').value = data.settings.image_cleanup_enabled ? '1' : '0';
            document.getElementById('checkInterval').value = data.settings.check_interval_minutes || 5;
            document.getElementById('imageAgeDays').value = data.settings.image_age_days || 7;
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/stats`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('totalContainers').textContent = data.stats.total || 0;
            document.getElementById('runningContainers').textContent = data.stats.running || 0;
            document.getElementById('removedContainers').textContent = data.stats.removed || 0;
            
            const dockerStatus = document.getElementById('dockerStatus');
            if (data.stats.docker_available) {
                dockerStatus.innerHTML = '✓ Доступен';
                dockerStatus.style.color = '#27ae60';
            } else {
                dockerStatus.innerHTML = '✗ Недоступен';
                dockerStatus.style.color = '#e74c3c';
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function runContainer() {
    const data = {
        project_id: parseInt(document.getElementById('projectId').value),
        image_name: document.getElementById('imageName').value,
        port: parseInt(document.getElementById('port').value),
        container_name: document.getElementById('containerName').value
    };
    
    if (!data.project_id || !data.image_name || !data.port) {
        showNotification('Ошибка', 'Заполните все обязательные поля', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/containers/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Успех', `Контейнер запущен: ${result.container_id.substring(0, 12)}`, 'success');
            closeModal('runContainerModal');
            refreshData();
            resetRunContainerForm();
        } else {
            showNotification('Ошибка', result.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка', 'Не удалось запустить контейнер', 'error');
    }
}

async function deleteContainer(containerId) {
    if (!confirm('Удалить этот контейнер?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/containers/${containerId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Успех', 'Контейнер удален', 'success');
            refreshData();
        } else {
            showNotification('Ошибка', result.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка', 'Не удалось удалить контейнер', 'error');
    }
}

async function deleteImage(imageId) {
    if (!confirm('Удалить этот образ?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/images/${imageId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Успех', 'Образ удален', 'success');
            loadImages();
        } else {
            showNotification('Ошибка', result.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка', 'Не удалось удалить образ', 'error');
    }
}

async function viewContainerDetails(containerId) {
    try {
        const response = await fetch(`${API_BASE}/api/containers/${containerId}`);
        const result = await response.json();
        
        if (result.success) {
            const container = result.container;
            const modalBody = document.getElementById('containerModalBody');
            const startDate = new Date(container.started_at).toLocaleString('ru-RU');
            
            modalBody.innerHTML = `
                <div class="info-row">
                    <div class="info-label">Container ID:</div>
                    <div class="info-value"><code>${container.container_id}</code></div>
                </div>
                <div class="info-row">
                    <div class="info-label">Project ID:</div>
                    <div class="info-value">${container.project_id}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Порт:</div>
                    <div class="info-value">${container.port}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Образ:</div>
                    <div class="info-value"><strong>${escapeHtml(container.image_name)}</strong></div>
                </div>
                <div class="info-row">
                    <div class="info-label">Запущен:</div>
                    <div class="info-value">${startDate}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">Статус:</div>
                    <div class="info-value"><span class="status-${container.status}">${getStatusText(container.status)}</span></div>
                </div>
            `;
            
            const deleteBtn = document.getElementById('deleteFromModalBtn');
            deleteBtn.onclick = () => deleteContainer(containerId);
            deleteBtn.style.display = container.status === 'running' ? 'block' : 'none';
            
            document.getElementById('containerModal').style.display = 'flex';
        } else {
            showNotification('Ошибка', result.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка', 'Не удалось загрузить детали', 'error');
    }
}

async function runCleanup() {
    if (!confirm('Запустить принудительную очистку? Это удалит все просроченные контейнеры и неиспользуемые образы.')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/cleanup/run`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Успех', 'Очистка запущена', 'success');
            setTimeout(refreshData, 3000);
        } else {
            showNotification('Ошибка', result.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка', 'Не удалось запустить очистку', 'error');
    }
}

async function cleanupImages() {
    if (!confirm('Удалить все неиспользуемые образы старше 7 дней?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/images/cleanup`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Успех', `Удалено образов: ${result.removed}`, 'success');
            loadImages();
        } else {
            showNotification('Ошибка', result.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Ошибка', 'Не удалось очистить образы', 'error');
    }
}

function refreshData() {
    loadStats();
    loadContainers();
}

function searchContainers() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#containersList table tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

function resetSettings() {
    document.getElementById('lifetimeHours').value = 24;
    document.getElementById('cleanupImages').value = '1';
    document.getElementById('checkInterval').value = 5;
    document.getElementById('imageAgeDays').value = 7;
}

function resetRunContainerForm() {
    document.getElementById('projectId').value = '';
    document.getElementById('imageName').value = '';
    document.getElementById('port').value = '';
    document.getElementById('containerName').value = '';
}

function showRunContainerModal() {
    resetRunContainerForm();
    document.getElementById('runContainerModal').style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function showNotification(title, message, type = 'success') {
    const container = document.getElementById('notificationContainer');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-title">${type === 'success' ? '✓' : '✗'} ${title}</div>
        <div class="notification-message">${escapeHtml(message)}</div>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getStatusText(status) {
    const statuses = {
        'running': 'Активен',
        'removed': 'Удален',
        'not_found': 'Не найден',
        'exited': 'Остановлен'
    };
    return statuses[status] || status;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

window.onclick = (event) => {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
};