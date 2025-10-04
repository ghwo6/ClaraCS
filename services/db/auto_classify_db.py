from utils.database import db_manager
from utils.logger import get_logger
from typing import Dict, List, Any, Optional

logger = get_logger(__name__)

class AutoClassifyDB:
    """자동분류 관련 데이터베이스 작업 클래스"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    def get_classification_results(self, user_id: int, file_id: int) -> Optional[Dict[str, Any]]:
        """분류 결과 조회"""
        logger.info(f"분류 결과 조회: user_id={user_id}, file_id={file_id}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT * FROM classification_results 
                WHERE user_id = %s AND file_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (user_id, file_id))
            result = cursor.fetchone()
            
            if result:
                logger.info(f"분류 결과 조회 완료: user_id={user_id}, file_id={file_id}")
            else:
                logger.info(f"분류 결과 없음: user_id={user_id}, file_id={file_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"분류 결과 조회 실패: {e}")
            raise
        finally:
            cursor.close()
    
    def save_classification_result(self, classification_data: Dict[str, Any]) -> bool:
        """분류 결과 저장"""
        logger.info(f"분류 결과 저장: user_id={classification_data.get('user_id')}, file_id={classification_data.get('file_id')}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO classification_results 
                (user_id, file_id, result_data, status, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            import json
            values = (
                classification_data.get('user_id'),
                classification_data.get('file_id'),
                json.dumps(classification_data.get('result_data', {}), ensure_ascii=False),
                classification_data.get('status', 'completed'),
                classification_data.get('created_at')
            )
            
            cursor.execute(query, values)
            connection.commit()
            
            logger.info(f"분류 결과 저장 완료: user_id={classification_data.get('user_id')}, file_id={classification_data.get('file_id')}")
            return True
            
        except Exception as e:
            logger.error(f"분류 결과 저장 실패: {e}")
            connection.rollback()
            raise
        finally:
            cursor.close()
    
    def get_classification_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """분류 히스토리 조회"""
        logger.info(f"분류 히스토리 조회: user_id={user_id}, limit={limit}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT * FROM classification_results 
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            
            cursor.execute(query, (user_id, limit))
            results = cursor.fetchall()
            
            logger.info(f"분류 히스토리 조회 완료: {len(results)}건")
            return results
            
        except Exception as e:
            logger.error(f"분류 히스토리 조회 실패: {e}")
            raise
        finally:
            cursor.close()
