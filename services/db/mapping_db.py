from utils.database import db_manager
from utils.logger import get_logger
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = get_logger(__name__)

class MappingDB:
    """컬럼 매핑 관련 데이터베이스 작업 클래스"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    def get_all_mapping_codes(self) -> List[Dict[str, Any]]:
        """모든 컬럼 매핑 코드 조회"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT 
                    mapping_code_id,
                    code_name,
                    description
                FROM tb_column_mapping_code
                ORDER BY mapping_code_id
            """
            cursor.execute(query)
            results = cursor.fetchall()
            
            logger.info(f"매핑 코드 {len(results)}개 조회 완료")
            return results
            
        except Exception as e:
            logger.error(f"매핑 코드 조회 실패: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    
    def get_mapping_code_id_by_name(self, code_name: str) -> Optional[int]:
        """코드명으로 매핑 코드 ID 조회"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT mapping_code_id
                FROM tb_column_mapping_code
                WHERE code_name = %s
            """
            cursor.execute(query, (code_name,))
            result = cursor.fetchone()
            
            return result['mapping_code_id'] if result else None
            
        except Exception as e:
            logger.error(f"매핑 코드 ID 조회 실패: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def insert_mappings(self, mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """컬럼 매핑 저장"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_column_mapping 
                (file_id, original_column, mapping_code_id, is_activate, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            # 모든 매핑을 동일한 created_at으로 저장하기 위해 미리 생성
            batch_created_at = datetime.now()
            
            inserted_count = 0
            for mapping in mappings:
                file_id = mapping.get('file_id')
                original_column = mapping.get('original_column')
                mapping_code_id = mapping.get('mapping_code_id')
                is_activate = mapping.get('is_activate', True)
                
                logger.info(f"매핑 저장 중: file_id={file_id}, column={original_column}, code_id={mapping_code_id}")
                
                cursor.execute(query, (
                    file_id,
                    original_column,
                    mapping_code_id,
                    is_activate,
                    batch_created_at  # 동일한 시간 사용
                ))
                inserted_count += 1
            
            connection.commit()
            logger.info(f"컬럼 매핑 {inserted_count}건 저장 완료 (created_at: {batch_created_at})")
            
            return {
                'inserted_count': inserted_count,
                'success': True
            }
            
        except Exception as e:
            connection.rollback()
            logger.error(f"컬럼 매핑 저장 실패: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def get_last_mappings(self, file_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """마지막 컬럼 매핑 조회 (최신 created_at 기준, file_id=NULL인 템플릿만)"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            if file_id:
                # 특정 파일의 매핑 조회
                query = """
                    SELECT 
                        m.mapping_id,
                        m.file_id,
                        m.original_column,
                        m.mapping_code_id,
                        m.is_activate,
                        m.created_at,
                        c.code_name,
                        c.description
                    FROM tb_column_mapping m
                    LEFT JOIN tb_column_mapping_code c 
                        ON m.mapping_code_id = c.mapping_code_id
                    WHERE m.file_id = %s
                    ORDER BY m.created_at DESC, m.mapping_id DESC
                """
                cursor.execute(query, (file_id,))
            else:
                # file_id가 없으면 템플릿(file_id=NULL) 중 가장 최근 매핑 조회
                query = """
                    SELECT 
                        m.mapping_id,
                        m.file_id,
                        m.original_column,
                        m.mapping_code_id,
                        m.is_activate,
                        m.created_at,
                        c.code_name,
                        c.description
                    FROM tb_column_mapping m
                    LEFT JOIN tb_column_mapping_code c 
                        ON m.mapping_code_id = c.mapping_code_id
                    WHERE m.file_id IS NULL
                      AND m.created_at = (
                        SELECT MAX(created_at) 
                        FROM tb_column_mapping
                        WHERE file_id IS NULL
                    )
                    ORDER BY m.mapping_id
                """
                cursor.execute(query)
            
            results = cursor.fetchall()
            
            # datetime을 문자열로 변환
            for result in results:
                if result.get('created_at'):
                    result['created_at'] = result['created_at'].isoformat()
            
            logger.info(f"마지막 컬럼 매핑 {len(results)}건 조회 완료 (file_id: {file_id})")
            return results
            
        except Exception as e:
            logger.error(f"마지막 매핑 조회 실패: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    
    def get_mappings_by_file(self, file_id: int) -> List[Dict[str, Any]]:
        """특정 파일의 컬럼 매핑 조회"""
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT 
                    m.mapping_id,
                    m.file_id,
                    m.original_column,
                    m.mapping_code_id,
                    m.is_activate,
                    m.created_at,
                    c.code_name,
                    c.description
                FROM tb_column_mapping m
                LEFT JOIN tb_column_mapping_code c 
                    ON m.mapping_code_id = c.mapping_code_id
                WHERE m.file_id = %s
                ORDER BY m.created_at DESC, m.mapping_id
            """
            cursor.execute(query, (file_id,))
            results = cursor.fetchall()
            
            # datetime을 문자열로 변환
            for result in results:
                if result.get('created_at'):
                    result['created_at'] = result['created_at'].isoformat()
            
            logger.info(f"파일 ID {file_id}의 컬럼 매핑 {len(results)}건 조회 완료")
            return results
            
        except Exception as e:
            logger.error(f"파일별 매핑 조회 실패: {e}")
            return []
        finally:
            cursor.close()
            connection.close()

