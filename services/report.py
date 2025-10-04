from utils.dummydata.report_dummy import data_repository
from services.db.report_db import ReportDB
from utils.ai_service import ai_service
from utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class ReportService:
    """리포트 관련 비즈니스 로직 서비스"""
    
    def __init__(self):
        # TODO: 더미데이터 사용 중 - 실제 DB 서비스로 변경하려면 아래 주석 해제하고 위 줄 주석 처리
        self.data_repository = data_repository  # 더미데이터 사용
        # self.report_db = ReportDB()  # 실제 DB 사용
        
        self.ai_service = ai_service
    
    def generate_report(self, user_id: str, start_date: str = None, end_date: str = None) -> dict:
        """분석 리포트 생성"""
        logger.info(f"사용자 {user_id}의 리포트 생성 시작")
        
        # 1. 채널별 추이 데이터 생성
        logger.info("채널별 추이 데이터 생성 중...")
        channel_trends = self.data_repository.get_channel_trend_data(user_id)
        
        # 2. 데이터 요약 생성
        logger.info("데이터 요약 생성 중...")
        summary = self.data_repository.get_summary_data(user_id)
        
        # 3. AI 분석용 데이터 준비
        logger.info("AI 분석 데이터 준비 중...")
        ai_analysis_data = self.data_repository.get_ai_analysis_data(user_id)
        
        # 4. AI 인사이트 분석
        logger.info("AI 인사이트 분석 중...")
        insights = self.ai_service.analyze_cs_insights(ai_analysis_data)
        
        # 5. 솔루션 제안 생성
        logger.info("솔루션 제안 생성 중...")
        solutions = self.ai_service.generate_solution_recommendations(insights)
        
        # 6. 응답 데이터 구성
        report_data = {
            'channel_trends': channel_trends,
            'summary': summary,
            'insights': insights,
            'solutions': solutions,
            'generated_at': self.data_repository._get_current_timestamp()
        }
        
        logger.info(f"사용자 {user_id}의 리포트 생성 완료")
        return report_data
    
    def get_channel_trends(self, user_id: str) -> dict:
        """채널별 추이 데이터 조회"""
        logger.info(f"사용자 {user_id}의 채널별 추이 데이터 조회")
        
        channel_trends = self.data_repository.get_channel_trend_data(user_id)
        return channel_trends
    
    def get_summary(self, user_id: str) -> dict:
        """데이터 요약 조회"""
        logger.info(f"사용자 {user_id}의 데이터 요약 조회")
        
        summary = self.data_repository.get_summary_data(user_id)
        return summary
    
    def get_insights(self, user_id: str) -> dict:
        """AI 인사이트 분석"""
        logger.info(f"사용자 {user_id}의 AI 인사이트 분석")
        
        # AI 분석용 데이터 준비
        ai_analysis_data = self.data_repository.get_ai_analysis_data(user_id)
        
        # AI 인사이트 분석
        insights = self.ai_service.analyze_cs_insights(ai_analysis_data)
        return insights
    
    def get_solutions(self, user_id: str, insights: dict = None) -> dict:
        """솔루션 제안 생성"""
        logger.info(f"사용자 {user_id}의 솔루션 제안 생성")
        
        # 인사이트가 제공되지 않은 경우 새로 생성
        if not insights:
            ai_analysis_data = self.data_repository.get_ai_analysis_data(user_id)
            insights = self.ai_service.analyze_cs_insights(ai_analysis_data)
        
        # 솔루션 제안 생성
        solutions = self.ai_service.generate_solution_recommendations(insights)
        return solutions
