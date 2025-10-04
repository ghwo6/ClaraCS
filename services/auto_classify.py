from flask import current_app
from pathlib import Path
import json
from utils.logger import get_logger

logger = get_logger(__name__)

class AutoClassifyService:
    """자동분류 관련 비즈니스 로직 서비스"""
    
    def __init__(self):
        pass
    
    def run_classification(self, user_id: int, file_id: int) -> dict:
        """자동분류 실행"""
        logger.info(f"자동분류 실행: user_id={user_id}, file_id={file_id}")
        
        # 앱 루트 기준으로 더미 JSON 로드
        payload_path = Path(current_app.root_path) / "utils" / "dummydata" / "2_after_classify" / "auto_class_result.json"
        data = json.loads(payload_path.read_text(encoding="utf-8"))

        data.setdefault("meta", {})["user_id"] = user_id
        data["meta"]["file_id"] = file_id
        
        logger.info(f"자동분류 완료: user_id={user_id}, file_id={file_id}")
        return data
