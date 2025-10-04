/**
 * PDF 내보내기 기능
 */
document.addEventListener("DOMContentLoaded", function() {
    const exportPdfButton = document.getElementById("btn-export-pdf");

    if (exportPdfButton) {
        exportPdfButton.addEventListener("click", function() {
            const file_id = 'file_12345'; // 예시 file_id

            // 다운로드 로직
            console.log("PDF 다운로드 요청을 서버로 보냅니다.");
            exportPdfButton.disabled = true;
            const originalText = exportPdfButton.textContent;
            exportPdfButton.textContent = "생성 중...";

            // 1. 백엔드의 /download-pdf URL로 요청을 보냅니다.
            fetch(`/download-pdf?file_id=${file_id}`)
                .then(response => {
                    // 2. 서버의 응답이 성공적인지 확인합니다.
                    if (!response.ok) {
                        throw new Error("서버에서 PDF 생성에 실패했습니다.");
                    }
                    const disposition = response.headers.get('Content-Disposition');
                    let filename = `AI분석리포트_${file_id}.pdf`; // 기본 파일 이름
                    if (disposition && disposition.indexOf('attachment') !== -1) {
                        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                        const matches = filenameRegex.exec(disposition);
                        if (matches != null && matches[1]) { 
                            // UTF-8 파일 이름을 디코딩합니다.
                            filename = decodeURI(matches[1].replace(/['"]/g, ''));
                        }
                    }

                    // 응답 본문을 Blob(파일 데이터) 형태로 변환합니다.
                    return response.blob().then(blob => ({ blob, filename }));
                })
                .then(({ blob, filename }) => {
                    // 3. Blob 데이터를 사용하여 다운로드 링크를 생성합니다.
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    // 다운로드될 파일의 기본 이름을 지정합니다.
                    link.setAttribute('download', filename);

                    // 링크를 클릭하여 다운로드를 실행합니다.
                    document.body.appendChild(link);
                    link.click();
                    // 다운로드 후 생성된 링크와 URL을 정리합니다.
                    link.parentNode.removeChild(link);
                    window.URL.revokeObjectURL(url);

                    console.log("PDF 다운로드가 완료되었습니다.");
                    
                    // 성공 메시지 표시
                    showMessage('PDF가 성공적으로 다운로드되었습니다.', 'success');
                })
                .catch(error => {
                    // 오류가 발생한 경우 사용자에게 알립니다.
                    console.error("PDF 다운로드 중 오류 발생:", error);
                    showMessage('PDF 생성에 실패했습니다. 다시 시도해주세요.', 'error');
                })
                .finally(() => {
                    // 버튼을 다시 활성화하고 원래 텍스트로 복원합니다.
                    exportPdfButton.disabled = false;
                    exportPdfButton.textContent = originalText;
                });
        });
    }
});

// 메시지 표시 함수
function showMessage(message, type = 'info') {
    // 기존 메시지 제거
    const existingMessage = document.querySelector('.message-toast');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // 새 메시지 생성
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-toast ${type}`;
    messageDiv.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()">×</button>
    `;
    
    document.body.appendChild(messageDiv);
    
    // 3초 후 자동 제거
    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.remove();
        }
    }, 3000);
}