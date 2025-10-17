from flask import Blueprint, jsonify
from flasgger.utils import swag_from
from utils.logger import get_logger

logger = get_logger(__name__)

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
@swag_from({
    'tags': ['Dashboard'],
    'description': '대시보드 데이터 조회',
    'responses': {
        200: {
            'description': '대시보드 데이터 조회 성공'
        }
    }
})
def get_dashboard_data():
    """대시보드 데이터 조회 API"""
    try:
        logger.info("대시보드 데이터 조회 시작")
        
        # TODO: 실제 DB에서 데이터 가져오기
        # 현재는 더미 데이터 사용
        
        # 1. KPI 데이터
        kpi_data = {
            'completed': 133,
            'pending': 13
        }

        # 2. TOP 3 카테고리 데이터
        top_categories_data = [
            {'rank': 1, 'category': '결제', 'count': 11},
            {'rank': 2, 'category': '배송', 'count': 7},
            {'rank': 3, 'category': '환불', 'count': 1}
        ]

        # 3. 카테고리별 분포 (파이 차트용)
        category_distribution_data = [
            {'category': '제품 하자', 'percentage': 40},
            {'category': '네트워크 불량', 'percentage': 35},
            {'category': '배송 문제', 'percentage': 25}
        ]
        
        # 4. AI 인사이트
        generated_insights_html = """
            <h4>1. 제품 하자 (40%)</h4>
            <ul>
                <li>음성, 상담 의존도가 높으므로 전문 대응이 필요합니다.</li>
                <li><b>단기:</b> 제품별 FAQ, 영상 가이드 제공</li>
                <li><b>장기:</b> 하자 데이터를 R&D 부서에 피드백하여 불량률 개선</li>
            </ul>
            <h4>종합적 인사이트</h4>
            <ul>
                <li><b>단기:</b> 게시판 자동 분류, 챗봇 고도화, 음성 콜백 도입을 통해 대응 효율을 높일 수 있습니다.</li>
                <li><b>장기:</b> CS 데이터를 제품, IT, 물류 부서와 실시간으로 공유하는 피드백 체계를 구축해야 합니다.</li>
            </ul>
        """

        # 최종 응답 데이터 구성
        response_data = {
            'kpi': kpi_data,
            'top_categories': top_categories_data,
            'category_distribution': category_distribution_data,
            'insights': generated_insights_html
        }

        logger.info("대시보드 데이터 조회 완료")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"대시보드 데이터 조회 실패: {e}")
        return jsonify({
            'error': '대시보드 데이터 조회 중 오류가 발생했습니다.'
        }), 500

