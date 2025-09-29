from flask import Flask
from flasgger import Swagger
from routes.main import main_bp
from routes.report import report_bp
from routes.auto_classify import auto_bp # new!

def create_app():
    app = Flask(__name__)

    app.config['SWAGGER'] = {
        'title': 'ClaraCS API',
        'uiversion': 3
    }
    Swagger(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(auto_bp) # new!

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
