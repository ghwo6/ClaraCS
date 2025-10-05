from flask import Blueprint, request, jsonify
from services.mapping import MappingService
from utils.logger import get_logger

logger = get_logger(__name__)

mapping_bp = Blueprint("mapping", __name__)

@mapping_bp.route("/api/mapping/codes", methods=["GET"])
def get_mapping_codes():
    """컬럼 매핑 코드 조회 API"""
    try:
        mapping_service = MappingService()
        codes = mapping_service.get_all_mapping_codes()
        
        return jsonify({
            'success': True,
            'data': codes
        }), 200
        
    except Exception as e:
        logger.error(f"매핑 코드 조회 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'매핑 코드 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500


@mapping_bp.route("/api/mapping/save", methods=["POST"])
def save_mapping():
    """컬럼 매핑 저장 API"""
    try:
        data = request.get_json()
        mappings = data.get('mappings', [])
        file_id = data.get('file_id', None)
        
        if not mappings:
            return jsonify({
                'status': 'error',
                'msg': '저장할 매핑 데이터가 없습니다.'
            }), 400
        
        mapping_service = MappingService()
        result = mapping_service.save_mappings(mappings, file_id)
        
        return jsonify({
            'status': 'success',
            'msg': '컬럼 매핑이 저장되었습니다.',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"매핑 저장 실패: {e}")
        return jsonify({
            'status': 'error',
            'msg': f'매핑 저장 중 오류가 발생했습니다: {str(e)}'
        }), 500


@mapping_bp.route("/api/mapping/last", methods=["GET"])
def get_last_mapping():
    """마지막 컬럼 매핑 조회 API"""
    try:
        file_id = request.args.get('file_id', None)
        
        mapping_service = MappingService()
        mappings = mapping_service.get_last_mappings(file_id)
        
        return jsonify({
            'success': True,
            'mappings': mappings
        }), 200
        
    except Exception as e:
        logger.error(f"마지막 매핑 조회 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'마지막 매핑 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500


@mapping_bp.route("/api/mapping/by-file/<int:file_id>", methods=["GET"])
def get_mapping_by_file(file_id):
    """특정 파일의 컬럼 매핑 조회 API"""
    try:
        mapping_service = MappingService()
        mappings = mapping_service.get_mappings_by_file(file_id)
        
        return jsonify({
            'success': True,
            'data': mappings
        }), 200
        
    except Exception as e:
        logger.error(f"파일별 매핑 조회 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'매핑 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500
