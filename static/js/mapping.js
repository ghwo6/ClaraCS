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
let mappingCodes = []; // DB에서 가져온 매핑 코드들

// 기본 8개 매핑 항목
const defaultMappings = [
    { original_column: 'created_at', code_name: '접수일' },
    { original_column: 'customer_id', code_name: '고객ID' },
    { original_column: 'channel', code_name: '채널' },
    { original_column: 'product_code', code_name: '상품코드' },
    { original_column: 'inquiry_type', code_name: '문의 유형' },
    { original_column: 'body', code_name: '본문' },
    { original_column: 'assignee', code_name: '담당자' },
    { original_column: 'status', code_name: '처리 상태' }
];

document.addEventListener('DOMContentLoaded', async () => {
    const add_column = document.querySelector('#btn-add-row');
    const maxRows = 15;
    
    // 1. 매핑 코드 로드
    await loadMappingCodes();
    
    // 2. DB에서 마지막 매핑 불러오기 (없으면 기본 8개)
    await loadLastMappingsOrDefault();

    // 행 추가
    if (add_column) {
        add_column.addEventListener('click', () => {
            const cardGrid = add_column.closest('.card').querySelector('.grid');
            const currentRows = cardGrid.querySelectorAll('.mapping-grid').length;

            if (currentRows >= maxRows) {
                alert(`⚠️ 제한 : 최대 ${maxRows}개 행까지만 추가할 수 있습니다.`);
                return;
            }

            const newRow = createMappingRow({
                original_column: '원본 컬럼을 입력하세요.',
                code_name: '',
                is_activate: true
            }, currentRows + 1);

            cardGrid.appendChild(newRow);
        });
    }
});

// 매핑 코드를 서버에서 로드
async function loadMappingCodes() {
    try {
        const response = await fetch('/api/mapping/codes');
        const data = await response.json();
        if (data.success) {
            mappingCodes = data.data;
            console.log('매핑 코드 로드 완료:', mappingCodes);
        }
    } catch (error) {
        console.error('매핑 코드 로드 실패:', error);
    }
}

// 기본 8개 매핑 초기화
function initializeDefaultMappings() {
    const container = document.getElementById('mapping-grid-container');
    if (!container) return;
    
    container.innerHTML = ''; // 기존 내용 초기화
    
    defaultMappings.forEach((mapping, index) => {
        const row = createMappingRow(mapping, index + 1);
        container.appendChild(row);
    });
}

// DB에서 마지막 매핑 불러오기 또는 기본값 사용
async function loadLastMappingsOrDefault() {
    try {
        const response = await fetch('/api/mapping/last');
        const data = await response.json();
        
        if (data.success && data.mappings && data.mappings.length > 0) {
            // DB에 저장된 매핑이 있으면 사용
            console.log('DB에서 매핑 불러오기:', data.mappings);
            apply_mappings(data.mappings);
        } else {
            // 없으면 기본 8개 사용
            console.log('기본 매핑 사용');
            initializeDefaultMappings();
        }
    } catch (error) {
        console.error('매핑 불러오기 실패, 기본값 사용:', error);
        initializeDefaultMappings();
    }
}

// 매핑 행 생성 함수
function createMappingRow(mapping, index) {
    const row = document.createElement('div');
    row.className = 'mapping-grid';
    row.style.cssText = 'display: flex; align-items: center; gap: 10px;';
    
    // select 옵션 생성
    let optionsHtml = '<option value="">선택</option>';
    mappingCodes.forEach(code => {
        const selected = code.code_name === mapping.code_name ? 'selected' : '';
        optionsHtml += `<option value="${code.code_name}" ${selected}>${code.code_name}</option>`;
    });
    
    row.innerHTML = `
        <div class="delete-btn-container">
            <button class="btn delete-row-btn">&minus;</button>
        </div>
        <input class="input" value="${mapping.original_column || ''}" />
        <span style="text-align:center; color:var(--muted)">→</span>
        <select class="select">
            ${optionsHtml}
        </select>
        <div class="toggle-switch">
            <input type="checkbox" class="toggle-input" id="toggle-${index}" ${mapping.is_activate !== false ? 'checked' : ''} />
            <label class="toggle-label" for="toggle-${index}"></label>
        </div>
    `;
    
    // 삭제 버튼 이벤트
    const deleteBtn = row.querySelector('.delete-row-btn');
    const deleteContainer = row.querySelector('.delete-btn-container');
    deleteBtn.addEventListener('click', () => {
        row.remove();
    });
    
    // 편집 모드에 따라 삭제 버튼 표시
    if (isEditMode) {
        deleteContainer.style.visibility = 'visible';
        deleteContainer.style.opacity = '1';
    } else {
        deleteContainer.style.visibility = 'hidden';
        deleteContainer.style.opacity = '0';
    }
    
    // 토글 이벤트
    const toggleEl = row.querySelector('.toggle-input');
    toggleEl.addEventListener('change', () => set_row_state(row, toggleEl.checked));
    set_row_state(row, toggleEl.checked);
    
    return row;
}

// 기존 함수 그대로
function collect_mappings() {
    return Array.from(document.querySelectorAll('.mapping-grid'))
        .map(row => {
            const toggle = row.querySelector('.toggle-input').checked;
            const original = row.querySelector('.input').value.trim();
            const selectEl = row.querySelector('.select');
            const mappingCodeValue = selectEl.value.trim();

            // 비활성화 또는 값 없는 경우 제외
            if (!toggle || !original || !mappingCodeValue) return null;

            return {
                original_column: original,
                mapping_code_id: mappingCodeValue, // code_name을 그대로 전송 (서버에서 변환)
                file_id: null, // 파일 업로드 시점에 설정될 예정
                is_activate: true
            };
        })
        .filter(item => item !== null);
}

function apply_mappings(mappings) {
    const container = document.getElementById('mapping-grid-container');
    if (!container) return;
    
    container.innerHTML = ''; // 기존 내용 초기화
    
    mappings.forEach((map, index) => {
        const row = createMappingRow({
            original_column: map.original_column,
            code_name: map.code_name,
            is_activate: map.is_activate !== false
        }, index + 1);
        container.appendChild(row);
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