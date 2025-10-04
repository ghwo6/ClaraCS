import pandas as pd
import json
from datetime import datetime, timedelta
import random
from typing import Dict, List, Any
from utils.logger import get_logger

logger = get_logger(__name__)

class DummyDataGenerator:
    """더미 데이터 생성 클래스"""
    
    def __init__(self):
        self.channels = ['카카오톡 접수', '1대1 접수', '전화 접수']
        self.categories = ['배송지연', '상품상태', '환불문의', 'AS요청', '기타문의']
        self.statuses = ['신규', '진행중', '완료', '보류']
        self.priorities = ['상', '중', '하']
    
    def generate_cs_tickets(self, user_id: str, days: int = 30) -> List[Dict]:
        """CS 티켓 더미 데이터 생성"""
        tickets = []
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(1000):  # 1000건의 티켓 생성
            ticket_date = start_date + timedelta(days=random.randint(0, days))
            
            ticket = {
                'ticket_id': f'TK{str(i+1).zfill(6)}',
                'user_id': user_id,
                'created_at': ticket_date.strftime('%Y-%m-%d %H:%M:%S'),
                'channel': random.choice(self.channels),
                'customer_id': f'CUST{str(random.randint(1000, 9999))}',
                'title': f'문의 제목 {i+1}',
                'content': f'문의 내용입니다. 상세한 내용은 {i+1}번 티켓과 관련된 내용입니다.',
                'status': random.choice(self.statuses),
                'priority': random.choice(self.priorities),
                'assigned_to': f'Agent{random.randint(1, 10)}',
                'category': random.choice(self.categories),
                'resolution_time': random.randint(1, 72) if random.choice(self.statuses) == '완료' else None
            }
            tickets.append(ticket)
        
        logger.info(f"CS 티켓 더미 데이터 {len(tickets)}건 생성 완료")
        return tickets
    
    def generate_classified_data(self, user_id: str, days: int = 30) -> List[Dict]:
        """자동분류된 데이터 더미 생성"""
        classified_data = []
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(1000):
            classified_date = start_date + timedelta(days=random.randint(0, days))
            
            data = {
                'classification_id': f'CLS{str(i+1).zfill(6)}',
                'user_id': user_id,
                'ticket_id': f'TK{str(i+1).zfill(6)}',
                'classified_at': classified_date.strftime('%Y-%m-%d %H:%M:%S'),
                'predicted_category': random.choice(self.categories),
                'confidence_score': round(random.uniform(0.7, 0.95), 3),
                'keywords': self._generate_keywords(),
                'sentiment': random.choice(['긍정', '중립', '부정']),
                'urgency_level': random.choice(['긴급', '보통', '낮음'])
            }
            classified_data.append(data)
        
        logger.info(f"자동분류 데이터 {len(classified_data)}건 생성 완료")
        return classified_data
    
    def _generate_keywords(self) -> str:
        """키워드 생성"""
        keyword_pools = {
            '배송지연': ['배송', '지연', '택배', '물류'],
            '상품상태': ['품질', '하자', '파손', '불량'],
            '환불문의': ['환불', '취소', '결제', '금액'],
            'AS요청': ['AS', '수리', '교체', '설치'],
            '기타문의': ['문의', '확인', '안내', '정보']
        }
        
        category = random.choice(self.categories)
        keywords = random.sample(keyword_pools.get(category, ['기타']), random.randint(2, 4))
        return ', '.join(keywords)

