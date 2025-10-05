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
    요청: { "user_id": int, "file_id": int (선택), "engine": str (선택) }
    응답: 분류 결과 JSON
    
    file_id가 없거나 0이면 최신 파일 자동 선택
    engine: 'rule' (규칙 기반) 또는 'ai' (AI 기반)
    """
    try:
        body = request.get_json(silent=True) or {}
        user_id = int(body.get("user_id", 1))  # 기본값 1
        file_id = int(body.get("file_id", 0))  # 0이면 최신 파일 선택
        engine = body.get("engine", "rule")  # 기본값: 규칙 기반

        # file_id가 없으면 최신 파일 자동 선택
        if not file_id:
            from services.db.auto_classify_db import AutoClassifyDB
            auto_db = AutoClassifyDB()
            file_id = auto_db.get_latest_file_id(user_id)
            
            if not file_id:
                return jsonify({
                    'success': False,
                    'error': '분류할 파일이 없습니다. 먼저 데이터를 업로드하세요.'
                }), 400
            
            logger.info(f"최신 파일 자동 선택: file_id={file_id}")

        logger.info(f"자동분류 실행 요청: user_id={user_id}, file_id={file_id}, engine={engine}")
        
        auto_classify_service = AutoClassifyService()
        result = auto_classify_service.run_classification(user_id, file_id, use_ai=(engine == 'ai'))
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"자동분류 실행 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'자동분류 실행 중 오류가 발생했습니다: {str(e)}'
        }), 500
