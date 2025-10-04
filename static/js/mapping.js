const column_reset = document.querySelector('.btn.reset');
if (column_reset) {
    column_reset.addEventListener('click', () => {
        const isConfirmed = confirm("⚠️ 경고 : 원본 컬럼의 매핑 정보가 모두 지워집니다. \n초기화 하시겠습니까?");
        if (isConfirmed) {
            document.querySelectorAll('.mapping-grid .input').forEach(input => input.value = '');
            console.log('Reset has been completed.');
        }
    });
}

const column_edit = document.querySelector('.button-mapping-group .btn.edit');
const add_btn_container = document.querySelector('.add-btn-container');
let isEditMode = false;

if (column_edit) {
    column_edit.addEventListener('click', () => {
        isEditMode = !isEditMode;
        column_edit.textContent = isEditMode ? 'Done' : 'Edit';
        column_edit.classList.toggle('active', isEditMode);

        if (add_btn_container) {
            const addBtn = add_btn_container.querySelector('.btn.add-row-btn');
            addBtn.classList.toggle('editing', isEditMode);
            add_btn_container.style.visibility = isEditMode ? 'visible' : 'hidden';
            add_btn_container.style.opacity = isEditMode ? '1' : '0';
        }

        document.querySelectorAll('.mapping-grid').forEach(grid => {
            const delete_btn_container = grid.querySelector('.delete-btn-container');
            if (delete_btn_container) {
                delete_btn_container.style.visibility = isEditMode ? 'visible' : 'hidden';
                delete_btn_container.style.opacity = isEditMode ? '1' : '0';
            }
        });
    });
}

let mappingData = []; // 전역 저장용

document.addEventListener('DOMContentLoaded', () => {
    const add_column = document.querySelector('#btn-add-row');
    const saveBtn = document.querySelector('#column_setting');
    const maxRows = 9;

    // 행 추가
    if (add_column) {
        add_column.addEventListener('click', () => {
            const cardGrid = add_column.closest('.card').querySelector('.grid');
            const currentRows = cardGrid.querySelectorAll('.mapping-grid').length;

            if (currentRows >= maxRows) {
                alert(`⚠️ 제한 : 최대 ${maxRows}개 행까지만 추가할 수 있습니다.`);
                return;
            }

            const newRow = document.createElement('div');
            newRow.className = 'mapping-grid';
            newRow.style.cssText = 'display: flex; align-items: center; gap: 10px;';
            newRow.innerHTML = `
                <div class="delete-btn-container">
                    <button class="btn delete-row-btn">&minus;</button>
                </div>
                <input class="input" value="원본 컬럼을 입력하세요." />
                <span style="text-align:center; color:var(--muted)">→</span>
                <select class="select"><option value="">선택</option><option value="custom">사용자 지정</option></select>
                <div class="toggle-switch">
                    <input type="checkbox" class="toggle-input" id="toggle-new-${currentRows+1}" checked />
                    <label class="toggle-label" for="toggle-new-${currentRows+1}"></label>
                </div>
            `;

            // 삭제 버튼 이벤트
            newRow.querySelector('.delete-row-btn').addEventListener('click', e => {
                e.target.closest('.mapping-grid').remove();
            });

            // toggle 이벤트
            const toggleEl = newRow.querySelector('.toggle-input');
            toggleEl.addEventListener('change', () => set_row_state(newRow, toggleEl.checked));
            set_row_state(newRow, toggleEl.checked);

            // select 사용자 지정
            const select = newRow.querySelector('.select');
            select.addEventListener('change', () => {
                if (select.value === 'custom') {
                    const userValue = prompt('[사용자 지정] 매핑 컬럼을 입력하세요.');
                    if (userValue && userValue.trim() !== '') {
                        const existingOption = Array.from(select.options).find(o => o.value === userValue.trim());
                        if (!existingOption) {
                            const newOption = document.createElement('option');
                            newOption.value = userValue.trim();
                            newOption.text = userValue.trim();
                            newOption.selected = true;
                            select.add(newOption);
                        } else {
                            existingOption.selected = true;
                        }
                        select.value = userValue.trim();
                    } else {
                        select.value = '';
                    }
                }
            });

            cardGrid.appendChild(newRow);
        });
    }

    // 서버에서 마지막 매핑 가져오기 → 자동 적용
    fetch('/api/mapping/last')
        .then(res => res.json())
        .then(data => {
            if (!data.mappings) return;
            apply_mappings(data.mappings);
        });

    // 컬럼 저장 버튼 클릭 → 서버 전송
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            const mappings = collect_mappings();
            if (!mappings.length) {
                showPopup('❌ 저장할 매핑 데이터가 없습니다.', 'error');
                return;
            }
            mappingData = mappings;

            try {
                const res = await fetch('/api/mapping/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mappings: mappingData })
                });
                const data = await res.json();
                console.log("서버 응답:", data);

                if (data.status === 'success') {
                    showPopup('✅ 컬럼이 저장되었습니다.\n저장된 컬럼은 다음 업로드 시 자동 적용됩니다.', 'success');
                } else {
                    showPopup(`❌ 컬럼 저장 실패: ${data.msg}`, 'error');
                }
            } catch (err) {
                console.error(err);
                showPopup('❌ 서버 요청 에러가 발생했습니다.', 'error');
            }
        });
    }
});

// 기존 함수 그대로
function collect_mappings() {
    return Array.from(document.querySelectorAll('.mapping-grid')).map(row => {
        const toggle = row.querySelector('.toggle-input').checked;
        if (!toggle) return null;
        return {
            original_column: row.querySelector('.input').value,
            mapping_code_id: parseInt(row.querySelector('.select').value) || null,
            file_id: 1,
            is_activate: toggle,
            created_at: new Date().toISOString()
        };
    }).filter(item => item !== null);
}

function apply_mappings(mappings) {
    const gridRows = document.querySelectorAll('.mapping-grid');
    mappings.forEach((map, index) => {
        let row = gridRows[index] || add_new_row();
        const inputEl = row.querySelector('.input');
        const selectEl = row.querySelector('.select');
        const toggleEl = row.querySelector('.toggle-input');

        inputEl.value = map.original_column;
        selectEl.value = map.mapping_code_id || '';
        toggleEl.checked = map.is_activate !== false;
        set_row_state(row, toggleEl.checked);
    });
}

function set_row_state(row, isActive) {
    const inputEl = row.querySelector('.input');
    const selectEl = row.querySelector('.select');
    row.classList.toggle('enabled', isActive);
    row.classList.toggle('disabled', !isActive);
    inputEl.disabled = !isActive;
    selectEl.disabled = !isActive;
    if (!isActive) {
        inputEl.dataset.originalValue = inputEl.value;
        selectEl.dataset.originalValue = selectEl.value;
    } else {
        if (inputEl.dataset.originalValue !== undefined) inputEl.value = inputEl.dataset.originalValue;
        if (selectEl.dataset.originalValue !== undefined) selectEl.value = selectEl.dataset.originalValue;
    }
}

function add_new_row() {
    const addBtn = document.querySelector('#btn-add-row');
    if (addBtn) addBtn.click();
    const rows = document.querySelectorAll('.mapping-grid');
    return rows[rows.length - 1];
}

function showPopup(message, type = 'success') {
    const popup = document.createElement('div');
    popup.className = type === 'success' ? 'popup-success' : 'popup-error';
    popup.textContent = message;
    document.body.appendChild(popup);
    setTimeout(() => popup.remove(), 3000);
}