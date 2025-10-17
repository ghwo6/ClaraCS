from flask import Flask, session
from flasgger import Swagger
from config import Config
from dotenv import load_dotenv
from controllers.main import main_bp
from controllers.upload import upload_bp
from controllers.report import report_bp
from controllers.auto_classify import auto_bp
from controllers.mapping import mapping_bp
from controllers.dashboard import dashboard_bp
from controllers.export_to_pdf import export_bp

# .env 파일 로드
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Config 설정 로드
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    app.config['SWAGGER'] = {
        'title': 'ClaraCS API',
        'uiversion': 3
    }
    Swagger(app)
    
    # 템플릿 컨텍스트 프로세서 (설정값을 모든 템플릿에 전달)
    @app.context_processor
    def inject_config():
        return {
            'DEFAULT_USER_ID': Config.DEFAULT_USER_ID,
            'CHART_DAYS_RANGE': Config.CHART_DAYS_RANGE
        }
    
    # 세션 초기화 (로그인 구현 전까지 기본 user_id 사용)
    @app.before_request
    def init_session():
        if 'user_id' not in session:
            session['user_id'] = Config.DEFAULT_USER_ID
    
    # Blueprint 등록
    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(auto_bp)
    app.register_blueprint(mapping_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(export_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
