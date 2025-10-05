const save_btn = document.getElementById('save_btn');
const upload_file = document.getElementById('upload_file');
const file_input = document.getElementById('file_input'); 
const select_all = document.getElementById('select_all');
const delete_files = document.getElementById('delete_file');

const uploader = document.querySelector('.uploader');
const title = document.querySelector('.title');
const desc = document.querySelector('.desc');
const file_list = document.querySelector('.file_list');
const validation_result = document.getElementById('validation_result');

const default_title = title.textContent;
const default_desc = desc.textContent;

let all_files = [];

// 저장 버튼 클릭 이벤트
if (save_btn) {
    save_btn.addEventListener('click', () => {
        validateAndUploadFiles();
    });
}

upload_file.addEventListener('click', () => {
    file_input.click();
    console.log('File upload button clicked');
});
file_input.addEventListener('change', (e) => {
    handle_files(e.target.files);
    console.log('File input changed:', e.target.files);
});

uploader.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploader.classList.add('dragover');
});
uploader.addEventListener('drop', (e) => {
    e.preventDefault();
    uploader.classList.remove('dragover');
    const files = Array.from (e.dataTransfer.files);
    const valid_files = files.filter(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        return ['csv', 'xlsx', 'xls'].includes(ext);
    });
    const invalid_files = files.filter(file => !valid_files.includes(file));
    if (invalid_files.length > 0) {
        alert('⚠️ 제한 : 허용되는 파일 형식은 .csv, .xlsx, .xls 입니다.');
        console.log('Invalid files filtered out:', invalid_files.map(f => f.name));
    }
        if (valid_files.length > 0) {
            handle_files(valid_files);
            console.log('Files dropped into drag area:', valid_files.map(f => f.name));
        }
    });
uploader.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploader.classList.remove('dragleave');
    console.log('Files removed from drag area');
});

function format_size(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
function display_upload_summary() {
    const summary = document.getElementById('upload_summary');
    if (!summary) return;
    const total_count = all_files.length;
    const total_size = all_files.reduce((sum, file) => sum + (file.size || 0), 0);
    summary.textContent = `총 ${total_count}개의 파일이 있습니다. (${format_size(total_size)})`;
}

function handle_files(files) {
    all_files = all_files.concat(Array.from(files));

    file_list.innerHTML = '';
    title.innerHTML = '';
    desc.innerHTML = '';

    all_files.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file_item';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = 'file_' + index;
        checkbox.value = file.name;

        checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }

            const checkboxes = file_list.querySelectorAll('input[type="checkbox"]');
            const all_checked = Array.from(checkboxes).every(cb => cb.checked);
            const some_checked = Array.from(checkboxes).some(cb => cb.checked);

            select_all.checked = all_checked;
            select_all.indeterminate = !all_checked && some_checked;
        });

        const label = document.createElement('label');
        label.htmlFor = 'file_' + index;
        label.innerHTML = `${file.name} <span class ="file_size">(${formatSize(file.size)})</span>`;
        
        item.appendChild(checkbox);
        item.appendChild(label);
        file_list.appendChild(item);
    });

    select_all.checked = false;
    select_all.indeterminate = false;

    updateSummary();
    console.log('Files handled, total files:', all_files.map(f => f.name));
} 

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function updateSummary() {
    const summary = document.getElementById('upload_summary');
    if (!summary) return;
    const totalFiles = all_files.length;
    const totalSize = all_files.reduce((sum, f) => sum + (f.size || 0), 0);
    summary.textContent = `총 ${totalFiles}개의 파일이 있습니다. (${formatSize(totalSize)})`;
}

let fileId = null;
let createdAt = null;

