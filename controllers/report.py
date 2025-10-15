from flask import Blueprint, request, jsonify, session
from flasgger.utils import swag_from
from services.report import ReportService
from utils.logger import get_logger
from config import Config
import json

logger = get_logger(__name__)

report_bp = Blueprint("report", __name__)

@report_bp.route("/api/report/generate", methods=["POST"])
@swag_from({
    'tags': ['Report'],
    'description': '분석 리포트 생성 (최신 업로드 파일 기준)',
    'parameters': [
        {
            'name': 'user_id',
            'in': 'body',
            'type': 'integer',
            'required': False,
            'description': '사용자 ID (기본값 1)'
        },
        {
            'name': 'file_id',
            'in': 'body',
            'type': 'integer',
            'required': False,
            'description': '파일 ID (선택사항, 없으면 최신 파일 사용)'
        }
    ],
    'responses': {
        200: {
            'description': '리포트 생성 성공',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'report_id': {'type': 'integer'},
                            'file_id': {'type': 'integer'},
                            'summary': {'type': 'object'},
                            'insight': {'type': 'object'},
                            'overall_insight': {'type': 'object'},
                            'solution': {'type': 'object'}
                        }
                    }
                }
            }
        },
        400: {
            'description': '잘못된 요청'
        },
        500: {
            'description': '서버 오류'
        }
    }
})
def generate_report():
    """분석 리포트 생성 API - 최신 파일 기준, GPT 기반 통합 분석"""
    try:
        logger.info("리포트 생성 요청 시작")
        
        # 요청 데이터 파싱
        data = request.get_json() or {}
        
        # user_id 우선순위: 요청 데이터 > 세션 > 환경변수 기본값
        user_id = data.get('user_id') or session.get('user_id') or Config.DEFAULT_USER_ID
        file_id = data.get('file_id')  # 선택사항
        
        logger.info(f"리포트 생성 요청: user_id={user_id}, file_id={file_id}")
        
        # 서비스를 통한 리포트 생성
        report_service = ReportService()
        report_data = report_service.generate_report(user_id, file_id)
        
        logger.info(f"리포트 생성 완료 (report_id: {report_data['report_id']})")
        
        return jsonify({
            'success': True,
            'data': report_data
        }), 200
        
    except ValueError as ve:
        logger.warning(f"리포트 생성 실패 (유효성 검증): {ve}")
        return jsonify({
            'success': False,
            'error': str(ve)
        }), 400
    except Exception as e:
        logger.error(f"리포트 생성 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'리포트 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500

@report_bp.route("/api/report/channel-trends", methods=["POST"])
@swag_from({
    'tags': ['Report'],
    'description': '채널별 추이 데이터 조회',
    'parameters': [
        {
            'name': 'file_id',
            'in': 'body',
            'type': 'integer',
            'required': True,
            'description': '파일 ID'
        }
    ],
    'responses': {
        200: {
            'description': '채널별 추이 데이터 조회 성공'
        }
    }
})
def get_channel_trends():
    """채널별 추이 데이터 조회 API"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        
        if not file_id:
            return jsonify({
                'success': False,
                'error': 'file_id가 필요합니다.'
            }), 400
        
        logger.info(f"파일 {file_id}의 채널별 추이 데이터 조회")
        
        report_service = ReportService()
        channel_trends = report_service.get_channel_trends(file_id)
        
        return jsonify({
            'success': True,
            'data': channel_trends
        }), 200
        
    except Exception as e:
        logger.error(f"채널별 추이 데이터 조회 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'데이터 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@report_bp.route("/api/report/summary", methods=["POST"])
@swag_from({
    'tags': ['Report'],
    'description': '데이터 요약 조회',
    'parameters': [
        {
            'name': 'file_id',
            'in': 'body',
            'type': 'integer',
            'required': True,
            'description': '파일 ID'
        }
    ],
    'responses': {
        200: {
            'description': '데이터 요약 조회 성공'
        }
    }
})
def get_summary():
    """데이터 요약 조회 API"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        
        if not file_id:
            return jsonify({
                'success': False,
                'error': 'file_id가 필요합니다.'
            }), 400
        
        logger.info(f"파일 {file_id}의 데이터 요약 조회")
        
        report_service = ReportService()
        summary = report_service.get_summary(file_id)
        
        return jsonify({
            'success': True,
            'data': summary
        }), 200
        
    except Exception as e:
        logger.error(f"데이터 요약 조회 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'데이터 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@report_bp.route("/api/report/insights", methods=["POST"])
@swag_from({
    'tags': ['Report'],
    'description': 'AI 인사이트 분석',
    'parameters': [
        {
            'name': 'file_id',
            'in': 'body',
            'type': 'integer',
            'required': True,
            'description': '파일 ID'
        }
    ],
    'responses': {
        200: {
            'description': 'AI 인사이트 분석 성공'
        }
    }
})
def get_insights():
    """AI 인사이트 분석 API"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        
        if not file_id:
            return jsonify({
                'success': False,
                'error': 'file_id가 필요합니다.'
            }), 400
        
        logger.info(f"파일 {file_id}의 AI 인사이트 분석")
        
        report_service = ReportService()
        insights = report_service.get_insights(file_id)
        
        return jsonify({
            'success': True,
            'data': insights
        }), 200
        
    except Exception as e:
        logger.error(f"AI 인사이트 분석 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'AI 분석 중 오류가 발생했습니다: {str(e)}'
        }), 500

@report_bp.route("/api/report/solutions", methods=["POST"])
@swag_from({
    'tags': ['Report'],
    'description': '솔루션 제안 생성',
    'parameters': [
        {
            'name': 'file_id',
            'in': 'body',
            'type': 'integer',
            'required': True,
            'description': '파일 ID'
        },
        {
            'name': 'insights',
            'in': 'body',
            'type': 'object',
            'required': False,
            'description': '인사이트 데이터 (선택사항)'
        }
    ],
    'responses': {
        200: {
            'description': '솔루션 제안 생성 성공'
        }
    }
})
def get_solutions():
    """솔루션 제안 생성 API"""
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        insights = data.get('insights')
        
        if not file_id:
            return jsonify({
                'success': False,
                'error': 'file_id가 필요합니다.'
            }), 400
        
        logger.info(f"파일 {file_id}의 솔루션 제안 생성")
        
        report_service = ReportService()
        solutions = report_service.get_solutions(file_id, insights)
        
        return jsonify({
            'success': True,
            'data': solutions
        }), 200
        
    except Exception as e:
        logger.error(f"솔루션 제안 생성 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'솔루션 생성 중 오류가 발생했습니다: {str(e)}'
        }), 500
