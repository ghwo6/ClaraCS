from flask import Blueprint, request, jsonify
from flasgger.utils import swag_from
from services.upload import UploadService
from services.mapping import MappingService
from utils.logger import get_logger
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
        user_id = request.form.get('user_id', 1)  # 임시로 1로 설정
        
        upload_service = UploadService()
        upload_data = upload_service.upload(file, user_id=int(user_id))
        
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