// 유효성 검사 및 파일 업로드
async function validateAndUploadFiles() {
    // 선택된 파일이 있는지 확인
    if (all_files.length === 0) {
        showValidationStep('error', '업로드할 파일을 선택해주세요.', true);
        return;
    }

    // 검증 단계 초기화
    initValidationSteps(all_files.length);

    try {
        // 1. 컬럼 매핑 저장
        updateValidationStep('mapping', 'loading', '컬럼 매핑 확인 및 저장 중...');
        
        const mappings = collect_mappings();
        if (mappings.length === 0) {
            updateValidationStep('mapping', 'error', '컬럼 매핑이 설정되지 않았습니다');
            return;
        }
        
        const mappingResponse = await fetch('/api/mapping/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mappings: mappings })
        });
        
        const mappingData = await mappingResponse.json();
        if (mappingData.status !== 'success') {
            updateValidationStep('mapping', 'error', '컬럼 매핑 저장 실패');
            return;
        }
        updateValidationStep('mapping', 'success', `컬럼 매핑 저장 완료 (${mappings.length}개 컬럼)`);
        await sleep(400);

        // 2. 각 파일별로 검증
        let allFilesValid = true;
        let failedFile = null;
        
        for (let i = 0; i < all_files.length; i++) {
            const file = all_files[i];
            const fileStepPrefix = `file_${i}`;
            
            // 2-1. 파일 형식 확인
            updateFileValidationStep(i, 'format', 'loading', `파일 형식 확인 중...`);
            await sleep(200);
            
            const ext = file.name.split('.').pop().toLowerCase();
            if (!['csv', 'xlsx', 'xls'].includes(ext)) {
                updateFileValidationStep(i, 'format', 'error', `지원하지 않는 파일 형식 (.${ext})`);
                allFilesValid = false;
                failedFile = file.name;
                break;
            }
            updateFileValidationStep(i, 'format', 'success', `파일 형식 확인 완료 (.${ext})`);
            await sleep(200);
            
            // 2-2. 서버에 파일 검증 요청
            updateFileValidationStep(i, 'validate', 'loading', '파일 데이터 검증 중...');
            
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/upload/validate', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!result.success || !result.data.is_valid) {
                updateFileValidationStep(i, 'validate', 'error', '파일 검증 실패');
                await sleep(200);
                
                // 상세 오류 표시
                displayDetailedValidationErrors(file.name, result.data.errors);
                allFilesValid = false;
                failedFile = file.name;
                break;
            }
            
            // 검증 성공 - 세부 항목 표시
            const errors = result.data.errors || [];
            const hasMissingValues = errors.some(e => e.type === 'missing_values');
            const hasDateFormat = errors.some(e => e.type === 'date_format');
            
            updateFileValidationStep(i, 'validate', 'success', 
                `검증 완료 (${result.data.row_count}행, ${result.data.column_count}컬럼)`);
            await sleep(200);
            
            // 2-3. 필수 컬럼 확인
            updateFileValidationStep(i, 'required', 'loading', '필수 컬럼 확인 중...');
            await sleep(200);
            updateFileValidationStep(i, 'required', 'success', '필수 컬럼 확인 완료');
            await sleep(200);
            
            // 2-4. 날짜 형식 확인
            updateFileValidationStep(i, 'date', 'loading', '날짜 형식 확인 중...');
            await sleep(200);
            updateFileValidationStep(i, 'date', 'success', '날짜 형식 확인 완료');
            await sleep(300);
        }
        
        if (!allFilesValid) {
            return; // 검증 실패 시 중단
        }

        // 3. 모든 파일 검증 통과
        updateValidationStep('final', 'loading', '최종 검증 중...');
        await sleep(300);
        updateValidationStep('final', 'success', `✅ 모든 파일 검증 완료! (${all_files.length}개 파일)`);
        await sleep(500);
        
        // 4. 데이터 업로드 시작
        await uploadFiles();

    } catch (error) {
        console.error('검증 중 오류:', error);
        showValidationStep('error', '❌ 검증 중 오류가 발생했습니다: ' + error.message);
    }
}

