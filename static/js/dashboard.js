console.log("✅ dashborad.js 파일이 성공적으로 로드되었습니다!");
document.addEventListener('DOMContentLoaded', function() {
    const filters = document.getElementById('period-filters');
    let categoryPieChart = null;

    filters.addEventListener('click', e => {
        if(e.target.tagName ==='BUTTON') {
            filters.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');

            const period = e.target.textContent; // '7일', '30일' 등
            fetchDashboardData(period);
        }
    });

    // 2. 백엔드에 데이터를 요청하는 함수

    // 2. 백엔드 API 호출 대신, 가상 데이터를 반환하는 함수
    function fetchDashboardData(period) {
        console.log(`'${period}'에 대한 가상 데이터를 불러옵니다.`);

        // --- DB 연결 전 사용할 가상(Dummy) 데이터 ---
        // 나중에 이 부분을 실제 fetch API 호출로 바꾸기만 하면 됩니다.
        const dummyDatabase = {
            '7일': {
                kpi: { completed: 133, pending: 13 },
                top_categories: [
                    { rank: 1, category: '결제', count: 11 },
                    { rank: 2, category: '배송', count: 7 },
                    { rank: 3, category: '환불', count: 1 }
                ],
                category_distribution: [
                    { category: 'Apple', percentage: 34.0 },
                    { category: 'Banana', percentage: 32.0 },
                    { category: 'Grapes', percentage: 18.0 },
                    { category: 'Melon', percentage: 16.0 }
                ]
            },
            '1달': {
                kpi: { completed: 650, pending: 45 },
                top_categories: [
                    { rank: 1, category: '배송', count: 152 },
                    { rank: 2, category: '제품 하자', count: 98 },
                    { rank: 3, category: '결제', count: 77 }
                ],
                category_distribution: [
                    { category: '배송', percentage: 38 },
                    { category: '제품 하자', percentage: 25 },
                    { category: '결제', percentage: 20 },
                    { category: '기타', percentage: 17 }
                ]
            }
        };

        const dataForPeriod = dummyDatabase[period] || dummyDatabase['7일'];
        updateDashboard(dataForPeriod);
    }

    function updateDashboard(data) {
        // KPI, TOP3, 차트만 업데이트 (인사이트 업데이트 코드 제거)
        document.getElementById('completed-count').textContent = data.kpi.completed;
        document.getElementById('pending-count').textContent = data.kpi.pending;

        const topCategoriesTable = document.getElementById('top-categories-table');
        topCategoriesTable.innerHTML = '';
        data.top_categories.forEach(item => {
            const row = `<tr><td>${item.rank}위</td><td>${item.category}</td><td class="right">${item.count}건</td></tr>`;
            topCategoriesTable.innerHTML += row;
        });

        const ctx = document.getElementById('category-pie-chart').getContext('2d');
        const chartData = {
            labels: data.category_distribution.map(item => item.category),
            datasets: [{
                data: data.category_distribution.map(item => item.percentage),
                backgroundColor: ['#36A2EB', '#FFCE56', '#FF6384', '#4BC0C0', '#9966FF'],
            }]
        };

        if (categoryPieChart) {
            categoryPieChart.destroy();
        }
        categoryPieChart = new Chart(ctx, { type: 'pie', data: chartData });
    }

    const initialButton = document.querySelector('#period-filters .btn');
    if (initialButton) {
        initialButton.classList.add('active');
        fetchDashboardData(initialButton.textContent);
    }
});