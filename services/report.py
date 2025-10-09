from services.db.report_db import ReportDB
from utils.ai_service import ai_service
from utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class ReportService:
    """리포트 관련 비즈니스 로직 서비스
    
    Note: 
        - 실제 DB 스키마 기반으로 동작
        - file_id 기반으로 리포트 생성
        - 생성된 리포트는 스냅샷으로 저장
    """
    
    def __init__(self):
        self.report_db = ReportDB()
        self.ai_service = ai_service
    
    def generate_report(self, file_id: int, user_id: int = 1, start_date: str = None, end_date: str = None) -> dict:
        """분석 리포트 생성
        
        Args:
            file_id: 파일 ID (필수)
            user_id: 사용자 ID (기본값 1)
            start_date: 시작 날짜 (선택사항)
            end_date: 종료 날짜 (선택사항)
        
        Returns:
            dict: 리포트 데이터 + report_id
        """
        logger.info(f"파일 {file_id}의 리포트 생성 시작 (user_id: {user_id})")
        
        try:
            # 1. 리포트 레코드 생성
            report_title = f"분석 리포트_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            report_id = self.report_db.create_report(file_id, user_id, 'full_analysis', report_title)
            
            if not report_id:
                raise Exception("리포트 레코드 생성 실패")
            
            # 2. 채널별 추이 데이터 생성
            logger.info("채널별 추이 데이터 생성 중...")
            channel_trends = self.report_db.get_channel_trend_data(file_id)
            
            # 3. 데이터 요약 생성
            logger.info("데이터 요약 생성 중...")
            summary = self.report_db.get_summary_data(file_id)
            
            # 4. AI 분석용 데이터 준비
            logger.info("AI 분석 데이터 준비 중...")
            ai_analysis_data = self.report_db.get_ai_analysis_data(file_id)
            
            # 5. AI 인사이트 분석
            logger.info("AI 인사이트 분석 중...")
            insights = self.ai_service.analyze_cs_insights(ai_analysis_data)
            
            # 6. 솔루션 제안 생성
            logger.info("솔루션 제안 생성 중...")
            solutions = self.ai_service.generate_solution_recommendations(insights)
            
            # 7. 스냅샷 저장
            logger.info("스냅샷 저장 중...")
            self._save_snapshots(report_id, channel_trends, summary, insights, solutions)
            
            # 8. 리포트 완료 처리
            self.report_db.complete_report(report_id)
            
            # 9. 응답 데이터 구성
            report_data = {
                'report_id': report_id,
                'file_id': file_id,
                'channel_trends': channel_trends,
                'summary': summary,
                'insights': insights,
                'solutions': solutions,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"파일 {file_id}의 리포트 생성 완료 (report_id: {report_id})")
            return report_data
            
        except Exception as e:
            logger.error(f"리포트 생성 실패: {e}")
            raise
    
    def _save_snapshots(self, report_id: int, channel_trends: dict, summary: dict, 
                       insights: dict, solutions: dict):
        """생성된 리포트 데이터를 스냅샷으로 저장"""
        try:
            # 요약 스냅샷 저장
            summary_snapshot = {
                'total_tickets': summary.get('total_tickets', 0),
                'resolved_count': summary.get('status_distribution', {}),
                'category_ratios': {},  # 카테고리 비율 계산 필요
                'repeat_rate': 0.0  # 반복 문의율 계산 필요
            }
            self.report_db.save_summary_snapshot(report_id, summary_snapshot)
            
            # 인사이트 스냅샷 저장
            self.report_db.save_insight_snapshot(report_id, insights)
            
            # 솔루션 스냅샷 저장
            self.report_db.save_solution_snapshot(report_id, solutions)
            
            logger.info(f"리포트 {report_id}의 스냅샷 저장 완료")
            
        except Exception as e:
            logger.error(f"스냅샷 저장 실패: {e}")
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