// 파일 업로드 함수
async function uploadFiles() {
    let uploadedCount = 0;
    let totalFiles = all_files.length;
    let totalTickets = 0;

    // 업로드 단계 추가 (기존 검증 내역 유지)
    const uploadSection = document.createElement('div');
    uploadSection.style.cssText = 'margin-top: 20px; padding: 10px; background: rgba(0, 0, 0, 0.2); border-radius: 6px;';
    uploadSection.innerHTML = `
        <div id="step_upload" class="validation-step" style="padding: 8px; background: rgba(255, 255, 255, 0.03); border-radius: 4px;">
            <span class="step-icon" style="font-size: 16px; margin-right: 8px;">⏳</span>
            <span class="step-text" style="color: var(--primary); font-weight: 600;">데이터 업로드 중...</span>
        </div>
    `;
    validation_result.appendChild(uploadSection);

    for (let i = 0; i < all_files.length; i++) {
        const file = all_files[i];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', 1); // 임시 user_id

        // 진행 상황 업데이트
        const stepElement = document.getElementById('step_upload');
        if (stepElement) {
            const textSpan = stepElement.querySelector('.step-text');
            textSpan.textContent = `데이터 업로드 중... (${i + 1}/${totalFiles})`;
        }

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                uploadedCount++;
                totalTickets += data.data.tickets_inserted;
                console.log(`파일 업로드 성공 (${uploadedCount}/${totalFiles}):`, data.data);
                
                // 마지막 파일 업로드 완료 시
                if (uploadedCount === totalFiles) {
                    fileId = data.data.file_id;
                    createdAt = data.data.created_at;
                    
                    // 최종 성공 메시지
                    const stepElement = document.getElementById('step_upload');
                    if (stepElement) {
                        const iconSpan = stepElement.querySelector('.step-icon');
                        const textSpan = stepElement.querySelector('.step-text');
                        iconSpan.textContent = '✓';
                        iconSpan.style.color = '#22c55e';
                        textSpan.textContent = '데이터 업로드 완료';
                        textSpan.style.color = '#22c55e';
                        textSpan.style.fontWeight = 'normal';
                    }
                    
                    await sleep(300);
                    
                    // 최종 성공 메시지 추가
                    const successSection = document.createElement('div');
                    successSection.style.cssText = 'margin-top: 20px; padding: 15px; background: rgba(16, 185, 129, 0.1); border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.3);';
                    successSection.innerHTML = `
                        <div style="color: #10b981; font-weight: 600; font-size: 15px; margin-bottom: 10px;">
                            🎉 모든 처리가 완료되었습니다!
                        </div>
                        <div style="color: var(--text); font-size: 13px; line-height: 1.6;">
                            <strong>처리 결과:</strong><br>
                            • 파일 업로드: ${totalFiles}개<br>
                            • 티켓 저장: ${totalTickets}건
                        </div>
                    `;
                    validation_result.appendChild(successSection);
                    
                    // 업로드 성공 후 파일 목록 초기화
                    all_files = [];
                    file_list.innerHTML = '';
                    title.textContent = default_title;
                    desc.textContent = default_desc;
                    updateSummary();
                }
            } else {
                console.error(`파일 업로드 실패 (${i + 1}/${totalFiles}):`, data.error);
                
                const stepElement = document.getElementById('step_upload');
                if (stepElement) {
                    const iconSpan = stepElement.querySelector('.step-icon');
                    const textSpan = stepElement.querySelector('.step-text');
                    iconSpan.textContent = '✗';
                    iconSpan.style.color = '#ef4444';
                    textSpan.textContent = '데이터 업로드 실패';
                    textSpan.style.color = '#ef4444';
                }
                
                await sleep(300);
                showValidationStep('error', `❌ 파일 업로드 실패: ${data.error}`);
            }
        } catch (error) {
            console.error(`서버 오류 발생 (${i + 1}/${totalFiles}):`, error);
            
            const stepElement = document.getElementById('step_upload');
            if (stepElement) {
                const iconSpan = stepElement.querySelector('.step-icon');
                const textSpan = stepElement.querySelector('.step-text');
                iconSpan.textContent = '✗';
                iconSpan.style.color = '#ef4444';
                textSpan.textContent = '서버 오류 발생';
                textSpan.style.color = '#ef4444';
            }
            
            await sleep(300);
            showValidationStep('error', '❌ 서버 오류가 발생했습니다.');
        }
    }
}

