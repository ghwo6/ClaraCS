import mysql.connector
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """MySQL 데이터베이스 연결 및 관리 클래스"""
    
    def __init__(self):
        self.connection = None
        self.config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'password',
            'database': 'clara_cs',
            'charset': 'utf8mb4'
        }
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info("데이터베이스 연결 성공")
            return True
        except mysql.connector.Error as e:
            logger.error(f"데이터베이스 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("데이터베이스 연결 해제")
    
    def get_connection(self):
        """연결된 데이터베이스 커넥션 반환"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection

# 싱글톤 인스턴스
db_manager = DatabaseManager()
