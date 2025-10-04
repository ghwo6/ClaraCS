// 사이드바 메뉴 포커싱 처리 (페이지 단위 이동)
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav a');
    
    // 현재 페이지 경로 확인
    const currentPath = window.location.pathname;
    
    // 메뉴 클릭 이벤트 처리 - 실제 페이지 이동
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        
        // 현재 페이지에 맞는 메뉴 활성화
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            link.classList.add('active');
        }
    });
});
