from flask import Blueprint, render_template
from flasgger.utils import swag_from

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
@swag_from({
    'tags': ['Main'],
    'description': '메인 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def main():
    return render_template("main.html")

@main_bp.route("/dashboard")
@swag_from({
    'tags': ['Main'],
    'description': '대시보드 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def dashboard():
    return render_template("dashboard.html")

@main_bp.route("/upload")
@swag_from({
    'tags': ['Main'],
    'description': '데이터 업로드 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def upload():
    return render_template("upload.html")

@main_bp.route("/classify")
@swag_from({
    'tags': ['Main'],
    'description': '자동 분류 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def classify():
    return render_template("classify.html")

@main_bp.route("/report")
@swag_from({
    'tags': ['Main'],
    'description': '분석 리포트 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def report():
    return render_template("report.html")

@main_bp.route("/settings")
@swag_from({
    'tags': ['Main'],
    'description': '설정 도움말 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def settings():
    return render_template("settings.html")

@main_bp.route("/contact")
@swag_from({
    'tags': ['Main'],
    'description': '연락처 페이지 반환',
    'responses': {
        200: {
            'description': 'response OK'
        }
    }
})
def contact():
    return render_template("contact.html")
