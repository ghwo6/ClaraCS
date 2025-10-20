from utils.database import db_manager
from utils.logger import get_logger
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = get_logger(__name__)

class UploadDB:
    """업로드 관련 데이터베이스 작업 클래스"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    # ========================================
    # 배치 관련 메서드
    # ========================================
    
    def create_batch(self, user_id: int, batch_name: str = None) -> int:
        """파일 배치 생성
        
        Args:
            user_id: 사용자 ID
            batch_name: 배치 이름 (선택)
            
        Returns:
            int: 생성된 batch_id
        """
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_file_batch 
                (user_id, batch_name, status, created_at)
                VALUES (%s, %s, 'uploading', %s)
            """
            
            cursor.execute(query, (user_id, batch_name, datetime.now()))
            connection.commit()
            
            batch_id = cursor.lastrowid
            logger.info(f"파일 배치 생성 완료: batch_id={batch_id}")
            return batch_id
            
        except Exception as e:
            connection.rollback()
            logger.error(f"파일 배치 생성 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def update_batch_file_count(self, batch_id: int, file_count: int, total_row_count: int):
        """배치의 파일 수 및 행 수 업데이트
        
        Args:
            batch_id: 배치 ID
            file_count: 파일 수
            total_row_count: 전체 행 수
        """
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                UPDATE tb_file_batch
                SET file_count = %s, total_row_count = %s
                WHERE batch_id = %s
            """
            
            cursor.execute(query, (file_count, total_row_count, batch_id))
            connection.commit()
            
            logger.info(f"배치 파일 수 업데이트: batch_id={batch_id}, files={file_count}, rows={total_row_count}")
            
        except Exception as e:
            connection.rollback()
            logger.error(f"배치 업데이트 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def complete_batch(self, batch_id: int):
        """배치 완료 처리
        
        Args:
            batch_id: 배치 ID
        """
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                UPDATE tb_file_batch
                SET status = 'completed', completed_at = %s
                WHERE batch_id = %s
            """
            
            cursor.execute(query, (datetime.now(), batch_id))
            connection.commit()
            
            logger.info(f"배치 완료 처리: batch_id={batch_id}")
            
        except Exception as e:
            connection.rollback()
            logger.error(f"배치 완료 처리 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def get_batch_info(self, batch_id: int) -> Optional[Dict[str, Any]]:
        """배치 정보 조회
        
        Args:
            batch_id: 배치 ID
            
        Returns:
            Dict: 배치 정보
        """
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT 
                    batch_id, user_id, batch_name, file_count, 
                    total_row_count, status, created_at, completed_at
                FROM tb_file_batch
                WHERE batch_id = %s
            """
            
            cursor.execute(query, (batch_id,))
            result = cursor.fetchone()
            
            if result:
                logger.info(f"배치 정보 조회 완료: batch_id={batch_id}")
            return result
            
        except Exception as e:
            logger.error(f"배치 정보 조회 실패: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def get_files_by_batch(self, batch_id: int) -> List[Dict[str, Any]]:
        """배치에 속한 파일 목록 조회
        
        Args:
            batch_id: 배치 ID
            
        Returns:
            List[Dict]: 파일 목록
        """
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT 
                    file_id, user_id, original_filename, storage_path,
                    row_count, status, created_at, processed_at
                FROM tb_uploaded_file
                WHERE batch_id = %s
                ORDER BY created_at ASC
            """
            
            cursor.execute(query, (batch_id,))
            results = cursor.fetchall()
            
            logger.info(f"배치의 파일 {len(results)}개 조회 완료: batch_id={batch_id}")
            return results
            
        except Exception as e:
            logger.error(f"배치 파일 목록 조회 실패: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    
    # ========================================
    # 기존 메서드 (파일 관련)
    # ========================================
    
    def get_extension_code_id(self, extension_name: str) -> Optional[int]:
        """파일 확장자 코드 ID 조회"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT extension_code_id
                FROM tb_uploaded_file_extension_code
                WHERE extension_name = %s
            """
            cursor.execute(query, (extension_name,))
            result = cursor.fetchone()
            
            return result['extension_code_id'] if result else None
            
        except Exception as e:
            logger.error(f"확장자 코드 ID 조회 실패: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def insert_file(self, file_data: Dict[str, Any]) -> int:
        """파일 정보 저장 (배치 지원)"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_uploaded_file 
                (user_id, original_filename, storage_path, extension_code_id, 
                 row_count, status, is_deleted, created_at, batch_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                file_data.get('user_id'),
                file_data.get('original_filename'),
                file_data.get('storage_path'),
                file_data.get('extension_code_id'),
                file_data.get('row_count'),
                file_data.get('status', 'uploaded'),
                False,  # is_deleted
                datetime.now(),
                file_data.get('batch_id')  # 배치 ID (선택)
            ))
            
            connection.commit()
            file_id = cursor.lastrowid
            
            batch_info = f", batch_id={file_data.get('batch_id')}" if file_data.get('batch_id') else ""
            logger.info(f"파일 정보 저장 완료: file_id={file_id}{batch_info}")
            return file_id
            
        except Exception as e:
            connection.rollback()
            logger.error(f"파일 정보 저장 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def update_file_status(self, file_id: int, status: str):
        """파일 상태 업데이트"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                UPDATE tb_uploaded_file
                SET status = %s, processed_at = %s
                WHERE file_id = %s
            """
            
            cursor.execute(query, (status, datetime.now(), file_id))
            connection.commit()
            
            logger.info(f"파일 상태 업데이트 완료: file_id={file_id}, status={status}")
            
        except Exception as e:
            connection.rollback()
            logger.error(f"파일 상태 업데이트 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def insert_tickets(self, tickets: List[Dict[str, Any]]) -> int:
        """티켓 데이터 일괄 저장"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_ticket 
                (file_id, user_id, received_at, channel, customer_id, 
                 product_code, inquiry_type, title, body, assignee, status, raw_data, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            inserted_count = 0
            for ticket in tickets:
                cursor.execute(query, (
                    ticket.get('file_id'),
                    ticket.get('user_id'),
                    ticket.get('received_at'),
                    ticket.get('channel'),
                    ticket.get('customer_id'),
                    ticket.get('product_code'),
                    ticket.get('inquiry_type'),
                    ticket.get('title'),
                    ticket.get('body'),
                    ticket.get('assignee'),
                    ticket.get('status', 'new'),
                    ticket.get('raw_data'),
                    datetime.now()
                ))
                inserted_count += 1
            
            connection.commit()
            logger.info(f"티켓 데이터 {inserted_count}건 저장 완료")
            
            return inserted_count
            
        except Exception as e:
            connection.rollback()
            logger.error(f"티켓 데이터 저장 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def get_tickets_by_file(self, file_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """파일 ID로 티켓 데이터 조회"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT 
                    t.ticket_id, t.file_id, t.user_id, t.received_at, t.channel,
                    t.customer_id, t.product_code, t.inquiry_type, t.title, t.body,
                    t.status, t.created_at, t.updated_at
                FROM tb_ticket t
                WHERE t.file_id = %s
            """
            params = [file_id]
            
            if start_date:
                query += " AND t.received_at >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND t.received_at <= %s"
                params.append(end_date)
            
            query += " ORDER BY t.received_at DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            df = pd.DataFrame(results)
            logger.info(f"티켓 데이터 {len(df)}건 조회 완료")
            return df
            
        except Exception as e:
            logger.error(f"티켓 데이터 조회 실패: {e}")
            return pd.DataFrame()
        finally:
            cursor.close()
            connection.close()