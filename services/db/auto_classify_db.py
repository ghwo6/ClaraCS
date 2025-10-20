from utils.database import db_manager
from utils.logger import get_logger
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = get_logger(__name__)

class AutoClassifyDB:
    """자동분류 관련 데이터베이스 작업 클래스"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    def get_tickets_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        """파일 ID로 티켓 조회"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT 
                    ticket_id, file_id, user_id, received_at, channel,
                    customer_id, product_code, inquiry_type, title, body,
                    assignee, status, created_at
                FROM tb_ticket
                WHERE file_id = %s
                ORDER BY received_at DESC
            """
            
            cursor.execute(query, (file_id,))
            tickets = cursor.fetchall()
            
            logger.info(f"티켓 조회 완료: file_id={file_id}, {len(tickets)}건")
            return tickets
            
        except Exception as e:
            logger.error(f"티켓 조회 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def get_tickets_by_batch(self, batch_id: int) -> List[Dict[str, Any]]:
        """배치 ID로 티켓 조회 (배치에 속한 모든 파일의 티켓)"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT 
                    t.ticket_id, t.file_id, t.user_id, t.received_at, t.channel,
                    t.customer_id, t.product_code, t.inquiry_type, t.title, t.body,
                    t.assignee, t.status, t.created_at
                FROM tb_ticket t
                INNER JOIN tb_uploaded_file f ON f.file_id = t.file_id
                WHERE f.batch_id = %s
                ORDER BY t.received_at DESC
            """
            
            cursor.execute(query, (batch_id,))
            tickets = cursor.fetchall()
            
            logger.info(f"배치 티켓 조회 완료: batch_id={batch_id}, {len(tickets)}건")
            return tickets
            
        except Exception as e:
            logger.error(f"배치 티켓 조회 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def get_latest_batch_id(self, user_id: int) -> Optional[int]:
        """사용자의 최신 배치 ID 조회"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT batch_id
                FROM tb_file_batch
                WHERE user_id = %s
                  AND status = 'completed'
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if result:
                logger.info(f"최신 배치 조회: batch_id={result['batch_id']}")
                return result['batch_id']
            return None
            
        except Exception as e:
            logger.error(f"최신 배치 조회 실패: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def get_latest_file_id(self, user_id: int) -> Optional[int]:
        """사용자의 최신 파일 ID 조회 (배치에 속하지 않은 파일만)"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT file_id
                FROM tb_uploaded_file
                WHERE user_id = %s
                  AND status = 'processed'
                  AND batch_id IS NULL
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if result:
                logger.info(f"최신 파일 조회: file_id={result['file_id']}")
                return result['file_id']
            return None
            
        except Exception as e:
            logger.error(f"최신 파일 조회 실패: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def get_category_mapping(self) -> Dict[int, str]:
        """카테고리 ID -> 이름 매핑 조회 (parent만)"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT category_id, category_name
                FROM tb_category
                WHERE parent_category_id IS NULL
            """
            
            cursor.execute(query)
            categories = cursor.fetchall()
            
            mapping = {cat['category_id']: cat['category_name'] for cat in categories}
            logger.info(f"카테고리 매핑 조회 완료: {len(mapping)}개")
            return mapping
            
        except Exception as e:
            logger.error(f"카테고리 매핑 조회 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def insert_classification_result(self, result_data: Dict[str, Any]) -> int:
        """분류 결과 메타 정보 저장 (tb_classification_result) - 배치 지원"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_classification_result
                (file_id, batch_id, user_id, engine_name, total_tickets, 
                 period_from, period_to, classified_at, needs_review)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                result_data.get('file_id'),
                result_data.get('batch_id'),  # 배치 ID 추가
                result_data.get('user_id'),
                result_data.get('engine_name'),
                result_data.get('total_tickets'),
                result_data.get('period_from'),
                result_data.get('period_to'),
                result_data.get('classified_at', datetime.now()),
                result_data.get('needs_review', False)
            ))
            
            connection.commit()
            class_result_id = cursor.lastrowid
            
            batch_info = f", batch_id={result_data.get('batch_id')}" if result_data.get('batch_id') else ""
            logger.info(f"분류 결과 저장 완료: class_result_id={class_result_id}{batch_info}")
            return class_result_id
            
        except Exception as e:
            connection.rollback()
            logger.error(f"분류 결과 저장 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def update_ticket_classification(self, ticket_id: int, classification: Dict[str, Any]):
        """티켓에 분류 결과 업데이트"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                UPDATE tb_ticket
                SET classified_category_id = %s,
                    classification_confidence = %s,
                    classification_keywords = %s,
                    classified_at = %s
                WHERE ticket_id = %s
            """
            
            cursor.execute(query, (
                classification.get('category_id'),
                classification.get('confidence'),
                json.dumps(classification.get('keywords', []), ensure_ascii=False),
                datetime.now(),
                ticket_id
            ))
            
            connection.commit()
            
        except Exception as e:
            connection.rollback()
            logger.error(f"티켓 분류 업데이트 실패: ticket_id={ticket_id}, {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def insert_category_results(self, class_result_id: int, category_results: List[Dict[str, Any]]):
        """카테고리별 집계 저장 (tb_classification_category_result)"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_classification_category_result
                (class_result_id, category_id, count, ratio, example_keywords)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            for result in category_results:
                cursor.execute(query, (
                    class_result_id,
                    result.get('category_id'),
                    result.get('count'),
                    result.get('ratio'),
                    json.dumps(result.get('keywords', []), ensure_ascii=False)
                ))
            
            connection.commit()
            logger.info(f"카테고리 집계 저장 완료: {len(category_results)}건")
            
        except Exception as e:
            connection.rollback()
            logger.error(f"카테고리 집계 저장 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def insert_channel_results(self, class_result_id: int, channel_results: List[Dict[str, Any]]):
        """채널별 집계 저장 (tb_classification_channel_result)"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_classification_channel_result
                (class_result_id, channel, category_id, count, ratio)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            for result in channel_results:
                cursor.execute(query, (
                    class_result_id,
                    result.get('channel'),
                    result.get('category_id'),
                    result.get('count'),
                    result.get('ratio')
                ))
            
            connection.commit()
            logger.info(f"채널 집계 저장 완료: {len(channel_results)}건")
            
        except Exception as e:
            connection.rollback()
            logger.error(f"채널 집계 저장 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def insert_reliability_result(self, class_result_id: int, reliability: Dict[str, Any]):
        """신뢰도 정보 저장 (tb_classification_reliability_result)"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            # accuracy, macro_f1, micro_f1 등 개별 메트릭 저장
            metrics = [
                ('accuracy', reliability.get('accuracy', 0.0)),
                ('macro_f1', reliability.get('macro_f1', 0.0)),
                ('micro_f1', reliability.get('micro_f1', 0.0))
            ]
            
            query = """
                INSERT INTO tb_classification_reliability_result
                (class_result_id, metric_name, metric_value, details)
                VALUES (%s, %s, %s, %s)
            """
            
            for metric_name, metric_value in metrics:
                cursor.execute(query, (
                    class_result_id,
                    metric_name,
                    metric_value,
                    json.dumps(reliability, ensure_ascii=False)
                ))
            
            connection.commit()
            logger.info(f"신뢰도 정보 저장 완료")
            
        except Exception as e:
            connection.rollback()
            logger.error(f"신뢰도 정보 저장 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def get_latest_classification(self, file_id: int) -> Optional[Dict[str, Any]]:
        """파일의 최신 분류 결과 조회"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT *
                FROM tb_classification_result
                WHERE file_id = %s
                ORDER BY classified_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (file_id,))
            result = cursor.fetchone()
            
            return result
            
        except Exception as e:
            logger.error(f"최신 분류 결과 조회 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def get_latest_file_id(self, user_id: int) -> Optional[int]:
        """사용자의 최신 파일 ID 조회"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT file_id
                FROM tb_uploaded_file
                WHERE user_id = %s
                  AND status = 'processed'
                  AND (is_deleted IS NULL OR is_deleted = FALSE)
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            if result:
                logger.info(f"최신 파일 ID 조회 완료: user_id={user_id}, file_id={result['file_id']}")
                return result['file_id']
            else:
                logger.warning(f"처리된 파일이 없습니다: user_id={user_id}")
                return None
            
        except Exception as e:
            logger.error(f"최신 파일 ID 조회 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
