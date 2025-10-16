# 필요한 라이브러리들을 가져옵니다.
from flask import Blueprint, send_file, jsonify, request, after_this_request
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm, inch
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from services.db.report_db import ReportDB
from utils.logger import get_logger
import os
import datetime
import re
from urllib.parse import quote

logger = get_logger(__name__)

export_bp = Blueprint("export", __name__)

# 'malgun.ttf' 폰트 파일을 코드와 같은 경로에 준비해야 합니다.
try:
    pdfmetrics.registerFont(TTFont('MalgunGothic', 'malgun.ttf'))
    pdfmetrics.registerFont(TTFont('MalgunGothic-Bold', 'malgunbd.ttf')) # 볼드체
    FONT_NAME = "MalgunGothic"
    FONT_NAME_BOLD = "MalgunGothic-Bold"
except:
    print("맑은 고딕 폰트 파일(malgun.ttf)이 필요합니다. 기본 폰트로 대체합니다.")
    FONT_NAME = "Helvetica"
    FONT_NAME_BOLD = "Helvetica-Bold"
# -----------------------------


def create_prototype_report(filename, report_data):
    """전달받은 데이터를 기반으로 동적 PDF 리포트를 생성합니다."""

    # 1. 도화지(Canvas)를 준비합니다.
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4  # 페이지 크기 (가로, 세로)
    
    right_margin = width - (1 * cm)

    # --- 페이지 상단: 제목과 날짜 ---
    # c.setFont(FONT_NAME_BOLD, 11)
    c.setFont(FONT_NAME_BOLD, 14)
    c.drawCentredString(width/2, height - 1 * cm, "Clara CS 분석 리포트")
    
    company_name = report_data.get("company_name", "회사명 없음")
    report_date = report_data.get("date", "날짜 없음")
    
    c.setFont(FONT_NAME, 10)
    c.drawCentredString(width/2, height - 1.5 * cm, company_name)
    c.drawRightString(right_margin, height - 1 * cm, report_date)

    # --- 왼쪽 컬럼: 분석 데이터 정보 ---
    c.setFont(FONT_NAME_BOLD, 16)
    c.drawString(1 * inch, height - 2.0 * inch, "분석한 데이터")
    
    c.setFont(FONT_NAME, 9)
    c.setFillColor(colors.grey)
    c.drawString(1 * inch, height - 2.2 * inch, "분석한 데이터를 나타냅니다.")
    
    # 간단한 구분선
    c.setStrokeColor(colors.lightgrey)
    c.line(1 * inch, height - 2.3 * inch, 3.5 * inch, height - 2.3 * inch)

    # 채널별/카테고리별 데이터 (자리만 잡아둠)
    c.setFillColor(colors.black)
    c.setFont(FONT_NAME_BOLD, 12)
    c.drawString(1.2 * inch, height - 2.8 * inch, "채널별 데이터")
    c.drawString(1.2 * inch, height - 4.0 * inch, "카테고리별 데이터")


    # --- 오른쪽 컬럼: 데이터 요약 표 ---
    c.setFont(FONT_NAME_BOLD, 16)
    c.drawString(4.5 * inch, height - 2.0 * inch, "데이터 요약")

    c.setFont(FONT_NAME, 9)
    c.setFillColor(colors.grey)
    c.drawString(4.5 * inch, height - 2.2 * inch, "분석한 데이터를 보기 쉽게 요약한 내용입니다.")
    
    c.line(4.5 * inch, height - 2.3 * inch, 7.5 * inch, height - 2.3 * inch)
    
    # (핵심) Table 객체를 위한 데이터 구조 만들기
    # SB의 복잡한 구조를 2차원 리스트로 표현합니다. None은 셀 병합(SPAN)을 위한 빈 칸입니다.
    table_data = [
        ['분석 데이터', '15,150건', None],
        ['1:1 상담', '105건 (11%)', '해결률 88%'],
        ['전화상담', '200건 (22%)', '해결률 88%'],
        ['카카오톡', '150건 (16.6%)', '해결률 88%'],
        ['배송', '111건 (11%)', '해결률 88%'],
        ['환불/취소', '222건 (22%)', '해결률 88%'],
        ['품질/하자', '333건 (33%)', '해결률 88%'],
        ['AS/설치', '111건 (11%)', '해결률 88%'],
        ['기타', '111건 (11%)', '해결률 88%']
    ]

    summary_table = Table(table_data, colWidths=[0.9*inch, 1.2*inch, 0.9*inch])

    # Table 스타일 지정
    summary_table.setStyle(TableStyle([
        # 전체 스타일
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), # 수직 중앙 정렬
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey), # 옅은 회색 격자
        
        # 첫 번째 행 스타일 (분석 데이터)
        ('SPAN', (1, 0), (2, 0)), # (1,0) 셀부터 (2,0) 셀까지 병합
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('FONTNAME', (0,0), (0,0), FONT_NAME_BOLD),

        # 데이터 행 스타일
        ('ALIGN', (0, 1), (0, -1), 'RIGHT'), # 첫번째 열 우측 정렬
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'), # 나머지 열 중앙 정렬
    ]))

    # 캔버스에 표 그리기
    table_x = 4.5 * inch
    table_y = height - 5.5 * inch
    summary_table.wrapOn(c, width, height) # 크기 계산
    summary_table.drawOn(c, table_x, table_y)


    # --- 하단: 차트 영역 ---
    c.setFillColor(colors.black)
    c.setFont(FONT_NAME_BOLD, 16)
    c.drawString(1 * inch, 3.0 * inch, "날짜별 접수된 CS 건 수")
    
    # 차트 영역을 회색 사각형으로 표시 (프로토타입)
    c.setFillColor(colors.HexColor('#F0F0F0'))
    c.setStrokeColor(colors.lightgrey)
    c.rect(1 * inch, 1.2 * inch, 6.5 * inch, 1.6 * inch, fill=1, stroke=1)
    
    # 사각형 안에 텍스트 추가
    c.setFillColor(colors.darkgrey)
    c.setFont(FONT_NAME, 12)
    c.drawCentredString(4.25 * inch, 2.0 * inch, "(차트 이미지가 여기에 표시됩니다)")

    # 2. 작업을 모두 마치고 파일을 저장합니다.
    c.save()
    print(f"'{filename}' 파일이 성공적으로 생성되었습니다.")


