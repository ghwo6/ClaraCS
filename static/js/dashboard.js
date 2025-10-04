console.log("✅ dashboard.js 파일이 성공적으로 로드되었습니다!");

document.addEventListener('DOMContentLoaded', function() {
    const filters = document.getElementById('period-filters');
    let categoryPieChart = null; // 차트 인스턴스를 저장할 변수

    // --- 이벤트 리스너 설정 (모든 오타 수정 완료) ---
    filters.addEventListener('click', e => {
        // 클릭된 요소가 <button>이 맞는지 확인
        if (e.target.tagName === 'BUTTON') {
            // 모든 버튼에서 'active' 스타일 제거
            filters.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
            
            // 지금 클릭한 버튼에만 'active' 스타일 추가
            e.target.classList.add('active');
            
            // 버튼의 텍스트("7일", "1달")를 가져와 데이터 요청
            const period = e.target.textContent;
            loadDashboardData(period);
        }
    });

    /**
     * [UI 제어] 화면의 대시보드 데이터를 업데이트하는 함수
     * @param {Object} data - API로부터 받은 데이터
     */
    function updateDashboardUI(data) {
        // KPI, TOP3, 차트 업데이트
        document.getElementById('completed-count').textContent = data.kpi.completed;
        document.getElementById('pending-count').textContent = data.kpi.pending;

        const topCategoriesTable = document.getElementById('top-categories-table');
        topCategoriesTable.innerHTML = ''; // 기존 내용 초기화
        data.top_categories.forEach(item => {
            const row = `<tr><td>${item.rank}위</td><td>${item.category}</td><td class="right">${item.count}건</td></tr>`;
            topCategoriesTable.innerHTML += row;
        });

        const ctx = document.getElementById('category-pie-chart').getContext('2d');
        const chartData = {
            labels: data.category_distribution.map(item => item.category),
            datasets: [{
                data: data.category_distribution.map(item => item.percentage),
                backgroundColor: ['#5B8CFF', '#4BC0C0', '#FFCE56', '#FF6384', '#9966FF'],
                borderWidth: 0
            }]
        };

        // 기존 차트가 있으면 파괴하고 새로 그립니다.
        if (categoryPieChart) {
            categoryPieChart.destroy();
        }
        
        categoryPieChart = new Chart(ctx, {
            type: 'pie',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#ffffff', boxWidth: 12, padding: 15 },
                        onClick: null
                    }

                }
            }
        });
    }

    /**
     * [데이터 로직] 가상 데이터를 가져오는 함수
     * @param {string} period - 선택된 기간
     */
    function loadDashboardData(period) {
        console.log(`[가상 데이터] '${period}' 데이터를 불러옵니다.`);

        const dummyDatabase = {
            '7일': {
                kpi: { completed: 133, pending: 13 },
                top_categories: [
                    { rank: 1, category: '결제', count: 11 },
                    { rank: 2, category: '배송', count: 7 },
                    { rank: 3, category: '환불', count: 1 }
                ],
                category_distribution: [
                    { category: 'Apple', percentage: 34.0 }, { category: 'Banana', percentage: 32.0 },
                    { category: 'Grapes', percentage: 18.0 }, { category: 'Melon', percentage: 16.0 }
                ]
            },
            '1달': {
                kpi: { completed: 542, pending: 41 },
                top_categories: [
                    { rank: 1, category: '배송', count: 88 },
                    { rank: 2, category: '결제', count: 71 },
                    { rank: 3, category: '품질/AS', count: 35 }
                ],
                category_distribution: [
                    { category: '결제', percentage: 35 }, { category: '배송', percentage: 45 },
                    { category: '환불', percentage: 10 }, { category: '품질/AS', percentage: 8 },
                    { category: '기타', percentage: 2 }
                ]
            },
            '3달': {
                kpi: { completed: 1890, pending: 102 },
                top_categories: [
                    { rank: 1, category: '배송', count: 350 },
                    { rank: 2, category: '품질/AS', count: 210 },
                    { rank: 3, category: '결제', count: 180 }
                ],
                category_distribution: [
                    { category: '결제', percentage: 25 }, { category: '배송', percentage: 40 },
                    { category: '환불', percentage: 15 }, { category: '품질/AS', percentage: 15 },
                    { category: '기타', percentage: 5 }
                ]
            }
        };

        const dataForPeriod = dummyDatabase[period] || dummyDatabase['7일'];
        updateDashboardUI(dataForPeriod);
    }

    // --- 초기 데이터 로드 ---
    const initialButton = document.querySelector('#period-filters button.active');
    if (initialButton) {
        loadDashboardData(initialButton.textContent);
    }
});