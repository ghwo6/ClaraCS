console.log("✅ dashboard.js 파일이 성공적으로 로드되었습니다!");

// Chart.js datalabels 플러그인 등록 (퍼센트 표시용)
if (typeof Chart !== 'undefined' && typeof ChartDataLabels !== 'undefined') {
    Chart.register(ChartDataLabels);
    console.log('✅ Chart.js datalabels 플러그인 등록 완료');
}

class DashboardManager {
    constructor() {
        this.categoryPieChart = null;
        this.currentUserId = this.getUserId();
        this.init();
    }
    
    getUserId() {
        const sessionUserId = sessionStorage.getItem('user_id');
        if (sessionUserId) return parseInt(sessionUserId);
        const localUserId = localStorage.getItem('user_id');
        if (localUserId) return parseInt(localUserId);
        return window.DEFAULT_USER_ID || 1;
    }
    
    init() {
        this.bindEvents();
        this.loadDashboardData();
    }
    
    bindEvents() {
        const filters = document.getElementById('period-filters');
        if (filters) {
            filters.addEventListener('click', e => {
                if (e.target.tagName === 'BUTTON') {
                    filters.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
                    e.target.classList.add('active');
                    const period = e.target.textContent;
                    this.loadDashboardData(period);
                }
            });
        }
    }
    
    async loadDashboardData(period = '7일') {
        console.log(`대시보드 데이터 로드 시작: period=${period}, user_id=${this.currentUserId}`);
        
        try {
            // 실제 DB에서 데이터 가져오기
            const data = await this.fetchDashboardData(this.currentUserId);
            
            console.log('조회된 데이터:', data);
            
            if (data) {
                this.updateDashboardUI(data);
            } else {
                console.warn('⚠️ 조회된 데이터가 없습니다. 자동 분류를 먼저 실행하세요.');
            }
        } catch (error) {
            console.error('❌ 대시보드 데이터 로드 실패:', error);
        }
    }
    
    async fetchDashboardData(userId) {
        try {
            console.log('🔍 1단계: 최신 파일 ID 조회 중...');
            
            // 최신 파일 ID 가져오기
            const fileResponse = await fetch('/api/upload/latest-file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            });
            
            console.log('파일 조회 응답 상태:', fileResponse.status);
            
            if (!fileResponse.ok) {
                const errorData = await fileResponse.json();
                console.warn('⚠️ 최신 파일 없음:', errorData.error);
                return null;
            }
            
            const fileResult = await fileResponse.json();
            console.log('파일 조회 결과:', fileResult);
            
            const fileId = fileResult.data?.file_id;
            
            if (!fileId) {
                console.warn('⚠️ 파일 ID가 응답에 없습니다');
                return null;
            }
            
            console.log(`✅ 최신 파일 ID: ${fileId}`);
            console.log('🔍 2단계: 자동 분류 통계 조회 중...');
            
            // 자동 분류 데이터 조회 (KPI, TOP 3, 카테고리 비율)
            const statsResponse = await fetch('/api/classifications/stats', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_id: fileId })
            });
            
            console.log('통계 조회 응답 상태:', statsResponse.status);
            
            if (!statsResponse.ok) {
                const errorData = await statsResponse.json();
                console.warn('⚠️ 분류 데이터 없음:', errorData.error);
                return null;
            }
            
            const statsResult = await statsResponse.json();
            console.log('통계 조회 결과:', statsResult);
            
            if (!statsResult.success) {
                console.warn('⚠️ 통계 조회 실패:', statsResult.error);
                return null;
            }
            
