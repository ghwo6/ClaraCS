from utils.database import db_manager
from utils.logger import get_logger
import pandas as pd
from typing import Dict, List, Any, Optional

logger = get_logger(__name__)

class ReportDB:
    """리포트 관련 데이터베이스 작업 클래스"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    def get_cs_tickets_by_user(self, user_id: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """사용자별 CS 티켓 데이터 조회"""
        logger.info(f"사용자 {user_id}의 CS 티켓 데이터 조회 시작")
        
        # TODO: 더미데이터 사용 중 - 아래 코드를 활성화하고 더미데이터 코드를 삭제하세요
        # 더미데이터 코드 시작
        from utils.dummydata.report_dummy import DummyDataGenerator
        dummy_generator = DummyDataGenerator()
        tickets = dummy_generator.generate_cs_tickets(user_id)
        df = pd.DataFrame(tickets)
        logger.info(f"CS 티켓 더미데이터 {len(df)}건 조회 완료")
        return df
        # 더미데이터 코드 끝
        
        # 실제 데이터베이스 쿼리 (주석 해제 후 사용)
        # connection = self.db_manager.get_connection()
        # cursor = connection.cursor(dictionary=True)
        # 
        # try:
        #     query = """
        #         SELECT ticket_id, user_id, created_at, channel, customer_id, 
        #                title, content, status, priority, assigned_to, category, resolution_time
        #         FROM cs_tickets 
        #         WHERE user_id = %s
        #     """
        #     params = [user_id]
        #     
        #     if start_date:
        #         query += " AND created_at >= %s"
        #         params.append(start_date)
        #     
        #     if end_date:
        #         query += " AND created_at <= %s"
        #         params.append(end_date)
        #     
        #     query += " ORDER BY created_at DESC"
        #     
        #     cursor.execute(query, params)
        #     results = cursor.fetchall()
        #     
        #     df = pd.DataFrame(results)
        #     logger.info(f"CS 티켓 데이터 {len(df)}건 조회 완료")
        #     return df
        #     
        # except Exception as e:
        #     logger.error(f"CS 티켓 데이터 조회 실패: {e}")
        #     raise
        # finally:
        #     cursor.close()
    
    def get_classified_data_by_user(self, user_id: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """사용자별 자동분류 데이터 조회"""
        logger.info(f"사용자 {user_id}의 자동분류 데이터 조회 시작")
        
        # TODO: 더미데이터 사용 중 - 아래 코드를 활성화하고 더미데이터 코드를 삭제하세요
        # 더미데이터 코드 시작
        from utils.dummydata.report_dummy import DummyDataGenerator
        dummy_generator = DummyDataGenerator()
        classified_data = dummy_generator.generate_classified_data(user_id)
        df = pd.DataFrame(classified_data)
        logger.info(f"자동분류 더미데이터 {len(df)}건 조회 완료")
        return df
        # 더미데이터 코드 끝
        
        # 실제 데이터베이스 쿼리 (주석 해제 후 사용)
        # connection = self.db_manager.get_connection()
        # cursor = connection.cursor(dictionary=True)
        # 
        # try:
        #     query = """
        #         SELECT classification_id, user_id, ticket_id, classified_at, 
        #                predicted_category, confidence_score, keywords, sentiment, urgency_level
        #         FROM classified_data 
        #         WHERE user_id = %s
        #     """
        #     params = [user_id]
        #     
        #     if start_date:
        #         query += " AND classified_at >= %s"
        #         params.append(start_date)
        #     
        #     if end_date:
        #         query += " AND classified_at <= %s"
        #         params.append(end_date)
        #     
        #     query += " ORDER BY classified_at DESC"
        #     
        #     cursor.execute(query, params)
        #     results = cursor.fetchall()
        #     
        #     df = pd.DataFrame(results)
        #     logger.info(f"자동분류 데이터 {len(df)}건 조회 완료")
        #     return df
        #     
        # except Exception as e:
        #     logger.error(f"자동분류 데이터 조회 실패: {e}")
        #     raise
        # finally:
        #     cursor.close()
    
    def insert_cs_ticket(self, ticket_data: Dict[str, Any]) -> bool:
        """CS 티켓 데이터 삽입"""
        logger.info(f"CS 티켓 데이터 삽입: {ticket_data.get('ticket_id')}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO cs_tickets 
                (ticket_id, user_id, created_at, channel, customer_id, title, content, 
                 status, priority, assigned_to, category, resolution_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                ticket_data.get('ticket_id'),
                ticket_data.get('user_id'),
                ticket_data.get('created_at'),
                ticket_data.get('channel'),
                ticket_data.get('customer_id'),
                ticket_data.get('title'),
                ticket_data.get('content'),
                ticket_data.get('status'),
                ticket_data.get('priority'),
                ticket_data.get('assigned_to'),
                ticket_data.get('category'),
                ticket_data.get('resolution_time')
            )
            
            cursor.execute(query, values)
            connection.commit()
            
            logger.info(f"CS 티켓 데이터 삽입 완료: {ticket_data.get('ticket_id')}")
            return True
            
        except Exception as e:
            logger.error(f"CS 티켓 데이터 삽입 실패: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
    
    def insert_classified_data(self, classified_data: Dict[str, Any]) -> bool:
        """자동분류 데이터 삽입"""
        logger.info(f"자동분류 데이터 삽입: {classified_data.get('classification_id')}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO classified_data 
                (classification_id, user_id, ticket_id, classified_at, predicted_category, 
                 confidence_score, keywords, sentiment, urgency_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                classified_data.get('classification_id'),
                classified_data.get('user_id'),
                classified_data.get('ticket_id'),
                classified_data.get('classified_at'),
                classified_data.get('predicted_category'),
                classified_data.get('confidence_score'),
                classified_data.get('keywords'),
                classified_data.get('sentiment'),
                classified_data.get('urgency_level')
            )
            
            cursor.execute(query, values)
            connection.commit()
            
            logger.info(f"자동분류 데이터 삽입 완료: {classified_data.get('classification_id')}")
            return True
            
        except Exception as e:
            logger.error(f"자동분류 데이터 삽입 실패: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
