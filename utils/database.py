import mysql.connector
from mysql.connector import pooling
from utils.logger import get_logger
import os
from dotenv import load_dotenv

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
        """Connection Pool 생성"""
        try:
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="clara_cs_pool",
                pool_size=5,  # 동시 연결 수
                pool_reset_session=True,
                **self.config
            )
            logger.info("데이터베이스 Connection Pool 생성 완료")
        except mysql.connector.Error as e:
            logger.error(f"Connection Pool 생성 실패: {e}")
            raise
    
    def get_connection(self):
        """Connection Pool에서 연결 가져오기"""
        try:
            connection = self.connection_pool.get_connection()
            if connection.is_connected():
                return connection
            else:
                logger.warning("연결이 끊어져 있습니다. 재연결 시도...")
                connection.reconnect()
                return connection
        except mysql.connector.Error as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            raise
    
    def close_all_connections(self):
        """모든 연결 종료 (애플리케이션 종료 시 호출)"""
        try:
            if self.connection_pool:
                logger.info("모든 데이터베이스 연결 종료")
        except Exception as e:
            logger.error(f"연결 종료 중 오류 발생: {e}")
    
    def test_connection(self):
        """데이터베이스 연결 테스트"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if result:
                logger.info("데이터베이스 연결 테스트 성공")
                return True
            return False
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {e}")
            return False

# 싱글톤 인스턴스
db_manager = DatabaseManager()