            console.log('✅ 대시보드 데이터 조회 성공');
            return statsResult.data || null;
            
        } catch (error) {
            console.error('❌ 대시보드 데이터 조회 실패:', error);
            return null;
        }
    }

    updateDashboardUI(data) {
        console.log('대시보드 UI 업데이트:', data);
        
        // 1. KPI 업데이트
        const completedEl = document.getElementById('completed-count');
        const pendingEl = document.getElementById('pending-count');
        
        if (data.total_resolved !== undefined) {
            // Empty state 제거하고 실제 값 표시
            const emptyState = completedEl.querySelector('.kpi-empty-state');
            if (emptyState) {
                emptyState.remove();
            }
            completedEl.innerHTML = `${data.total_resolved.toLocaleString()}건`;
            completedEl.style.fontSize = '22px';
            completedEl.style.fontWeight = '700';
        }
        
        if (data.total_unresolved !== undefined) {
            // Empty state 제거하고 실제 값 표시
            const emptyState = pendingEl.querySelector('.kpi-empty-state');
            if (emptyState) {
                emptyState.remove();
            }
            pendingEl.innerHTML = `${data.total_unresolved.toLocaleString()}건`;
            pendingEl.style.fontSize = '22px';
            pendingEl.style.fontWeight = '700';
        }
        
        // 2. TOP 3 카테고리 업데이트
        const topCategoriesTable = document.getElementById('top-categories-table');
        if (data.top_categories && data.top_categories.length > 0) {
            topCategoriesTable.innerHTML = '';
            data.top_categories.slice(0, 3).forEach((item, index) => {
                const row = `<tr><td>${index + 1}위</td><td>${item.category_name}</td><td class="right">${item.count}건</td></tr>`;
                topCategoriesTable.innerHTML += row;
            });
        }
        
        // 3. 카테고리별 비율 차트 업데이트
        if (data.category_distribution && data.category_distribution.length > 0) {
            this.renderCategoryChart(data.category_distribution);
        }
        
        // 4. 인사이트 업데이트 (리포트가 있는 경우)
        if (data.latest_insight) {
            this.renderInsights(data.latest_insight);
        }
    }
    
    renderCategoryChart(categoryData) {
        const container = document.getElementById('category-chart-container');
        const canvas = document.getElementById('category-pie-chart');
        
        // Empty state 텍스트 제거
        const emptyText = container.querySelector('p');
        if (emptyText) {
            emptyText.remove();
        }
        
        // 컨테이너 스타일 초기화
        container.style.display = 'block';
        container.style.alignItems = 'initial';
        container.style.justifyContent = 'initial';
        
        // Canvas 표시
        canvas.style.display = 'block';
        
        const ctx = canvas.getContext('2d');
        const chartData = {
            labels: categoryData.map(item => item.category_name || item.category),
            datasets: [{
                data: categoryData.map(item => item.percentage || item.count),
                backgroundColor: ['#5B8CFF', '#4BC0C0', '#FFCE56', '#FF6384', '#9966FF', '#FF9F40', '#36A2EB'],
                borderWidth: 0
            }]
        };
        
        if (this.categoryPieChart) {
            this.categoryPieChart.destroy();
        }
        
        this.categoryPieChart = new Chart(ctx, {
            type: 'doughnut',  // pie → doughnut으로 변경
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { 
                            color: '#ffffff', 
                            boxWidth: 12, 
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value}건 (${percentage}%)`;
                            }
                        }
                    },
                    datalabels: {
                        display: true,
                        color: '#fff',
                        font: {
                            weight: 'bold',
                            size: 14
                        },
                        formatter: (value, context) => {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return percentage > 5 ? `${percentage}%` : '';  // 5% 이상만 표시
                        }
                    }
                },
                cutout: '50%'  // 도넛 구멍 크기
            }
        });
    }
    
    renderInsights(insight) {
        const container = document.getElementById('generated-insights');
        
        if (!insight || (!insight.overall && (!insight.by_category || insight.by_category.length === 0))) {
            return;
        }
        
        // 컨테이너 스타일 초기화
        container.style.display = 'block';
        container.style.alignItems = 'initial';
        container.style.justifyContent = 'initial';
        container.style.minHeight = 'auto';
        
        let html = '';
        const overall = insight.overall || {};
        const byCategory = insight.by_category || [];
        
        // 종합 인사이트
        if (overall.summary) {
            html += `
                <div style="background: rgba(34, 211, 238, 0.1); padding: 12px; border-radius: 8px; margin-bottom: 16px; border-left: 3px solid #22d3ee;">
                    <p style="color: #fff; font-size: 14px; line-height: 1.6;">${overall.summary}</p>
                </div>
            `;
        }
        
        // 카테고리별 인사이트 (분석 리포트와 동일한 형식)
        if (byCategory.length > 0) {
            html += '<div style="margin-top: 12px;"><strong style="color: #22d3ee;">카테고리별 인사이트:</strong></div>';
            html += '<ul class="subtle" style="margin-top: 8px; font-size: 13px;">';
            
            byCategory.slice(0, 3).forEach(cat => {
                const priorityBadge = cat.priority === 'high' ? '🔴' : cat.priority === 'medium' ? '🟡' : '🟢';
                html += `
                    <li style="margin-bottom: 10px;">
                        <strong>${cat.category_name} ${priorityBadge}</strong>
                        <ul style="margin-left: 15px; font-size: 12px; margin-top: 4px;">
                            ${cat.problem ? `<li><strong>문제점:</strong> ${cat.problem}</li>` : ''}
                            ${cat.short_term_goal ? `<li><strong>단기 목표:</strong> ${cat.short_term_goal}</li>` : ''}
                            ${cat.long_term_goal ? `<li><strong>장기 목표:</strong> ${cat.long_term_goal}</li>` : ''}
                        </ul>
                    </li>
                `;
            });
            
            html += '</ul>';
        }
        
        if (html) {
            container.innerHTML = html;
        }
    }
}

// 페이지 로드 시 DashboardManager 초기화
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.dashboardManager === 'undefined') {
        window.dashboardManager = new DashboardManager();
    }
});