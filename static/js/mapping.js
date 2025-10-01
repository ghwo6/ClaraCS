const resetButton = document.querySelector('.btn.reset');
if (resetButton) {
    resetButton.addEventListener('click', () => {
        const isConfirmed = confirm("⚠️ 경고 : 원본 컬럼의 매핑 정보가 모두 지워집니다. \n초기화 하시겠습니까?");
        if (isConfirmed) {
            const columnInputs = document.querySelectorAll('.card .grid .mapping-grid .input');
            columnInputs.forEach(input => input.value = '');
            console.log('초기화가 완료되었습니다.');
        } else {
            console.log('초기화가 취소되었습니다.');
        }
    });
}

const editButton = document.querySelector('.button-mapping-group .btn.edit');
const mappingGrids = document.querySelectorAll('.mapping-grid');
const addBtnContainer = document.querySelector('.add-btn-container');

let isEditMode = false;
if (editButton) {
    editButton.addEventListener('click', () => {
        isEditMode = !isEditMode;
        editButton.textContent = isEditMode ? 'Done' : 'Edit';
        editButton.classList.toggle('active', isEditMode);
        if (addBtnContainer) {
            const addBtn = addBtnContainer.querySelector('.btn.add-row-btn');
            addBtn.classList.toggle('editing', isEditMode);
            addBtnContainer.style.visibility = isEditMode ? 'visible' : 'hidden';
            addBtnContainer.style.opacity = isEditMode ? '1' : '0';
        }
        mappingGrids.forEach(grid => {
            const deleteContainer = grid.querySelector('.delete-btn-container');
            if (deleteContainer) {
                deleteContainer.style.visibility = isEditMode ? 'visible' : 'hidden';
                deleteContainer.style.opacity = isEditMode ? '1' : '0';
            }
        });
    });
}
mappingGrids.forEach(grid => {
    const deleteButton = grid.querySelector('.delete-row-btn');
    if (deleteButton) {
        deleteButton.addEventListener('click', (event) => {
            const rowToRemove = event.target.closest('.mapping-grid');
            if (rowToRemove) {
                rowToRemove.remove();
                console.log('매핑 행이 즉시 삭제되었습니다.');
            }
        });
    }
});