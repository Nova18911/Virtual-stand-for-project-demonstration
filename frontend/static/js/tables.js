let tables = [];

async function loadCoursesFromServer() {
    const response = await fetch('/api/tables');
    tables = await response.json();
    renderTablesList();
}

function renderTablesList() {
    const container = document.getElementById('tables');
    if (!container) return;

    let html = '<table border="1" cellpadding="8" cellspacing="0">';
    html += '<br><label><input type="checkbox" id="selectAll"> Выбрать все</label>';
    html += '<thead><tr><th>Выбор</th><th>Название таблицы</th></tr></thead><tbody>';

    tables.forEach(table => {
        html += `
            <tr>
                <td><input type="checkbox" class="tableCheckbox" data-id="${table.id}" data-name="${table.name}"></td>
                <td>${table.name}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;

    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.tableCheckbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }

    const fullBackupCheckbox = document.getElementById('fullBackupCheckbox');
    const customExportCheckbox = document.getElementById('customExportCheckbox');

    if (fullBackupCheckbox) {
        fullBackupCheckbox.addEventListener('change', function() {
            if (this.checked) {
                if (customExportCheckbox) {
                    customExportCheckbox.checked = false;
                    customExportCheckbox.disabled = true;
                }

                const checkboxes = document.querySelectorAll('.tableCheckbox');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = true;
                });

                if (selectAll) {
                    selectAll.checked = true;
                    selectAll.disabled = true;
                }
            } else {
                if (customExportCheckbox) customExportCheckbox.disabled = false;
                if (selectAll) selectAll.disabled = false;
            }
        });
    }

    if (customExportCheckbox) {
        customExportCheckbox.addEventListener('change', function() {
            if (this.checked) {
                if (fullBackupCheckbox) {
                    fullBackupCheckbox.checked = false;
                    fullBackupCheckbox.disabled = true;
                }
                if (selectAll) selectAll.disabled = false;
            } else {
                if (fullBackupCheckbox) fullBackupCheckbox.disabled = false;
            }
        });
    }
}

async function performBackup() {
    const fullBackupCheckbox = document.getElementById('fullBackupCheckbox');
    const fileFormat = document.getElementById('fileFormat')?.value || 'PostgreSQL';
    const zipCheckbox = document.getElementById('zipCheckbox');
    const fileName = document.getElementById('fileName')?.value || 'backup';

    const isFullBackup = fullBackupCheckbox ? fullBackupCheckbox.checked : false;

    let selectedTables = [];

    if (isFullBackup) {
        selectedTables = tables.map(table => table.name);
    } else {
        const checkboxes = document.querySelectorAll('.tableCheckbox:checked');
        selectedTables = Array.from(checkboxes).map(cb => cb.dataset.name);
    }

    if (selectedTables.length === 0) {
        alert('Выберите хотя бы одну таблицу для экспорта');
        return;
    }

    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = '<p>Создание бекапа...</p>';

    const backupData = {
        type: isFullBackup ? 'full' : 'partial',
        tables: selectedTables,
        format: fileFormat,
        zip: zipCheckbox ? zipCheckbox.checked : false,
        filename: fileName
    };

    const response = await fetch('/api/backup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(backupData)
    });

    const blob = await response.blob();

    const contentDisposition = response.headers.get('Content-Disposition');
    let downloadName = '';
    if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (match && match[1]) {
            downloadName = match[1].replace(/['"]/g, '');
        }
    }

    if (!downloadName) {
        const extension = fileFormat === 'MySQL' ? '.sql' : '.json';
        downloadName = zipCheckbox?.checked ? `${fileName}.zip` : `${fileName}${extension}`;
    }

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = downloadName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    const fileSize = (blob.size / 1024).toFixed(2);
    resultDiv.innerHTML = `<p>Бекап создан</p><p>Размер: ${fileSize} KB</p><p>Таблиц: ${selectedTables.length}</p>`;
}

function clearSelection() {
    const checkboxes = document.querySelectorAll('.tableCheckbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.checked = false;
    }
    document.getElementById('result').innerHTML = '';
}

function showSelected() {
    const selectedCheckboxes = document.querySelectorAll('.tableCheckbox:checked');
    const resultDiv = document.getElementById('result');

    if (selectedCheckboxes.length > 0) {
        let selectedTables = [];
        selectedCheckboxes.forEach(checkbox => {
            selectedTables.push(checkbox.dataset.name);
        });

        let html = '<p>Выбранные таблицы:</p><ul>';
        selectedTables.forEach(name => {
            html += `<li>${name}</li>`;
        });
        html += '</ul>';
        html += `<p>Всего: ${selectedTables.length}</p>`;
        resultDiv.innerHTML = html;
    } else {
        resultDiv.innerHTML = '<p>Таблицы не выбраны</p>';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadCoursesFromServer();

    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function(e) {
            e.preventDefault();
            performBackup();
        });
    }
});