from flask import Flask, send_file, jsonify,request
from flasgger import Swagger
from routes.main import main_bp
from routes.report import report_bp
from routes.auto_classify import auto_bp
from routes.export_to_pdf import create_prototype_report 
import os
import datetime
import re
from urllib.parse import quote

def create_app():
    app = Flask(__name__)

    app.config['SWAGGER'] = {
        'title': 'ClaraCS API',
        'uiversion': 3
    }
    Swagger(app)

    @app.route('/download-pdf', methods=["GET"])
    def download_pdf_report():
        """PDF 리포트를 생성하고 다운로드 합니다."""
        try:
            #1. PDF 파일을 저장할 임시 경로를 지정합니다.
            file_id = request.args.get('file_id')
            if not file_id:
                return jsonify({"error": "file_id 파라미터가 필요합니다."}), 400
            
            # 오늘 날짜를 'YYYYMMDD'형식의 문자열로 만듭니다.
            report_data = {
                "company_name": "XX(주)",
                "date":datetime.date.today().strftime("%Y.%m.%d")
            }
            # 최종 다운로드 파일 이름을 조합한다.
            download_filename = f"AI분석리포트_{report_data['company_name']}_{report_data['date']}.pdf"

            save_dir = os.path.join(app.root_path,'temp_reports_folder')
            os.makedirs(save_dir,exist_ok=True) # 폴더가 없으면 생성
            # 서버에 저장되는 임시 파일 이름
            temp_filename = f"AI분석리포트_{file_id}_{report_data['date']}.pdf"
            filename = re.sub(r'[\\/*?:"<>|]',"_",temp_filename) # 파일명에 특수문자 제거
            file_path = os.path.join(save_dir,filename)
            
            #2. PDF 리포트를 생성합니다.
            create_prototype_report(file_path,report_data)

            #3. 생성된 PDF 파일을 클라이언트에 전송합니다.
            return send_file(file_path,
                            as_attachment=True,
                            download_name=quote(download_filename))
        except Exception as e:
            print(f"PDF 생성 오류 : {e}")
            return jsonify({"error": "PDF 파일을 생성하는 중 오류가 발생했습니다."}), 500
    

    app.register_blueprint(main_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(auto_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
