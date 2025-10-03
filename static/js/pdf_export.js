document.addEventListener("DOMContentLoaded", function() {
  const exportPdfButton = document.getElementById("btn-export-pdf");
  if (exportPdfButton) {
    exportPdfButton.addEventListener("click", function() {
        // 다운로드 로직

        // 가상의 <a>태그
        const link = document.createElement('a');

        // 다운로드할 파일의 경로
        // 예제 파일 a.pdf static/downloads/a.pdf
        // 이후에 파일을 생성해서 넣도록 진행할 예정입니다.(호재)
        link.href = 'static/downloads/a.pdf';

        // 다운로드 시 저장할 파일 이름을 지정합니다.
        link.download = 'ClaraCS_임시리포트.pdf';

        // 가상의 a 태그 클릭
        link.click();

        // -- 다운로드 로직 끝 --

        console.log("PDF 다운로드를 시작합니다.");
    });
  }
});