@export_bp.route('/download-pdf', methods=['GET'])
def download_pdf_file():
    """리포트 PDF 다운로드 API - 실제 생성된 리포트 데이터 사용 (메모리 스트림)"""
    try:
        report_id = request.args.get('report_id')
        if not report_id:
            return jsonify({"error": "report_id 파라미터가 필요합니다."}), 400
        
        logger.info(f"리포트 PDF 다운로드 요청: report_id={report_id}")
        
        # 1. DB에서 리포트 데이터 조회
        report_db = ReportDB()
        report_data = report_db.get_report_with_snapshots(int(report_id))
        
        if not report_data:
            logger.warning(f"리포트를 찾을 수 없음: report_id={report_id}")
            return jsonify({"error": "해당 리포트를 찾을 수 없습니다."}), 404
        
        # 2. PDF 데이터 구성
        pdf_data = {
            "company_name": "ClaraCS",
            "date": datetime.date.today().strftime("%Y.%m.%d"),
            "report_id": report_id,
            "report_data": report_data
        }
        
        download_filename = f"AI분석리포트_{pdf_data['company_name']}_{pdf_data['date']}.pdf"
        
        # 3. 메모리에서 PDF 생성
        logger.info(f"PDF 생성 중 (메모리): {download_filename}")
        from io import BytesIO
        
        pdf_buffer = BytesIO()
        create_report_with_real_data_to_buffer(pdf_buffer, pdf_data)
        pdf_buffer.seek(0)
        
        # 4. 생성된 PDF를 메모리에서 바로 전송
        logger.info(f"PDF 다운로드 완료: {download_filename}")
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=quote(download_filename)
        )
        
    except Exception as e:
        logger.error(f"PDF 다운로드 처리 중 오류 발생: {e}")
        return jsonify({"error": "리포트를 처리하는 중 서버에서 오류가 발생했습니다."}), 500


