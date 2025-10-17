from services.db.report_db import ReportDB
from utils.ai_service import ai_service
from utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class ReportService:
    """리포트 관련 비즈니스 로직 서비스
    
    Note: 
        - 최신 업로드 파일 자동 선택
        - GPT 기반 통합 분석 (데이터 요약, 인사이트, 솔루션)
        - 생성된 리포트는 스냅샷으로 저장
    """
    
    def __init__(self):
        self.report_db = ReportDB()
        self.ai_service = ai_service
    
    def generate_report(self, user_id: int = 1, file_id: int = None) -> dict:
        """분석 리포트 생성 - GPT 기반 통합 분석
        
        Args:
            user_id: 사용자 ID (기본값 1)
            file_id: 파일 ID (선택사항, None이면 최신 파일 사용)
        
        Returns:
            dict: 리포트 데이터 (summary, insight, overall_insight, solution)
        """
        logger.info(f"리포트 생성 시작 (user_id: {user_id}, file_id: {file_id})")
        
        try:
            # 1. file_id가 없으면 최신 파일 선택
            if not file_id:
                file_id = self.report_db.get_latest_file_id(user_id)
                if not file_id:
                    raise ValueError("분석할 데이터가 없습니다. 먼저 파일을 업로드하고 자동 분류를 실행하세요.")
                logger.info(f"최신 파일 자동 선택: file_id={file_id}")
            
            # 2. 리포트 레코드 생성
            report_title = f"AI 분석 리포트_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            report_id = self.report_db.create_report(file_id, user_id, 'ai_analysis', report_title)
            
            if not report_id:
                raise Exception("리포트 레코드 생성 실패")
            
            logger.info(f"리포트 레코드 생성 완료: report_id={report_id}")
            
            # 3. CS 데이터 조회 (분류 결과 기반)
            logger.info("CS 데이터 조회 중...")
            cs_data = self.report_db.get_cs_analysis_data(file_id)
            
            if not cs_data or cs_data['total_tickets'] == 0:
                raise ValueError("분류된 CS 데이터가 없습니다. 먼저 자동 분류를 실행하세요.")
            
            # 4. 채널별 추이 데이터 조회 (그래프용)
            logger.info("채널별 추이 데이터 조회 중...")
            channel_trends = self.report_db.get_channel_trend_data(file_id)
            
            # 5. GPT 기반 통합 분석 (한 번의 호출로 모든 섹션 생성)
            logger.info("GPT 기반 통합 분석 시작...")
            analysis_result = self.ai_service.generate_comprehensive_report(cs_data)
            
            # 6. 스냅샷 저장 (DB에 영구 보관 - 3개 테이블)
            logger.info("분석 결과 스냅샷 저장 중...")
            self._save_analysis_snapshot(report_id, analysis_result, channel_trends)
            
            # 7. 리포트 완료 처리
            self.report_db.complete_report(report_id)
            
            # 8. 응답 데이터 구성
            report_data = {
                'report_id': report_id,
                'file_id': file_id,
                'channel_trends': channel_trends,  # 그래프 데이터 추가
                'summary': analysis_result.get('summary', {}),
                'insight': analysis_result.get('insight', {}),
                'solution': analysis_result.get('solution', {}),
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'is_ai_generated': analysis_result.get('_is_ai_generated', False),  # AI 생성 여부
                'data_source': analysis_result.get('_data_source', 'fallback')  # 데이터 출처
            }
            
            logger.info(f"리포트 생성 완료 (report_id: {report_id}, file_id: {file_id})")
            return report_data
            
        except Exception as e:
            logger.error(f"리포트 생성 실패: {e}")
            raise
    
    def _save_analysis_snapshot(self, report_id: int, analysis_result: dict, channel_trends: dict = None):
        """GPT 분석 결과를 스냅샷으로 저장 (4개 테이블)"""
        try:
            # 1. Summary 스냅샷 저장 (tb_analysis_summary_snapshot)
            summary = analysis_result.get('summary', {})
            
            # 개선된 구조에서 데이터 추출
            categories = summary.get('categories', [])
            channels = summary.get('channels', [])
            
            # category_ratios 변환 (배열 → 딕셔너리)
            category_ratios = {}
            for cat in categories:
                category_ratios[cat.get('category_name', '알수없음')] = cat.get('percentage', 0.0)
            
            # resolved_count 변환 (배열 → 딕셔너리)
            resolved_count = {}
            for ch in channels:
                resolved_count[ch.get('channel', '알수없음')] = ch.get('resolution_rate', 0.0)
            
            summary_snapshot = {
                'total_tickets': summary.get('total_cs_count', 0),
                'resolved_count': resolved_count,
                'category_ratios': category_ratios,
                'repeat_rate': 0.0  # TODO: 반복 문의율 계산
            }
            self.report_db.save_summary_snapshot(report_id, summary_snapshot)
            logger.info(f"요약 스냅샷 저장 완료")
            
            # 2. Insight 스냅샷 저장 (tb_analysis_insight_snapshot)
            insight_snapshot = analysis_result.get('insight', {})
            self.report_db.save_insight_snapshot(report_id, insight_snapshot)
            logger.info(f"인사이트 스냅샷 저장 완료")
            
            # 3. Solution 스냅샷 저장 (tb_analysis_solution_snapshot)
            solution = analysis_result.get('solution', {})
            self.report_db.save_solution_snapshot(report_id, solution)
            logger.info(f"솔루션 스냅샷 저장 완료")
            
            # 4. Channel 스냅샷 저장 (tb_analysis_channel_snapshot)
            if channel_trends and len(channel_trends) > 0:
                saved = self.report_db.save_channel_snapshot(report_id, channel_trends)
                if saved:
                    logger.info(f"채널 스냅샷 저장 완료")
                else:
                    logger.warning(f"채널 스냅샷 저장 실패 (데이터는 있으나 저장 오류)")
            else:
                logger.warning(f"채널 추이 데이터가 없어 스냅샷 저장을 건너뜁니다")
            
            logger.info(f"리포트 {report_id}의 모든 스냅샷 저장 완료")
            
        except Exception as e:
            logger.error(f"스냅샷 저장 실패: {e}", exc_info=True)
            # 스냅샷 저장 실패해도 리포트 생성은 계속 진행
    
    def get_channel_trends(self, file_id: int) -> dict:
        """채널별 추이 데이터 조회"""
        logger.info(f"파일 {file_id}의 채널별 추이 데이터 조회")
        
        channel_trends = self.report_db.get_channel_trend_data(file_id)
        return channel_trends
    
    def get_summary(self, file_id: int) -> dict:
        """데이터 요약 조회"""
        logger.info(f"파일 {file_id}의 데이터 요약 조회")
        
        summary = self.report_db.get_summary_data(file_id)
        return summary
    
    def get_insights(self, file_id: int) -> dict:
        """AI 인사이트 분석"""
        logger.info(f"파일 {file_id}의 AI 인사이트 분석")
        
        # AI 분석용 데이터 준비
        ai_analysis_data = self.report_db.get_ai_analysis_data(file_id)
        
        # AI 인사이트 분석
        insights = self.ai_service.analyze_cs_insights(ai_analysis_data)
        return insights
    
    def get_solutions(self, file_id: int, insights: dict = None) -> dict:
        """솔루션 제안 생성"""
        logger.info(f"파일 {file_id}의 솔루션 제안 생성")
        
        # 인사이트가 제공되지 않은 경우 새로 생성
        if not insights:
            ai_analysis_data = self.report_db.get_ai_analysis_data(file_id)
            insights = self.ai_service.analyze_cs_insights(ai_analysis_data)
        
        # 솔루션 제안 생성
        solutions = self.ai_service.generate_solution_recommendations(insights)
        return solutions
    
    def get_report_by_id(self, report_id: int) -> dict:
        """저장된 리포트 조회 (스냅샷에서)"""
        logger.info(f"리포트 {report_id} 조회")
        
        # TODO: 스냅샷 테이블에서 리포트 데이터 조회
        # tb_analysis_insight_snapshot, tb_analysis_solution_snapshot 등에서 조회
        pass
    
    def get_latest_report(self, user_id: int) -> dict:
        """사용자의 마지막 생성된 리포트 조회"""
        logger.info(f"마지막 리포트 조회: user_id={user_id}")
        
        try:
            # 마지막 리포트 ID 조회
            latest_report_id = self.report_db.get_latest_report_id(user_id)
            
            if not latest_report_id:
                logger.warning(f"사용자 {user_id}의 리포트가 없습니다")
                return None
            
            logger.info(f"마지막 리포트 조회 완료: report_id={latest_report_id}")
            return {
                'report_id': latest_report_id
            }
            
        except Exception as e:
            logger.error(f"마지막 리포트 조회 실패: {e}")
            return None