class DataRepository:
    """데이터 조회 및 처리 클래스"""
    
    def __init__(self):
        self.dummy_generator = DummyDataGenerator()
    
    def get_cs_tickets_by_user(self, user_id: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """사용자별 CS 티켓 데이터 조회"""
        logger.info(f"사용자 {user_id}의 CS 티켓 데이터 조회 시작")
        
        # 실제 DB 연동 시 사용할 코드 (현재는 더미 데이터)
        # tickets = self._query_tickets_from_db(user_id, start_date, end_date)
        
        # 더미 데이터 생성
        tickets = self.dummy_generator.generate_cs_tickets(user_id)
        
        df = pd.DataFrame(tickets)
        logger.info(f"CS 티켓 데이터 {len(df)}건 조회 완료")
        return df
    
    def get_classified_data_by_user(self, user_id: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """사용자별 자동분류 데이터 조회"""
        logger.info(f"사용자 {user_id}의 자동분류 데이터 조회 시작")
        
        # 실제 DB 연동 시 사용할 코드
        # classified_data = self._query_classified_data_from_db(user_id, start_date, end_date)
        
        # 더미 데이터 생성
        classified_data = self.dummy_generator.generate_classified_data(user_id)
        
        df = pd.DataFrame(classified_data)
        logger.info(f"자동분류 데이터 {len(df)}건 조회 완료")
        return df
    
    def get_channel_trend_data(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """채널별 추이 데이터 생성"""
        logger.info(f"사용자 {user_id}의 채널별 추이 데이터 생성 시작")
        
        cs_data = self.get_cs_tickets_by_user(user_id)
        classified_data = self.get_classified_data_by_user(user_id)
        
        # 날짜별 채널별 카테고리별 집계
        trend_data = {}
        channels = cs_data['channel'].unique()
        
        for channel in channels:
            channel_data = cs_data[cs_data['channel'] == channel]
            channel_data['created_at'] = pd.to_datetime(channel_data['created_at'])
            channel_data['date'] = channel_data['created_at'].dt.date
            
            # 날짜별 카테고리별 집계
            daily_counts = channel_data.groupby(['date', 'category']).size().unstack(fill_value=0)
            
            trend_data[channel] = {
                'dates': [str(date) for date in daily_counts.index],
                'categories': daily_counts.columns.tolist(),
                'data': daily_counts.values.tolist()
            }
        
        logger.info(f"채널별 추이 데이터 생성 완료: {len(trend_data)}개 채널")
        return trend_data
    
    def get_summary_data(self, user_id: str) -> Dict[str, Any]:
        """데이터 요약 정보 생성"""
        logger.info(f"사용자 {user_id}의 요약 데이터 생성 시작")
        
        cs_data = self.get_cs_tickets_by_user(user_id)
        classified_data = self.get_classified_data_by_user(user_id)
        
        summary = {
            'total_tickets': len(cs_data),
            'channels': cs_data['channel'].value_counts().to_dict(),
            'categories': cs_data['category'].value_counts().to_dict(),
            'status_distribution': cs_data['status'].value_counts().to_dict(),
            'priority_distribution': cs_data['priority'].value_counts().to_dict(),
            'avg_resolution_time': cs_data['resolution_time'].mean() if 'resolution_time' in cs_data.columns else None,
            'classification_accuracy': classified_data['confidence_score'].mean(),
            'sentiment_distribution': classified_data['sentiment'].value_counts().to_dict()
        }
        
        logger.info(f"요약 데이터 생성 완료")
        return summary
    
    def get_ai_analysis_data(self, user_id: str) -> Dict[str, Any]:
        """AI 분석용 데이터 준비"""
        logger.info(f"사용자 {user_id}의 AI 분석 데이터 준비 시작")
        
        cs_data = self.get_cs_tickets_by_user(user_id)
        classified_data = self.get_classified_data_by_user(user_id)
        
        # AI 분석을 위한 데이터 구조화
        analysis_data = {
            'ticket_summaries': cs_data[['title', 'content', 'category', 'status']].to_dict('records'),
            'classification_insights': classified_data[['predicted_category', 'confidence_score', 'keywords', 'sentiment']].to_dict('records'),
            'trend_analysis': self._analyze_trends(cs_data),
            'issue_patterns': self._identify_issue_patterns(cs_data, classified_data)
        }
        
        logger.info(f"AI 분석 데이터 준비 완료")
        return analysis_data
    
    def _analyze_trends(self, cs_data: pd.DataFrame) -> Dict[str, Any]:
        """트렌드 분석"""
        cs_data['created_at'] = pd.to_datetime(cs_data['created_at'])
        cs_data['date'] = cs_data['created_at'].dt.date
        
        # 일별 트렌드
        daily_trends = cs_data.groupby('date').size()
        
        # 카테고리별 트렌드
        category_trends = cs_data.groupby(['date', 'category']).size().unstack(fill_value=0)
        
        return {
            'daily_counts': daily_trends.to_dict(),
            'category_trends': category_trends.to_dict()
        }
    
    def _identify_issue_patterns(self, cs_data: pd.DataFrame, classified_data: pd.DataFrame) -> Dict[str, Any]:
        """이슈 패턴 식별"""
        # 고빈도 키워드 추출
        all_keywords = []
        for keywords in classified_data['keywords']:
            all_keywords.extend(keywords.split(', '))
        
        keyword_counts = pd.Series(all_keywords).value_counts()
        
        # 문제가 많은 카테고리 식별
        problem_categories = cs_data['category'].value_counts().head(3)
        
        return {
            'top_keywords': keyword_counts.head(10).to_dict(),
            'problem_categories': problem_categories.to_dict(),
            'sentiment_analysis': classified_data['sentiment'].value_counts().to_dict()
        }
    
    def _get_current_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 싱글톤 인스턴스
data_repository = DataRepository()