// sleep 유틸리티 함수
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// 검증 단계 초기화
function initValidationSteps(fileCount) {
    if (!validation_result) return;
    
    let html = '<div class="validation-steps" style="font-size: 13px; max-height: 450px; overflow-y: auto; padding: 10px; background: rgba(0, 0, 0, 0.2); border-radius: 6px;">';
    
    // 1. 컬럼 매핑
    html += `
        <div id="step_mapping" class="validation-step" style="margin-bottom: 10px; padding: 8px; background: rgba(255, 255, 255, 0.03); border-radius: 4px;">
            <span class="step-icon" style="font-size: 16px; margin-right: 8px;">⏳</span>
            <span class="step-text" style="color: var(--text);">컬럼 매핑 확인 중...</span>
        </div>
    `;
    
    // 2. 각 파일별 검증 단계
    for (let i = 0; i < fileCount; i++) {
        html += `
            <div class="file-validation-group" style="margin-left: 0px; margin-top: 15px; margin-bottom: 15px; padding: 12px; background: rgba(255, 255, 255, 0.05); border-radius: 6px; border-left: 3px solid var(--primary);">
                <div style="font-weight: 600; margin-bottom: 10px; color: var(--text); display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">📄</span>
                    <span>${all_files[i].name}</span>
                </div>
                <div id="step_file_${i}_format" class="validation-step" style="margin-bottom: 8px; padding-left: 8px; font-size: 12px;">
                    <span class="step-icon" style="font-size: 14px; margin-right: 6px;">⏳</span>
                    <span class="step-text" style="color: var(--muted);">파일 형식 확인 대기 중...</span>
                </div>
                <div id="step_file_${i}_validate" class="validation-step" style="margin-bottom: 8px; padding-left: 8px; font-size: 12px;">
                    <span class="step-icon" style="font-size: 14px; margin-right: 6px;">⏳</span>
                    <span class="step-text" style="color: var(--muted);">데이터 검증 대기 중...</span>
                </div>
                <div id="step_file_${i}_required" class="validation-step" style="margin-bottom: 8px; padding-left: 8px; font-size: 12px;">
                    <span class="step-icon" style="font-size: 14px; margin-right: 6px;">⏳</span>
                    <span class="step-text" style="color: var(--muted);">필수 컬럼 확인 대기 중...</span>
                </div>
                <div id="step_file_${i}_date" class="validation-step" style="margin-bottom: 0; padding-left: 8px; font-size: 12px;">
                    <span class="step-icon" style="font-size: 14px; margin-right: 6px;">⏳</span>
                    <span class="step-text" style="color: var(--muted);">날짜 형식 확인 대기 중...</span>
                </div>
            </div>
        `;
    }
    
    // 3. 최종 검증
    html += `
        <div id="step_final" class="validation-step" style="margin-bottom: 0; margin-top: 15px; padding: 8px; background: rgba(255, 255, 255, 0.03); border-radius: 4px;">
            <span class="step-icon" style="font-size: 16px; margin-right: 8px;">⏳</span>
            <span class="step-text" style="color: var(--text);">최종 검증 대기 중...</span>
        </div>
    `;
    
    html += '</div>';
    
    // 기존 내용에 추가 (교체하지 않음)
    if (validation_result.querySelector('.validation-steps')) {
        // 이미 검증 단계가 있으면 새로운 세션으로 추가
        const separator = document.createElement('div');
        separator.style.cssText = 'height: 1px; background: rgba(255, 255, 255, 0.1); margin: 20px 0;';
        validation_result.appendChild(separator);
        
        const newSection = document.createElement('div');
        newSection.innerHTML = html;
        validation_result.appendChild(newSection.firstChild);
    } else {
        // 첫 번째 검증이면 교체
        validation_result.innerHTML = html;
    }
}

