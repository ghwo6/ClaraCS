from flask import Flask
from flasgger import Swagger
from dotenv import load_dotenv
from controllers.main import main_bp
from controllers.report import report_bp
from controllers.auto_classify import auto_bp

# .env 파일 로드
load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config['SWAGGER'] = {
        'title': 'ClaraCS API',
        'uiversion': 3
    }
    Swagger(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(auto_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
