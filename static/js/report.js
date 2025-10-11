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
            console.log('GPT 기반 리포트 생성 시작...');
            
            // 1. 리포트 생성 API 호출 (최신 파일 자동 선택)
            const reportData = await this.callGenerateReportAPI();
            
            // 2. 각 섹션별 데이터 렌더링
            this.renderSummary(reportData.summary);
            this.renderInsights(reportData.insight, reportData.overall_insight);
            this.renderSolutions(reportData.solution);
            
            this.showMessage(`AI 리포트가 성공적으로 생성되었습니다. (Report ID: ${reportData.report_id})`, 'success');
            
        } catch (error) {
            console.error('리포트 생성 실패:', error);
            this.showMessage(error.message || '리포트 생성 중 오류가 발생했습니다.', 'error');
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
                user_id: this.currentUserId  // file_id는 자동 선택
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || '리포트 생성 실패');
        }
        
        return result.data;
    }
    
    
    renderSummary(summary) {
        console.log('데이터 요약 렌더링 시작...', summary);
        
        // 차트 카드는 숨기기
        const chartCard = document.querySelector('#report .card:first-child');
        if (chartCard) {
            chartCard.style.display = 'none';
        }
        
        // 데이터 요약 컨테이너
        const container = document.querySelector('#report .card:nth-child(2) .subtle');
        if (!container) return;
        
        const totalCount = summary.total_cs_count || 0;
        const categoryRatio = summary.category_ratio || {};
        const resolutionRate = summary.resolution_rate || {};
        
        // 카테고리별 비율 리스트
        const categoryList = Object.entries(categoryRatio)
            .map(([cat, ratio]) => `<li><b>${cat}</b>: ${ratio}</li>`)
            .join('');
        
        // 채널별 해결률 리스트
        const resolutionList = Object.entries(resolutionRate)
            .map(([channel, rate]) => `<li><b>${channel}</b>: ${rate}</li>`)
            .join('');
        
        container.innerHTML = `
            <li><strong>전체 CS 건수:</strong> <b>${totalCount.toLocaleString()}건</b></li>
            <li><strong>카테고리별:</strong>
                <ul style="margin-left: 20px; margin-top: 5px;">
                    ${categoryList || '<li>데이터 없음</li>'}
                </ul>
            </li>
            <li><strong>해결률:</strong>
                <ul style="margin-left: 20px; margin-top: 5px;">
                    ${resolutionList || '<li>데이터 없음</li>'}
                </ul>
            </li>
        `;
    }
    
    renderInsights(insight, overallInsight) {
        console.log('인사이트 렌더링 시작...', insight, overallInsight);
        
        const container = document.querySelector('#report .card:nth-child(3) .subtle');
        if (!container) return;
        
        let insightsHTML = '';
        
        // 카테고리별 인사이트
        if (insight && Object.keys(insight).length > 0) {
            insightsHTML += '<li><strong>카테고리별 인사이트:</strong><ul style="margin-left: 20px; margin-top: 5px;">';
            
            Object.entries(insight).forEach(([category, data]) => {
                insightsHTML += `
                    <li>
                        <strong>${category}</strong>
                        <ul style="margin-left: 15px; font-size: 14px;">
                            <li>문제점: ${data.issue || '-'}</li>
                            <li>단기: ${data.short_term || '-'}</li>
                            <li>장기: ${data.long_term || '-'}</li>
                        </ul>
                    </li>
                `;
            });
            
            insightsHTML += '</ul></li>';
        }
        
        // 종합 인사이트
        if (overallInsight) {
            insightsHTML += '<li><strong>종합적 인사이트:</strong><ul style="margin-left: 20px; margin-top: 5px;">';
            
            if (overallInsight.short_term) {
                insightsHTML += `<li><strong>단기:</strong> ${overallInsight.short_term}</li>`;
            }
            if (overallInsight.long_term) {
                insightsHTML += `<li><strong>장기:</strong> ${overallInsight.long_term}</li>`;
            }
            if (overallInsight.notable) {
                insightsHTML += `<li><strong>특이사항:</strong> ${overallInsight.notable}</li>`;
            }
            
            insightsHTML += '</ul></li>';
        }
        
        if (!insightsHTML) {
            insightsHTML = '<li>AI 인사이트 분석 중...</li>';
        }
        
        container.innerHTML = insightsHTML;
    }
    
    renderSolutions(solution) {
        console.log('솔루션 렌더링 시작...', solution);
        
        const container = document.querySelector('#report .card:last-child .subtle');
        if (!container) return;
        
        let solutionsHTML = '';
        
        // 단기 솔루션
        if (solution.short_term && solution.short_term.length > 0) {
            solutionsHTML += '<li><strong>단기 (1~6개월):</strong><ul style="margin-left: 20px; margin-top: 5px;">';
            
            solution.short_term.forEach((item, index) => {
                solutionsHTML += `
                    <li>
                        <strong>${item.suggestion}</strong><br/>
                        <span style="color: #666; font-size: 13px;">→ ${item.expected_effect}</span>
                    </li>
                `;
            });
            
            solutionsHTML += '</ul></li>';
        }
        
        // 장기 솔루션
        if (solution.long_term && solution.long_term.length > 0) {
            solutionsHTML += '<li><strong>장기 (6개월~2년):</strong><ul style="margin-left: 20px; margin-top: 5px;">';
            
            solution.long_term.forEach((item, index) => {
                solutionsHTML += `
                    <li>
                        <strong>${item.suggestion}</strong><br/>
                        <span style="color: #666; font-size: 13px;">→ ${item.expected_effect}</span>
                    </li>
                `;
            });
            
            solutionsHTML += '</ul></li>';
        }
        
        if (!solutionsHTML) {
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
