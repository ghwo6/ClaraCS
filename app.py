from flask import Flask, send_file, jsonify,request,after_this_request
from flasgger import Swagger
from controllers.mapping import mapping_bp
from controllers.export_to_pdf import create_prototype_report
import os
import datetime
import re
from urllib.parse import quote
import pandas as pd
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
    
    @app.route('/dashboard')
    def get_dashboard_data():
        """ 여기서 DB 쿼리를 통해 실제 데이터를 가져와야 합니다."""
        """ 아래는 더미데이터 입니다."""
            # 1. KPI 데이터
        kpi_data = {
            'completed': 133,
            'pending': 13
        }

        # 2. TOP 3 카테고리 데이터
        top_categories_data = [
            {'rank': 1, 'category': '결제', 'count': 11},
            {'rank': 2, 'category': '배송', 'count': 7},
            {'rank': 3, 'category': '환불', 'count': 1}
        ]

        # 3. 카테고리별 분포 (파이 차트용)
        category_distribution_data = [
            {'category': '제품 하자', 'percentage': 40},
            {'category': '네트워크 불량', 'percentage': 35},
            {'category': '배송 문제', 'percentage': 25}
        ]
        
        # 4. AI 인사이트 (openai 라이브러리 활용)
        # insight_prompt = f"{period} 동안의 CS 데이터를 요약하고 단기/장기 솔루션을 제안해줘."
        # generated_text = call_openai_api(insight_prompt) # 가상의 함수
        generated_insights_html = """
            <h4>1. 제품 하자 (40%)</h4>
            <ul>
                <li>음성, 상담 의존도가 높으므로 전문 대응이 필요합니다.</li>
                <li><b>단기:</b> 제품별 FAQ, 영상 가이드 제공</li>
                <li><b>장기:</b> 하자 데이터를 R&D 부서에 피드백하여 불량률 개선</li>
            </ul>
            <h4>종합적 인사이트</h4>
            <ul>
                <li><b>단기:</b> 게시판 자동 분류, 챗봇 고도화, 음성 콜백 도입을 통해 대응 효율을 높일 수 있습니다.</li>
                <li><b>장기:</b> CS 데이터를 제품, IT, 물류 부서와 실시간으로 공유하는 피드백 체계를 구축해야 합니다.</li>
            </ul>
        """

        # 최종 응답 데이터 구성
        response_data = {
            'kpi': kpi_data,
            'top_categories': top_categories_data,
            'category_distribution': category_distribution_data,
            'insights': generated_insights_html
        }

        return jsonify(response_data)

    @app.route('/download-pdf', methods=['GET'])
    def download_pdf_file():
        try:
            file_id = request.args.get('file_id')
            if not file_id:
                return jsonify({"error": "file_id 파라미터가 필요합니다."}), 400
        
            # 1. 파일 이름 및 경로 설정
            report_data = {
                "company_name": "XX(주)",
                "date": datetime.date.today().strftime("%Y.%m.%d")
            }
            download_filename = f"AI분석리포트_{report_data['company_name']}_{report_data['date']}.pdf"
            save_dir = os.path.join(app.root_path, 'temp_reports_folder')
            os.makedirs(save_dir, exist_ok=True)
            temp_filename = f"AI분석리포트_{file_id}_{report_data['date']}.pdf"
            filename = re.sub(r'[\\\\/*?:"<>|]', "_", temp_filename)
            file_path = os.path.join(save_dir, filename)
            
            # 2. PDF 리포트 생성
            create_prototype_report(file_path, report_data)

            # 3. 파일 전송이 끝난 후 실행될 삭제 작업을 예약
            @after_this_request
            def remove_file(response):
                try:
                    os.remove(file_path)
                    print(f"임시 파일 삭제 완료: {file_path}")
                except Exception as error:
                    print(f"임시 파일 삭제 실패: {error}")
                return response

            # 4. 생성된 PDF 파일을 클라이언트에 전송
            return send_file(
                file_path,
                as_attachment=True,
                download_name=quote(download_filename)
            )

        except Exception as e:
            # PDF 생성이나 파일 전송 등 모든 과정에서 발생하는 오류를 처리
            print(f"PDF 다운로드 처리 중 오류 발생: {e}")
            return jsonify({"error": "리포트를 처리하는 중 서버에서 오류가 발생했습니다."}), 500

    app.register_blueprint(main_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(mapping_bp)
    app.register_blueprint(auto_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