// 파일별 검증 단계 업데이트
function updateFileValidationStep(fileIndex, stepType, status, message) {
    const stepId = `step_file_${fileIndex}_${stepType}`;
    const stepElement = document.getElementById(stepId);
    if (!stepElement) return;
    
    const iconSpan = stepElement.querySelector('.step-icon');
    const textSpan = stepElement.querySelector('.step-text');
    
    if (status === 'loading') {
        iconSpan.textContent = '⏳';
        iconSpan.style.color = 'var(--primary)';
        textSpan.textContent = message;
        textSpan.style.color = 'var(--primary)';
        textSpan.style.fontWeight = '600';
    } else if (status === 'success') {
        iconSpan.textContent = '✓';
        iconSpan.style.color = '#10b981';
        textSpan.textContent = message;
        textSpan.style.color = '#10b981';
        textSpan.style.fontWeight = 'normal';
    } else if (status === 'error') {
        iconSpan.textContent = '✗';
        iconSpan.style.color = '#ef4444';
        textSpan.textContent = message;
        textSpan.style.color = '#ef4444';
        textSpan.style.fontWeight = '600';
    }
}

// 검증 단계 업데이트
function updateValidationStep(stepId, status, message) {
    const stepElement = document.getElementById(`step_${stepId}`);
    if (!stepElement) return;
    
    const iconSpan = stepElement.querySelector('.step-icon');
    const textSpan = stepElement.querySelector('.step-text');
    
    if (status === 'loading') {
        iconSpan.textContent = '⏳';
        iconSpan.style.color = 'var(--primary)';
        textSpan.textContent = message;
        textSpan.style.color = 'var(--primary)';
        textSpan.style.fontWeight = '600';
    } else if (status === 'success') {
        iconSpan.textContent = '✓';
        iconSpan.style.color = '#10b981';
        textSpan.textContent = message;
        textSpan.style.color = '#10b981';
        textSpan.style.fontWeight = 'normal';
    } else if (status === 'error') {
        iconSpan.textContent = '✗';
        iconSpan.style.color = '#ef4444';
        textSpan.textContent = message;
        textSpan.style.color = '#ef4444';
        textSpan.style.fontWeight = '600';
    }
}

// 단일 메시지 표시 (오류 등)
function showValidationStep(type, message, clearAll = false) {
    if (!validation_result) return;

    let html = '';
    if (type === 'error') {
        html = `<div style="color: #ef4444; padding: 12px; background: rgba(239, 68, 68, 0.1); border-radius: 6px; border: 1px solid rgba(239, 68, 68, 0.3);">${message}</div>`;
    } else if (type === 'success') {
        html = `<div style="color: #10b981; padding: 12px; background: rgba(16, 185, 129, 0.1); border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.3);">${message}</div>`;
    }

    if (clearAll) {
        validation_result.innerHTML = html;
    } else {
        validation_result.innerHTML += html;
    }
}

