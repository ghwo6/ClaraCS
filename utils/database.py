import mysql.connector
from mysql.connector import pooling
from utils.logger import get_logger
import os
from dotenv import load_dotenv
import time
from functools import wraps
from contextlib import contextmanager

# .env 파일 로드
load_dotenv()

logger = get_logger(__name__)

class DatabaseManager:
    """MySQL 데이터베이스 연결 및 관리 클래스 (Connection Pool 사용)"""
    
    def __init__(self):
        self.connection_pool = None
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'clara_cs'),
            'charset': 'utf8mb4',
            'auth_plugin': 'mysql_native_password'
        }
        self._create_connection_pool()
    
    def _create_connection_pool(self):
        """Connection Pool 생성 (크기 증가 + 타임아웃 설정)"""
        try:
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="clara_cs_pool",
                pool_size=20,  # 5 → 20으로 증가 (동시 작업 대응)
                pool_reset_session=True,  # 세션 재설정 활성화
                **self.config
            )
            logger.info("데이터베이스 Connection Pool 생성 완료 (pool_size=20)")
        except mysql.connector.Error as e:
            logger.error(f"Connection Pool 생성 실패: {e}")
            raise
    
    def get_connection(self, max_retries=3, retry_delay=1):
        """Connection Pool에서 연결 가져오기 (재시도 로직 추가)
        
        Args:
            max_retries: 최대 재시도 횟수
            retry_delay: 재시도 간격(초)
        
        Returns:
            MySQL connection 객체
        
        Raises:
            Exception: 재시도 후에도 실패 시
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                connection = self.connection_pool.get_connection()
                
                # 연결 상태 확인
                if connection.is_connected():
                    logger.debug(f"DB 연결 성공 (attempt {attempt + 1}/{max_retries})")
                    return connection
                else:
                    logger.warning(f"연결이 끊어져 있습니다. 재연결 시도 {attempt + 1}/{max_retries}...")
                    connection.reconnect(attempts=3, delay=1)
                    return connection
                    
            except mysql.connector.errors.PoolError as e:
                last_error = e
                logger.warning(f"Connection Pool 고갈 (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"{retry_delay}초 후 재시도...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 지수 백오프 (1초 → 2초 → 4초)
                else:
                    logger.error(f"Connection Pool 고갈: 최대 재시도 횟수 초과")
                    
            except mysql.connector.Error as e:
                last_error = e
                logger.error(f"데이터베이스 연결 실패 (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error(f"데이터베이스 연결 실패: 최대 재시도 횟수 초과")
        
        # 모든 재시도 실패
        raise Exception(f"데이터베이스 연결 실패 ({max_retries}회 재시도): {last_error}")
    
    @contextmanager
    def get_connection_context(self):
        """Context Manager를 사용한 안전한 연결 관리
        
        사용 예시:
            with db_manager.get_connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
                # connection은 자동으로 반환됨
        """
        connection = None
        try:
            connection = self.get_connection()
            yield connection
        except Exception as e:
            if connection:
                try:
                    connection.rollback()
                    logger.warning("트랜잭션 롤백 완료")
                except:
                    pass
            raise
        finally:
            if connection and connection.is_connected():
                try:
                    connection.close()
                    logger.debug("DB 연결 반환 완료")
                except Exception as e:
                    logger.error(f"연결 반환 중 오류: {e}")
    
    def close_all_connections(self):
        """모든 연결 종료 (애플리케이션 종료 시 호출)"""
        try:
            if self.connection_pool:
                logger.info("모든 데이터베이스 연결 종료")
        except Exception as e:
            logger.error(f"연결 종료 중 오류 발생: {e}")
    
    def test_connection(self):
        """데이터베이스 연결 테스트"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result:
                logger.info("데이터베이스 연결 테스트 성공")
                return True
            return False
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

def db_retry_decorator(max_retries=3, retry_delay=1):
    """데이터베이스 작업 재시도 데코레이터
    
    사용 예시:
        @db_retry_decorator(max_retries=3)
        def insert_data(self, data):
            connection = self.db_manager.get_connection()
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            delay = retry_delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (mysql.connector.errors.PoolError, 
                        mysql.connector.errors.OperationalError,
                        mysql.connector.errors.DatabaseError) as e:
                    last_error = e
                    logger.warning(f"{func.__name__} 실패 (attempt {attempt + 1}/{max_retries}): {e}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"{delay}초 후 재시도...")
                        time.sleep(delay)
                        delay *= 2  # 지수 백오프
                    else:
                        logger.error(f"{func.__name__} 최대 재시도 횟수 초과")
            
            raise Exception(f"{func.__name__} 실패 ({max_retries}회 재시도): {last_error}")
        
        return wrapper
    return decorator

# 싱글톤 인스턴스
db_manager = DatabaseManager()
