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
        """파일 정보 저장"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_uploaded_file 
                (user_id, original_filename, storage_path, extension_code_id, 
                 row_count, status, is_deleted, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                file_data.get('user_id'),
                file_data.get('original_filename'),
                file_data.get('storage_path'),
                file_data.get('extension_code_id'),
                file_data.get('row_count'),
                file_data.get('status', 'uploaded'),
                False,  # is_deleted
                datetime.now()
            ))
            
            connection.commit()
            file_id = cursor.lastrowid
            
            logger.info(f"파일 정보 저장 완료: file_id={file_id}")
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
                 product_code, inquiry_type, title, body, status, raw_data, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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