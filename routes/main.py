from flask import Blueprint, render_template
from flasgger.utils import swag_from

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