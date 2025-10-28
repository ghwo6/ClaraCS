document.addEventListener("DOMContentLoaded", function() {
    const sendEmailButton = document.getElementById("btn-send-email");

    if (sendEmailButton) {
        sendEmailButton.addEventListener("click", async function() {
            let reportId = window.reportManager?.currentReportId;

            // 1. 리포트가 없으면 서버에서 마지막 리포트 조회
            if (!reportId) {
                try {
                    const response = await fetch('/api/report/latest', {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    if (response.ok) {
                        const result = await response.json();
                        if (result.success && result.data && result.data.report_id) {
                            reportId = result.data.report_id;
                            console.log(`마지막 리포트 사용: report_id=${reportId}`);
                        } else {
                            alert('생성된 리포트가 없습니다. 먼저 리포트를 생성해주세요.');
                            return;
                        }
                    } else {
                        alert('리포트를 찾을 수 없습니다. 먼저 리포트를 생성해주세요.');
                        return;
                    }
                } catch (err) {
                    console.error('마지막 리포트 조회 실패:', err);
                    alert('리포트를 찾을 수 없습니다. 먼저 리포트를 생성해주세요.');
                    return;
                }
            }

            // 2. 이메일 입력
            const emailTo = prompt("📤️ 리포트(PDF)를 전송할 이메일 주소를 입력해주세요 :");
            if (!emailTo) return;

            sendEmailButton.disabled = true;
            const originalText = sendEmailButton.textContent;
            sendEmailButton.textContent = "전송 중...";

            try {
                // 3. 서버로 POST 요청
                const response = await fetch("/send-pdf-email", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ report_id: reportId, email: emailTo })
                });

                const result = await response.json();
                if (response.ok && result.success) {
                    showMessage(`PDF가 ${emailTo}로 전송되었습니다.`, "success");
                } else {
                    showMessage(result.error || "PDF 전송에 실패했습니다.", "error");
                }
            } catch (err) {
                console.error("PDF 이메일 전송 오류:", err);
                showMessage("PDF 전송 중 오류가 발생했습니다.", "error");
            } finally {
                sendEmailButton.disabled = false;
                sendEmailButton.textContent = originalText;
            }
        });
    }
});

// 메시지 표시(pdf_export.js와 동일)
function showMessage(message, type = 'info') {
    const existingMessage = document.querySelector('.message-toast');
    if (existingMessage) existingMessage.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message-toast ${type}`;
    messageDiv.innerHTML = `<span>${message}</span><button onclick="this.parentElement.remove()">×</button>`;
    document.body.appendChild(messageDiv);

    setTimeout(() => {
        if (messageDiv.parentElement) messageDiv.remove();
    }, 3000);
}