const upload_file = document.getElementById('upload_file');
const file_input = document.getElementById('file_input'); 
const select_all = document.getElementById('select_all');
const delete_files = document.getElementById('delete_file');

const uploader = document.querySelector('.uploader');
const title = document.querySelector('.title');
const desc = document.querySelector('.desc');
const file_list = document.querySelector('.file_list');

const default_title = title.textContent;
const default_desc = desc.textContent;

let all_files = [];


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

