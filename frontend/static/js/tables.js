//тестовые данные пока без бека
const tables = [
    { id: 1, name: 'users' },
    { id: 2, name: 'products' },
    { id: 3, name: 'orders' },
    { id: 4, name: 'categories' },
    { id: 5, name: 'customers' },
    { id: 6, name: 'suppliers' },
    { id: 7, name: 'inventory' },
    { id: 8, name: 'payments' }
];

function renderTablesList() {
    const container = document.getElementById('tables');
    let html = '<table border="1" cellpadding="8" cellspacing="0">';
    html += '<br><label><input type="checkbox" id="selectAll"> Выбрать все</label>';
    html += '<thead><tr><th>Выбор</th><th>Название таблицы</th></tr></thead><tbody>';
    tables.forEach(table => {
        html += `
            <tr>
                <td><input type="checkbox" class="tableCheckbox" data-name="${table.name}"></td>
                <td>${table.name}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    container.innerHTML = html;

    document.getElementById('selectAll').addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('.tableCheckbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
    });
}

function clearSelection() {
    const checkboxes = document.querySelectorAll('.tableCheckbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    document.getElementById('selectAll').checked = false;
    document.getElementById('result').innerHTML = '';
}

function showSelected() {
    const selectedCheckboxes = document.querySelectorAll('.tableCheckbox:checked');
    const resultDiv = document.getElementById('result');

    if (selectedCheckboxes.length > 0) {
        let selectedTables = [];

        selectedCheckboxes.forEach(checkbox => {
            selectedTables.push({
                id: checkbox.value,
                name: checkbox.dataset.name
            });
        });

        resultDiv.innerHTML = html;
    } else {
        resultDiv.innerHTML = '<p>Таблицы не выбраны</p>';
    }
}

document.addEventListener('DOMContentLoaded', renderTablesList);