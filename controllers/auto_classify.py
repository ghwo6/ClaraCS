from flask import Blueprint, jsonify, request, current_app
from pathlib import Path
import json
from services.auto_classify import AutoClassifyService
from utils.logger import get_logger

logger = get_logger(__name__)

auto_bp = Blueprint("auto_classify", __name__, url_prefix="/api/classifications")

@auto_bp.route("/run", methods=["POST"])
def run():
    """
    요청: { "user_id": int, "file_id": int }
    응답: auto_class_result.json 내용 (meta에 user/file echo)
    """
    try:
        body = request.get_json(silent=True) or {}
        user_id = int(body.get("user_id", 0))
        file_id = int(body.get("file_id", 0))

        logger.info(f"자동분류 실행 요청: user_id={user_id}, file_id={file_id}")
        
        auto_classify_service = AutoClassifyService()
        result = auto_classify_service.run_classification(user_id, file_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"자동분류 실행 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'자동분류 실행 중 오류가 발생했습니다: {str(e)}'
        }), 500
