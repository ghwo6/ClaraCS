from flask import Blueprint, jsonify, request, session, current_app
from pathlib import Path
import json
from services.auto_classify import AutoClassifyService
from services.db.report_db import ReportDB
from utils.logger import get_logger
from config import Config

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
        
        # user_id 우선순위: 요청 데이터 > 세션 > 환경변수 기본값
        user_id = int(body.get("user_id") or session.get('user_id') or Config.DEFAULT_USER_ID)
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

@auto_bp.route("/stats", methods=["POST"])
def get_classification_stats():
    """
    자동 분류 통계 조회 (대시보드용)
    요청: { "file_id": int }
    응답: 처리 완료/미처리 건수, TOP 3 카테고리, 카테고리별 분포
    """
    try:
        body = request.get_json(silent=True) or {}
        file_id = int(body.get("file_id", 0))
        
        if not file_id:
            return jsonify({
                'success': False,
                'error': 'file_id가 필요합니다.'
            }), 400
        
        logger.info(f"분류 통계 조회: file_id={file_id}")
        
        report_db = ReportDB()
        
        # 1. CS 데이터 조회
        cs_data = report_db.get_cs_analysis_data(file_id)
        
        if not cs_data or cs_data['total_tickets'] == 0:
            return jsonify({
                'success': False,
                'error': '분류 데이터가 없습니다.'
            }), 404
        
        # 2. 통계 데이터 구성
        stats_data = {
            'total_tickets': cs_data['total_tickets'],
            'total_resolved': cs_data.get('total_resolved', 0),
            'total_unresolved': cs_data.get('total_unresolved', 0),
            'top_categories': cs_data['category_distribution'][:3],  # TOP 3
            'category_distribution': cs_data['category_distribution']
        }
        
        # 3. 최신 리포트의 인사이트 조회 (있는 경우만)
        try:
            user_id = session.get('user_id') or Config.DEFAULT_USER_ID
            latest_report_id = report_db.get_latest_report_id(user_id)
            
            if latest_report_id:
                report_data = report_db.get_report_with_snapshots(latest_report_id)
                if report_data and report_data.get('insight'):
                    stats_data['latest_insight'] = report_data['insight']
                    logger.info(f"최신 인사이트 포함: report_id={latest_report_id}")
        except Exception as e:
            logger.warning(f"인사이트 조회 실패 (무시): {e}")
        
        logger.info(f"분류 통계 조회 완료: {stats_data['total_tickets']}건")
        
        return jsonify({
            'success': True,
            'data': stats_data
        }), 200
        
    except Exception as e:
        logger.error(f"분류 통계 조회 실패: {e}")
        return jsonify({
            'success': False,
            'error': f'통계 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500
