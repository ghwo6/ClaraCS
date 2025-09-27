// 사이드바 메뉴 포커싱 처리
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav a');
    const sections = document.querySelectorAll('.section');
    
    // 초기 로드 시 현재 섹션에 맞는 메뉴 활성화
    function setActiveMenu() {
        const currentSection = getCurrentSection();
        navLinks.forEach(link => {
            link.classList.remove('active');
            const href = link.getAttribute('href');
            if (href === '#' && currentSection === 'dashboard') {
                link.classList.add('active');
            } else if (href === currentSection) {
                link.classList.add('active');
            }
        });
    }
    
    // 현재 보이는 섹션 확인
    function getCurrentSection() {
        const scrollPosition = window.scrollY + 100; // 오프셋 추가
        
        for (let section of sections) {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                return section.id;
            }
        }
        return 'dashboard'; // 기본값
    }
    
    // 메뉴 클릭 이벤트 처리
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 모든 메뉴에서 active 클래스 제거
            navLinks.forEach(navLink => navLink.classList.remove('active'));
            
            // 클릭된 메뉴에 active 클래스 추가
            this.classList.add('active');
            
            // 해당 섹션으로 스크롤
            const href = this.getAttribute('href');
            if (href === '#') {
                // 대시보드로 스크롤
                document.getElementById('dashboard').scrollIntoView({
                    behavior: 'smooth'
                });
            } else if (href.startsWith('#')) {
                const targetId = href.substring(1);
                const targetSection = document.getElementById(targetId);
                if (targetSection) {
                    targetSection.scrollIntoView({
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
    
    // 스크롤 시 현재 섹션에 맞는 메뉴 활성화
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            const currentSection = getCurrentSection();
            navLinks.forEach(link => {
                link.classList.remove('active');
                const href = link.getAttribute('href');
                if (href === '#' && currentSection === 'dashboard') {
                    link.classList.add('active');
                } else if (href === '#' + currentSection) {
                    link.classList.add('active');
                }
            });
        }, 100);
    });
    
    // 초기 설정
    setActiveMenu();
});
