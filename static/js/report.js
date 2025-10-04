/**
 * 분석 리포트 기능 JavaScript (실제 스키마 기반)
 */

class ReportManager {
    constructor() {
        this.currentFileId = 1; // 기본 파일 ID (실제로는 선택된 파일 ID 사용)
        this.currentUserId = 1; // 기본 사용자 ID
        this.isGenerating = false;
        this.chartInstances = {};
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadReportSection();
    }
    
    bindEvents() {
        // 리포트 생성 버튼 이벤트
        const generateBtn = document.querySelector('#btn-generate-report');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => this.generateReport());
        }
        
        // 템플릿 선택 버튼 이벤트
        const templateBtn = document.querySelector('#btn-template-select');
        if (templateBtn) {
            templateBtn.addEventListener('click', () => this.showTemplateSelector());
        }
    }
    
    async generateReport() {
        if (this.isGenerating) {
            this.showMessage('리포트 생성 중입니다. 잠시만 기다려주세요.', 'warning');
            return;
        }
        
        this.isGenerating = true;
        this.showLoading(true);
        
        try {
            console.log('리포트 생성 시작...');
            
            // 1. 리포트 생성 API 호출 (file_id 기반)
            const reportData = await this.callGenerateReportAPI();
            
            // 2. 각 섹션별 데이터 렌더링
            await this.renderChannelTrends(reportData.channel_trends);
            await this.renderSummary(reportData.summary);
            await this.renderInsights(reportData.insights);
            await this.renderSolutions(reportData.solutions);
            
            this.showMessage(`리포트가 성공적으로 생성되었습니다. (Report ID: ${reportData.report_id})`, 'success');
            
        } catch (error) {
            console.error('리포트 생성 실패:', error);
            this.showMessage('리포트 생성 중 오류가 발생했습니다.', 'error');
        } finally {
            this.isGenerating = false;
            this.showLoading(false);
        }
    }
    
    async callGenerateReportAPI() {
        const response = await fetch('/api/report/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                file_id: this.currentFileId,  // user_id 대신 file_id 사용
                user_id: this.currentUserId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || '리포트 생성 실패');
        }
        
        return result.data;
    }
    
    async renderChannelTrends(channelTrends) {
        console.log('채널별 추이 렌더링 시작...');
        
        const container = document.querySelector('#report .card:first-child .chart-box');
        if (!container) return;
        
        // 기존 차트 제거
        container.innerHTML = '';
        
        // 채널 데이터가 없는 경우
        if (!channelTrends || Object.keys(channelTrends).length === 0) {
            container.innerHTML = '<p style="text-align:center; color: var(--muted);">채널별 데이터가 없습니다.</p>';
            return;
        }
        
        // 각 채널별로 차트 생성
        for (const [channel, data] of Object.entries(channelTrends)) {
            const chartContainer = document.createElement('div');
            chartContainer.className = 'chart-container';
            chartContainer.innerHTML = `
                <h4>${channel}</h4>
                <div class="chart" id="chart-${channel.replace(/\s+/g, '-')}"></div>
            `;
            container.appendChild(chartContainer);
            
            // 차트 데이터 준비
            const chartData = this.prepareChartData(data);
            this.createChannelChart(`chart-${channel.replace(/\s+/g, '-')}`, chartData);
        }
    }
    
    prepareChartData(data) {
        const categories = data.categories;
        const dates = data.dates;
        const values = data.data;
        
        return {
            categories: categories,
            dates: dates,
            series: categories.map((category, index) => ({
                name: category,
                data: values.map(row => row[index] || 0)
            }))
        };
    }
    
    createChannelChart(containerId, data) {
        // 간단한 막대그래프 생성 (Chart.js 없이 CSS로 구현)
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const maxValue = Math.max(...data.series.flatMap(s => s.data), 1);
        const chartHeight = 200;
        
        let chartHTML = '<div class="simple-chart">';
        
        data.dates.forEach((date, dateIndex) => {
            chartHTML += `<div class="chart-group">`;
            chartHTML += `<div class="date-label">${date}</div>`;
            chartHTML += `<div class="bars">`;
            
            data.series.forEach((series, seriesIndex) => {
                const value = series.data[dateIndex] || 0;
                const height = (value / maxValue) * chartHeight;
                const color = this.getCategoryColor(series.name);
                
                chartHTML += `
                    <div class="bar-container">
                        <div class="bar" style="height: ${height}px; background-color: ${color};" 
                             title="${series.name}: ${value}건"></div>
                        <div class="bar-label">${value}</div>
                    </div>
                `;
            });
            
            chartHTML += '</div></div>';
        });
        
        chartHTML += '</div>';
        container.innerHTML = chartHTML;
    }
    
    getCategoryColor(category) {
        const colors = {
            '배송': '#ff6b6b',
            '배송지연': '#ff6b6b',
            '환불': '#4ecdc4',
            '환불문의': '#4ecdc4',
            '품질': '#45b7d1',
            '품질불만': '#45b7d1',
            'AS': '#96ceb4',
            'AS요청': '#96ceb4',
            '기타': '#feca57',
            '기타문의': '#feca57',
            '미분류': '#95a5a6'
        };
        return colors[category] || '#95a5a6';
    }
    
    async renderSummary(summary) {
        console.log('데이터 요약 렌더링 시작...');
        
        const container = document.querySelector('#report .card:nth-child(2) .subtle');
        if (!container) return;
        
        const channelList = Object.entries(summary.channels || {})
            .map(([channel, count]) => `${channel} (${count}건)`)
            .join(', ') || 'N/A';
        
        container.innerHTML = `
            <li>총 티켓 수: <b>${summary.total_tickets.toLocaleString()}건</b></li>
            <li>분류 정확도: <b>${(summary.classification_accuracy * 100).toFixed(1)}%</b></li>
            <li>주요 채널: <b>${channelList}</b></li>
            <li>상태별 분포: <b>${JSON.stringify(summary.status_distribution || {})}</b></li>
        `;
    }
    
    async renderInsights(insights) {
        console.log('인사이트 렌더링 시작...');
        
        const container = document.querySelector('#report .card:nth-child(3) .subtle');
        if (!container) return;
        
        let insightsHTML = '';
        
        if (insights.insights && insights.insights.length > 0) {
            insights.insights.forEach(insight => {
                insightsHTML += `
                    <li>
                        <strong>${insight.title}</strong><br/>
                        ${insight.description}
                        <span class="priority-badge ${insight.priority}">${insight.priority}</span>
                    </li>
                `;
            });
        } else {
            insightsHTML = '<li>AI 인사이트 분석 중...</li>';
        }
        
        container.innerHTML = insightsHTML;
    }
    
    async renderSolutions(solutions) {
        console.log('솔루션 렌더링 시작...');
        
        const container = document.querySelector('#report .card:last-child .subtle');
        if (!container) return;
        
        let solutionsHTML = '';
        
        if (solutions.solutions && solutions.solutions.length > 0) {
            solutions.solutions.forEach(solution => {
                solutionsHTML += `
                    <li>
                        <strong>${solution.name}</strong><br/>
                        ${solution.description}<br/>
                        <span style="color: var(--muted); font-size: 12px;">
                            예상 효과: ${solution.expected_impact} | 
                            난이도: <span class="difficulty-badge ${solution.difficulty}">${solution.difficulty}</span>
                        </span>
                    </li>
                `;
            });
        } else {
            solutionsHTML = '<li>솔루션 분석 중...</li>';
        }
        
        container.innerHTML = solutionsHTML;
    }
    
    showTemplateSelector() {
        this.showMessage('템플릿 선택 기능은 준비 중입니다.', 'info');
    }
    
    showLoading(show) {
        const reportSection = document.querySelector('#report');
        if (!reportSection) return;
        
        if (show) {
            reportSection.classList.add('loading');
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading-indicator';
            loadingDiv.innerHTML = '<div class="spinner"></div><p>리포트 생성 중...</p>';
            reportSection.appendChild(loadingDiv);
        } else {
            reportSection.classList.remove('loading');
            const loadingDiv = reportSection.querySelector('.loading-indicator');
            if (loadingDiv) {
                loadingDiv.remove();
            }
        }
    }
    
    showMessage(message, type = 'info') {
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
    
    loadReportSection() {
        // 리포트 섹션이 로드될 때 초기화
        const reportSection = document.querySelector('#report');
        if (reportSection) {
            console.log('리포트 섹션 로드됨 (file_id 기반)');
        }
    }
}

// 페이지 로드 시 ReportManager 초기화
document.addEventListener('DOMContentLoaded', function() {
    if (typeof window.reportManager === 'undefined') {
        window.reportManager = new ReportManager();
    }
});

// 페이지 로드 시 자동으로 섹션 표시
document.addEventListener('DOMContentLoaded', function() {
    const reportSection = document.querySelector('#report');
    if (reportSection) {
        console.log('리포트 페이지가 로드되었습니다.');
    }
});
