from flask import Blueprint, request, jsonify, session
from flasgger.utils import swag_from
from services.upload import UploadService
from services.mapping import MappingService
from services.db.report_db import ReportDB
from utils.logger import get_logger
from config import Config
import json

logger = get_logger(__name__)

upload_bp = Blueprint("upload", __name__)

@upload_bp.route("/api/upload", methods=["POST"])
def upload_file():
    """데이터 업로드 API"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400
        
        file = request.files['file']  # 업로드된 파일 객체
        
        # user_id 우선순위: 폼 데이터 > 세션 > 환경변수 기본값
        user_id = request.form.get('user_id') or session.get('user_id') or Config.DEFAULT_USER_ID
        user_id = int(user_id)
        
        upload_service = UploadService()
        upload_data = upload_service.upload(file, user_id=user_id)
        
        return jsonify({
            'success': True,
            'message': '파일 업로드 및 처리가 완료되었습니다.',
            'data': upload_data
        }), 200
        
    except ValueError as ve:
        logger.warning(f"데이터 업로드 검증 실패: {ve}")
        return jsonify({
            'success': False,
            'error': str(ve)
        }), 400
    except Exception as e:
        logger.error(f"데이터 업로드 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'데이터 업로드 중 오류가 발생했습니다: {str(e)}'
        }), 500


@upload_bp.route("/api/upload/validate", methods=["POST"])
def validate_file():
    """파일 유효성 검사 API"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '파일이 없습니다.'}), 400
        
        file = request.files['file']
        
        upload_service = UploadService()
        mapping_service = MappingService()
        
        # 컬럼 매핑 정보 가져오기
        mapping_dict = mapping_service.get_active_mappings_dict()
        
        if not mapping_dict:
            return jsonify({
                'success': False,
                'data': {
                    'is_valid': False,
                    'errors': [{'type': 'no_mapping', 'message': '컬럼 매핑이 설정되지 않았습니다.'}]
                }
            }), 200
        
        # 유효성 검사 수행
        validation_result = upload_service.validate_file(file, mapping_dict)
        
        return jsonify({
            'success': True,
            'data': validation_result
        }), 200
        
    except ValueError as ve:
        logger.warning(f"파일 검증 실패: {ve}")
        return jsonify({
            'success': False,
            'data': {
                'is_valid': False,
                'errors': [{'type': 'validation_error', 'message': str(ve)}]
            }
        }), 200
    except Exception as e:
        logger.error(f"파일 검증 중 오류: {e}")
        return jsonify({
            'success': False,
            'error': f'파일 검증 중 오류가 발생했습니다: {str(e)}'
        }), 500

@upload_bp.route("/api/upload/latest-file", methods=["POST"])
@swag_from({
    'tags': ['Upload'],
    'description': '최신 업로드 파일 조회',
    'responses': {
        200: {
            'description': '최신 파일 조회 성공'
        }
    }
})
def get_latest_file():
    """최신 업로드 파일 조회 API"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id') or session.get('user_id') or Config.DEFAULT_USER_ID
        
        logger.info(f"최신 파일 조회: user_id={user_id}")
        
        report_db = ReportDB()
        file_id = report_db.get_latest_file_id(user_id)
        
        if not file_id:
            return jsonify({
                'success': False,
                'error': '업로드된 파일이 없습니다.'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'file_id': file_id
            }
        }), 200
        
    except Exception as e:
        logger.error(f"최신 파일 조회 실패: {e}")
        return jsonify({
            'success': False,
            'error': '파일 조회 중 오류가 발생했습니다.'
        }), 500
