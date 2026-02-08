/**
 * Smart Student Distribution System
 * Integrated with Flask Backend
 */

const API_BASE_URL = 'http://localhost:5000';

// ============ State ============
const state = {
    channelPercentages: {
        markazi: 60,
        mawazi: 30,
        shuhada: 10
    },
    studentFile: null,
    departments: [] // [{name: 'Dept', capacity: 100, is_active: true}]
};

// ============ DOM Elements ============
const elements = {
    totalSeats: document.getElementById('total-seats'),
    manualSeatsCheckbox: document.getElementById('manual-seats'),
    addDepartmentBtn: document.getElementById('add-department-btn'),
    departmentRows: document.getElementById('department-rows'),
    channelMarkazi: document.getElementById('channel-markazi'),
    channelMawazi: document.getElementById('channel-mawazi'),
    channelShuhada: document.getElementById('channel-shuhada'),
    acceptanceError: document.getElementById('acceptance-error'),
    fileInput: document.getElementById('file-input'),
    fileSelect: document.getElementById('file-select'),
    chooseFileBtn: document.getElementById('choose-file-btn'),
    fileInfo: document.getElementById('file-info'),
    startDistributionBtn: document.getElementById('start-distribution-btn'),
    resultsSection: document.getElementById('results-section'),
    resultsContent: document.getElementById('results-content'),
    exportExcelBtn: document.getElementById('export-btn')
};

let rowIdCounter = 0;

// ============ API Helper Functions ============
async function fetchConfig() {
    try {
        const res = await fetch(`${API_BASE_URL}/config`);
        const result = await res.json();
        if (result.status === 'success') {
            return result.data;
        }
    } catch (e) {
        console.error('Failed to load config:', e);
    }
    return null;
}

async function saveConfig() {
    const data = collectFormData();
    // Prepare data for /config endpoint
    const configData = {
        quotas: {
            'مركزي': data.channelPercentages.markazi / 100,
            'الموازي': data.channelPercentages.mawazi / 100,
            'ذوي الشهداء': data.channelPercentages.shuhada / 100
        },
        departments: data.departments.map(d => ({
            name: d.name,
            capacity: d.seats || 0,
            is_active: true
        })),
        total_capacity: data.totalSeats,
        manual_mode: data.manualSeats
    };

    try {
        await fetch(`${API_BASE_URL}/config`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configData)
        });
    } catch (e) {
        console.error('Failed to save config:', e);
    }
}

async function uploadFileForScan(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API_BASE_URL}/scan`, {
            method: 'POST',
            body: formData
        });
        return await res.json();
    } catch (e) {
        console.error('Scan failed:', e);
        throw e;
    }
}

// ============ UI Logic ============

function updateAllDepartmentSeatsEnabled() {
    const manualSeats = elements.manualSeatsCheckbox.checked;
    elements.departmentRows.querySelectorAll('.department-row').forEach(row => {
        const seatsInput = row.querySelector('[name="departmentSeats"]');
        seatsInput.disabled = !manualSeats;
        if (!manualSeats) seatsInput.value = '';
    });
}

function addDepartmentRow(name = '', capacity = '') {
    const id = ++rowIdCounter;
    const row = document.createElement('div');
    row.className = 'department-row';
    row.dataset.rowId = id;
    const manualSeats = elements.manualSeatsCheckbox.checked;

    row.innerHTML = `
        <div class="department-row-fields">
            <div class="form-group">
                <label for="dept-name-${id}">اسم القسم</label>
                <input type="text" id="dept-name-${id}" name="departmentName" placeholder="اسم القسم" value="${name}">
            </div>
            <div class="form-group">
                <label for="dept-seats-${id}">عدد المقاعد</label>
                <input type="number" id="dept-seats-${id}" name="departmentSeats" min="0" step="1" 
                       placeholder="عدد المقاعد" value="${capacity}" ${manualSeats ? '' : 'disabled'}>
            </div>
            <button type="button" class="btn btn-remove" data-row-id="${id}">حذف</button>
        </div>
    `;

    // Saving config on change
    const inputs = row.querySelectorAll('input');
    inputs.forEach(input => input.addEventListener('change', saveConfig));

    const removeBtn = row.querySelector('.btn-remove');
    removeBtn.addEventListener('click', () => {
        row.remove();
        saveConfig();
    });

    elements.departmentRows.appendChild(row);
}

function updateChannelPercentages() {
    state.channelPercentages = {
        markazi: parseInt(elements.channelMarkazi.value, 10) || 0,
        mawazi: parseInt(elements.channelMawazi.value, 10) || 0,
        shuhada: parseInt(elements.channelShuhada.value, 10) || 0
    };
}

function initFileUpload() {
    elements.chooseFileBtn.addEventListener('click', () => elements.fileInput.click());

    elements.fileInput.addEventListener('change', async function () {
        const file = this.files[0];
        if (!file) return;

        state.studentFile = file;
        elements.fileInfo.textContent = `جاري الفحص: ${file.name}...`;
        elements.startDistributionBtn.textContent = 'بدء عملية التوزيع';
        elements.resultsSection.style.display = 'none'; // Hide results of old file

        try {
            const scanResult = await uploadFileForScan(file);
            if (scanResult.status === 'success') {
                elements.fileInfo.textContent = `${file.name} (تم الفحص: ${scanResult.student_count} طالب)`;
                elements.fileSelect.innerHTML = `<option value="${file.name}" selected>${file.name}</option>`;

                // Optional: Update departments from file if needed, 
                // but usually we want to keep User's config.
                // We could prompt user to sync departments.
            } else {
                elements.fileInfo.textContent = `خطأ: ${scanResult.message}`;
            }
        } catch (e) {
            elements.fileInfo.textContent = 'فشل الاتصال بالخادم';
        }
    });
}

function collectDepartmentsFromRows() {
    const manualSeats = elements.manualSeatsCheckbox.checked;
    const rows = elements.departmentRows.querySelectorAll('.department-row');
    return Array.from(rows).map(row => {
        const rowId = row.dataset.rowId;
        const nameInput = row.querySelector(`#dept-name-${rowId}`);
        const seatsInput = row.querySelector(`#dept-seats-${rowId}`);

        const name = nameInput.value.trim();
        const seatsVal = seatsInput.value;
        const seats = manualSeats && seatsVal !== '' && !isNaN(parseInt(seatsVal, 10))
            ? parseInt(seatsVal, 10)
            : 0;

        return { id: parseInt(rowId, 10), name: name, seats: seats };
    });
}

