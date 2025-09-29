# routes/auto_classify.py
from flask import Blueprint, jsonify, request, current_app
from pathlib import Path
import json

auto_bp = Blueprint("auto_classify", __name__, url_prefix="/api/classifications")

@auto_bp.route("/run", methods=["POST"])
def run():
    """
    요청: { "user_id": int, "file_id": int }
    응답: auto_class_result.json 내용 (meta에 user/file echo)
    """
    body = request.get_json(silent=True) or {}
    user_id = int(body.get("user_id", 0))
    file_id = int(body.get("file_id", 0))

    # 앱 루트 기준으로 더미 JSON 로드
    payload_path = Path(current_app.root_path) / "utils" / "dummydata" / "2_after_classify" / "auto_class_result.json"
    data = json.loads(payload_path.read_text(encoding="utf-8"))

    data.setdefault("meta", {})["user_id"] = user_id
    data["meta"]["file_id"] = file_id
    return jsonify(data), 200