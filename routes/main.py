from flask import Blueprint, render_template, Flask
from flasgger.utils import swag_from
from .mapping import mapping_bp


main_bp = Blueprint("main", __name__)

@main_bp.route("/")
@swag_from({
    'tags': ['Main'],
    'description': 'index.html 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def index():
    return render_template("index.html")

app = Flask(__name__)
app.register_blueprint(main_bp)   
app.register_blueprint(mapping_bp)  

if __name__ == "__main__":
    app.run(debug=True)