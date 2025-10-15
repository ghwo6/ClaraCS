import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """애플리케이션 설정"""
    
    # OpenAI 설정
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # 데이터베이스 설정
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_NAME = os.getenv('DB_NAME', 'clara_cs')
    
    # 애플리케이션 설정
    DEFAULT_USER_ID = int(os.getenv('DEFAULT_USER_ID', '1'))  # 기본 사용자 ID
    
    # 리포트 설정
    CHART_DAYS_RANGE = int(os.getenv('CHART_DAYS_RANGE', '365'))  # 차트 조회 기간 (일)
    
    # 로깅 설정
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Flask 설정
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