function collectFormData() {
    updateChannelPercentages();
    const departments = collectDepartmentsFromRows();
    const totalSeatsVal = elements.totalSeats.value;

    return {
        totalSeats: totalSeatsVal ? parseInt(totalSeatsVal, 10) : 0,
        manualSeats: elements.manualSeatsCheckbox.checked,
        departmentCount: departments.length,
        departments: departments,
        channelPercentages: state.channelPercentages,
        hasStudentFile: !!state.studentFile
    };
}

// ============ Distribution Logic ============
async function startDistribution() {
    elements.acceptanceError.textContent = '';
    const data = collectFormData();

    // Validation
    if (!data.hasStudentFile) {
        alert('يرجى رفع ملف الطلاب أولاً');
        return;
    }

    const totalPercent = data.channelPercentages.markazi +
        data.channelPercentages.mawazi +
        data.channelPercentages.shuhada;

    if (totalPercent !== 100) {
        // Note: You can relax this if you want to allow < 100%
        if (totalPercent > 100) {
            elements.acceptanceError.textContent = `المجموع ${totalPercent}% يتجاوز 100%`;
            return;
        }
    }

    elements.startDistributionBtn.disabled = true;
    elements.startDistributionBtn.textContent = 'جاري التوزيع...';
    elements.resultsSection.style.display = 'none';

    const formData = new FormData();
    formData.append('file', state.studentFile);
    formData.append('mode', data.manualSeats ? 'MANUAL' : 'EQUAL');
    formData.append('total_capacity', data.totalSeats);

    // Capacities Map
    const capMap = {};
    data.departments.forEach(d => {
        capMap[d.name] = d.seats;
    });
    formData.append('capacities', JSON.stringify(capMap));

    // Quotas Map
    const quotasMap = {
        'مركزي': data.channelPercentages.markazi / 100,
        'الموازي': data.channelPercentages.mawazi / 100,
        'ذوي الشهداء': data.channelPercentages.shuhada / 100
    };
    formData.append('quotas', JSON.stringify(quotasMap));

    // Send to Backend
    try {
        const response = await fetch(`${API_BASE_URL}/distribute`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();

            if (result.status === 'success') {
                elements.resultsSection.style.display = 'block';
                elements.startDistributionBtn.textContent = 'إعادة التوزيع';

                // 1. Show Success Message & Stats
                elements.resultsContent.innerHTML = `
                    <div class="success-message">
                        <h3>✅ تم التوزيع بنجاح!</h3>
                        <p>تم توزيع ${result.stats.assigned} طالب من أصل ${result.stats.total}</p>
                        <p>طلاب غير مقبولين: ${result.stats.unassigned}</p>
                    </div>
                `;

                // 2. Build Results Table
                const tableContainer = document.createElement('div');
                tableContainer.className = 'results-table-container';
                tableContainer.style.marginTop = '20px';
                tableContainer.style.overflowX = 'auto';

                // Sort data by Average (descending) for better visibility
                result.data.sort((a, b) => (b['المعدل'] || 0) - (a['المعدل'] || 0));

                let tableHtml = `
                    <div style="margin-bottom: 1rem; color: var(--text-muted); font-size: 0.9em;">
                        ملاحظة: النتائج مرتبة حسب المعدل. يتم إشغال المقاعد حسب النسب المحددة، وفي حال بقاء شواغر في أي قناة (مثل الموازي) يتم ملؤها تلقائياً بالأعلى معدلاً من القنوات الأخرى لضمان عدم ضياع أي مقعد.
                    </div>
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>ت</th>
                                <th>الاسم</th>
                                <th>المعدل</th>
                                <th>فئة القبول</th>
                                <th>القسم المقبول</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                result.data.forEach(student => {
                    const isUnassigned = student['القسم المقبول'] === 'غير مقبول';
                    const trStyle = isUnassigned ? 'background-color: #ffebee;' : '';

                    // Try to find the name from common column headers
                    const studentName = student['الاسم الرباعي'] || student['اسم الطالب'] || student['الاسم'] || student['Name'] || '';
                    const channel = student['قناة القبول'] || student['channel'] || '-';

                    tableHtml += `
                        <tr class="${isUnassigned ? 'unassigned-row' : ''}" style="${isUnassigned ? 'background-color: #fee2e2;' : ''}">
                            <td>${student['ت'] || ''}</td>
                            <td>${studentName}</td>
                            <td>${student['المعدل'] || ''}</td>
                            <td>${channel}</td>
                            <td style="${isUnassigned ? 'color: var(--danger-color); font-weight: bold;' : 'font-weight: bold;'}">${student['القسم المقبول']}</td>
                        </tr>
                    `;
                });

                tableHtml += `</tbody></table>`;
                tableContainer.innerHTML = tableHtml;
                elements.resultsContent.appendChild(tableContainer);

                // 3. Setup Export Button
                if (elements.exportExcelBtn) {
                    elements.exportExcelBtn.style.display = 'inline-block';
                    elements.exportExcelBtn.onclick = () => {
                        if (result.file_b64) {
                            // Decode Base64 to Blob
                            const binaryString = window.atob(result.file_b64);
                            const len = binaryString.length;
                            const bytes = new Uint8Array(len);
                            for (let i = 0; i < len; i++) {
                                bytes[i] = binaryString.charCodeAt(i);
                            }
                            const blob = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

                            // Download
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = result.file_name || 'distribution_result.xlsx';
                            document.body.appendChild(a);
                            a.click();
                            a.remove();
                            window.URL.revokeObjectURL(url);
                        } else {
                            alert('لا يوجد ملف جاهز للتصدير');
                        }
                    };
                }

            } else {
                alert(`خطأ: ${result.message}`);
            }
        } else {
            const err = await response.json();
            alert(`خطأ: ${err.message}`);
        }
    } catch (e) {
        console.error(e);
        alert('حدث خطأ أثناء الاتصال بالخادم');
        elements.startDistributionBtn.textContent = 'بدء عملية التوزيع';
    } finally {
        elements.startDistributionBtn.disabled = false;
        // Keep 'Redistribute' text on success, reset only on error (handled above)
        if (elements.startDistributionBtn.textContent === 'جاري التوزيع...') {
            elements.startDistributionBtn.textContent = 'بدء عملية التوزيع';
        }
    }
}

// ============ Initialize ============
async function init() {
    initFileUpload();

    // Load saved config
    const config = await fetchConfig();
    if (config) {
        // Apply Quotas
        if (config.quotas) {
            elements.channelMarkazi.value = (config.quotas['مركزي'] || 0.6) * 100;
            elements.channelMawazi.value = (config.quotas['الموازي'] || 0.3) * 100;
            elements.channelShuhada.value = (config.quotas['ذوي الشهداء'] || 0.1) * 100;
        }

        // Apply Departments
        if (config.departments && config.departments.length > 0) {
            elements.departmentRows.innerHTML = ''; // Clear defaults
            config.departments.forEach(d => {
                if (d.is_active !== false) {
                    addDepartmentRow(d.name, d.capacity);
                }
            });
        } else {
            // Add one empty row if nothing saved
            addDepartmentRow();
        }

        // Apply Total Capacity & Manual Mode
        if (config.total_capacity !== undefined) {
            elements.totalSeats.value = config.total_capacity;
        }
        if (config.manual_mode !== undefined) {
            elements.manualSeatsCheckbox.checked = config.manual_mode;
            updateAllDepartmentSeatsEnabled();
        }

    } else {
        addDepartmentRow();
    }

    elements.totalSeats.addEventListener('input', function () {
        const val = this.value;
        if (val && val.includes('.')) {
            this.value = Math.floor(parseFloat(val)) || '';
        }
    });

    elements.totalSeats.addEventListener('change', saveConfig);

    elements.manualSeatsCheckbox.addEventListener('change', () => {
        updateAllDepartmentSeatsEnabled();
        saveConfig(); // Auto-save preference? Maybe wait for explicit action or debounced
    });

    [elements.channelMarkazi, elements.channelMawazi, elements.channelShuhada].forEach(input => {
        input.addEventListener('change', () => {
            updateChannelPercentages();
            saveConfig();
        });
    });

    elements.addDepartmentBtn.addEventListener('click', () => {
        addDepartmentRow();
        saveConfig();
    });

    elements.startDistributionBtn.addEventListener('click', startDistribution);
    // Export button removed from logic as the backend sends the file directly
    if (elements.exportExcelBtn) elements.exportExcelBtn.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', init);