def create_report_with_real_data_to_buffer(buffer, pdf_data):
    """실제 리포트 데이터를 기반으로 PDF 생성 (BytesIO 버퍼에 직접 작성)"""
    report_data = pdf_data.get('report_data', {})
    summary = report_data.get('summary', {})
    insight = report_data.get('insight', {})
    solution = report_data.get('solution', {})
    
    # 1. 도화지(Canvas)를 준비합니다 (버퍼에 작성)
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    right_margin = width - (1 * cm)
    
    # --- 페이지 상단: 제목과 날짜 ---
    c.setFont(FONT_NAME_BOLD, 14)
    c.drawCentredString(width/2, height - 1 * cm, "ClaraCS AI 분석 리포트")
    
    company_name = pdf_data.get("company_name", "ClaraCS")
    report_date = pdf_data.get("date", datetime.date.today().strftime("%Y.%m.%d"))
    
    c.setFont(FONT_NAME, 10)
    c.drawCentredString(width/2, height - 1.5 * cm, company_name)
    c.drawRightString(right_margin, height - 1 * cm, report_date)
    
    # --- 데이터 요약 섹션 ---
    c.setFont(FONT_NAME_BOLD, 16)
    c.drawString(1 * inch, height - 2.0 * inch, "데이터 요약")
    
    c.setFont(FONT_NAME, 9)
    c.setFillColor(colors.grey)
    c.drawString(1 * inch, height - 2.2 * inch, f"Report ID: {pdf_data.get('report_id', 'N/A')}")
    
    c.setStrokeColor(colors.lightgrey)
    c.line(1 * inch, height - 2.3 * inch, 7.5 * inch, height - 2.3 * inch)
    
    # 데이터 요약 테이블 생성
    total_cs = summary.get('total_tickets', 0) if isinstance(summary, dict) else 0
    category_ratios = summary.get('category_ratios', {}) if isinstance(summary, dict) else {}
    resolved_count = summary.get('resolved_count', {}) if isinstance(summary, dict) else {}
    
    # 테이블 데이터 구성
    table_data = [
        ['항목', '값', '비율']
    ]
    
    # 전체 CS 건수
    table_data.append(['전체 CS 건수', f'{total_cs:,}건', '-'])
    
    # 카테고리별 데이터
    if category_ratios and isinstance(category_ratios, dict):
        for i, (cat_name, cat_percentage) in enumerate(list(category_ratios.items())[:5]):
            cat_count = int(total_cs * float(cat_percentage) / 100) if total_cs > 0 else 0
            table_data.append([cat_name, f'{cat_count}건', f'{cat_percentage}%'])
    
    # 채널별 해결률
    if resolved_count and isinstance(resolved_count, dict):
        for channel, resolution_rate in list(resolved_count.items())[:3]:
            table_data.append([f'{channel} 해결률', '-', f'{resolution_rate}%'])
    
    summary_table = Table(table_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
        ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    
    table_x = 1 * inch
    table_y = height - 5.5 * inch
    summary_table.wrapOn(c, width, height)
    summary_table.drawOn(c, table_x, table_y)
    
    # --- 인사이트 섹션 ---
    c.setFont(FONT_NAME_BOLD, 14)
    c.drawString(1 * inch, height - 6.0 * inch, "AI 인사이트")
    
    y_position = height - 6.3 * inch
    c.setFont(FONT_NAME, 9)
    c.setFillColor(colors.black)
    
    # 인사이트 내용 표시
    if insight and isinstance(insight, dict):
        overall = insight.get('overall', {})
        if isinstance(overall, dict) and overall.get('summary'):
            summary_text = overall.get('summary', '')
            max_width = 6.5 * inch
            lines = []
            words = summary_text.split()
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if c.stringWidth(test_line, FONT_NAME, 9) < max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            for line in lines[:5]:
                c.drawString(1.2 * inch, y_position, line)
                y_position -= 0.15 * inch
    
    # --- 솔루션 제안 섹션 ---
    y_position -= 0.3 * inch
    c.setFont(FONT_NAME_BOLD, 14)
    c.drawString(1 * inch, y_position, "솔루션 제안")
    
    y_position -= 0.25 * inch
    c.setFont(FONT_NAME, 9)
    
    if solution and isinstance(solution, dict):
        short_term = solution.get('short_term', {})
        if isinstance(short_term, dict) and short_term.get('goal_kpi'):
            c.setFont(FONT_NAME_BOLD, 10)
            c.drawString(1.2 * inch, y_position, "단기 (1-6개월)")
            y_position -= 0.2 * inch
            
            c.setFont(FONT_NAME, 9)
            goal = short_term.get('goal_kpi', '')[:80]
            c.drawString(1.4 * inch, y_position, f"목표: {goal}")
            y_position -= 0.15 * inch
    
    # 2. 버퍼에 저장
    c.save()
    logger.info(f"PDF 생성 완료 (메모리)")


# --- [수정] 함수를 직접 테스트할 때도 임시 데이터를 넣어줍니다 ---
if __name__ == "__main__":
    test_data = {
        "company_name": "XX(주)",
        "date": "2025.10.03"
    }
    create_prototype_report("test_report.pdf", test_data)