// 상세 오류 표시
function displayDetailedValidationErrors(filename, errors) {
    if (!validation_result) return;
    
    let errorHtml = '<div style="margin-top: 15px; padding: 15px; background: rgba(239, 68, 68, 0.1); border-radius: 6px; border: 1px solid rgba(239, 68, 68, 0.3);">';
    errorHtml += `<p style="font-weight: 600; color: #ef4444; margin-bottom: 12px; font-size: 14px;">❌ ${filename} 검증 실패</p>`;
    errorHtml += '<ul style="list-style: none; padding-left: 0; margin-left: 0;">';
    
    errors.forEach(error => {
        if (error.type === 'column_not_found') {
            errorHtml += `<li style="color: var(--text); margin-bottom: 10px; padding: 8px; background: rgba(0, 0, 0, 0.2); border-radius: 4px; font-size: 12px;">
                <strong style="color: #ef4444;">컬럼 매핑 오류:</strong> <span class="badge danger" style="background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 2px 6px; border-radius: 3px; font-size: 11px;">${error.column}</span><br>
                <span style="font-size: 11px; color: var(--muted); margin-left: 0px; display: inline-block; margin-top: 4px;">
                    → 매핑된 컬럼 '<code style="background: rgba(255,255,255,0.1); padding: 1px 4px; border-radius: 2px;">${error.expected_column}</code>'을(를) 파일에서 찾을 수 없습니다.<br>
                    → 컬럼 매핑 설정을 확인하고 파일의 실제 컬럼명과 일치시켜주세요.
                </span>
            </li>`;
        } else if (error.type === 'missing_values') {
            errorHtml += `<li style="color: var(--text); margin-bottom: 10px; padding: 8px; background: rgba(0, 0, 0, 0.2); border-radius: 4px; font-size: 12px;">
                <strong style="color: #ef4444;">필수 컬럼 누락:</strong> <span class="badge danger" style="background: rgba(239, 68, 68, 0.2); color: #ef4444; padding: 2px 6px; border-radius: 3px; font-size: 11px;">${error.column}</span> 컬럼에서 ${error.count}건의 빈 값 발견<br>
                <span style="font-size: 11px; color: var(--muted); margin-left: 0px; display: inline-block; margin-top: 4px;">→ 해당 컬럼의 모든 행에 값이 필요합니다.</span>
            </li>`;
        } else if (error.type === 'date_format') {
            errorHtml += `<li style="color: var(--text); margin-bottom: 10px; padding: 8px; background: rgba(0, 0, 0, 0.2); border-radius: 4px; font-size: 12px;">
                <strong style="color: #f59e0b;">날짜 형식 불일치:</strong> <span class="badge warn" style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; padding: 2px 6px; border-radius: 3px; font-size: 11px;">${error.column}</span> 컬럼에서 ${error.count}건의 잘못된 형식 발견<br>
                <span style="font-size: 11px; color: var(--muted); margin-left: 0px; display: inline-block; margin-top: 4px;">→ 권장 형식: YYYY-MM-DD (예: 2025-10-05)</span>
            </li>`;
        } else {
            errorHtml += `<li style="color: #ef4444; margin-bottom: 8px; font-size: 12px;">${error.message}</li>`;
        }
    });
    
    errorHtml += '</ul>';
    errorHtml += '<p style="margin-top: 12px; color: var(--muted); font-size: 12px; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 10px;">💡 파일을 수정한 후 다시 시도해주세요.</p>';
    errorHtml += '</div>';
    
    validation_result.innerHTML += errorHtml;
}

// 유효성 검사 결과 표시 함수 (호환성 유지)
function showValidationResult(type, message) {
    showValidationStep(type, message, true);
}

select_all.addEventListener('change', () => {
    const checkboxes = file_list.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.checked = select_all.checked;
        if (select_all.checked) {
            cb.parentElement.classList.add('selected');
        } else {
            cb.parentElement.classList.remove('selected');
        }
    });
});

delete_files.addEventListener('click', () => {
    const checked_items = file_list.querySelectorAll('input[type="checkbox"]:checked');
    checked_items.forEach((cb) => {
        const index = all_files.findIndex(f => f.name === cb.value);
        if (index > -1) all_files.splice(index, 1);
        cb.parentElement.remove();
        console.log('File deleted:', cb.value);
    });
    if (all_files.length === 0) {
        title.textContent = default_title;
        desc.textContent = default_desc;
        file_input.value = '';
        const summary = document.getElementById('upload_summary');
        if (summary) summary.textContent = '';
        console.log('All files deleted, reset to default state');
        
        select_all.checked = false;
        select_all.indeterminate = false;
    } else {
        updateSummary();
    }
    console.log('Delete button clicked, remaining files:', all_files.map(f => f.name));
});

