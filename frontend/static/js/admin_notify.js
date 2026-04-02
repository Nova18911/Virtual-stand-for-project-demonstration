function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';
    
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 3000);
}

async function loadPendingUsers() {
    try {
        const response = await fetch('/admin-notify/users/pending');
        const data = await response.json();
        
        if (data.success && data.users.length > 0) {
            displayUsers(data.users);
        } else {
            document.getElementById('pending-users').innerHTML = 
                '<div class="empty">Нет пользователей на одобрение</div>';
        }
    } catch (error) {
        document.getElementById('pending-users').innerHTML = 
            '<div class="empty">Ошибка загрузки</div>';
    }
}

function displayUsers(users) {
    const container = document.getElementById('pending-users');
    let html = '';
    
    users.forEach(user => {
        html += `
            <div class="user-card">
                <div class="user-info">
                    <p><strong>ID:</strong> ${user.user_id}</p>
                    <p><strong>Имя:</strong> ${escapeHtml(user.full_name)}</p>
                    <p><strong>Email:</strong> ${escapeHtml(user.email)}</p>
                    <p><strong>Дата:</strong> ${user.created_at || '—'}</p>
                </div>
                <div class="user-actions">
                    <button class="btn btn-approve" onclick="approveUser(${user.user_id})">✓ Одобрить</button>
                    <button class="btn btn-reject" onclick="rejectUser(${user.user_id})">✗ Отклонить</button>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

async function approveUser(userId) {
    if (!confirm('Одобрить пользователя?')) return;
    
    try {
        const response = await fetch(`/admin-notify/approve/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadPendingUsers();
        } else {
            showMessage(data.error, 'error');
        }
    } catch (error) {
        showMessage('Ошибка', 'error');
    }
}

async function rejectUser(userId) {
    if (!confirm('Отклонить пользователя?')) return;
    
    try {
        const response = await fetch(`/admin-notify/reject/${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(data.message, 'success');
            loadPendingUsers();
        } else {
            showMessage(data.error, 'error');
        }
    } catch (error) {
        showMessage('Ошибка', 'error');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', loadPendingUsers);