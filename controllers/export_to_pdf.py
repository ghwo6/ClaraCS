# 필요한 라이브러리들을 가져옵니다.
from flask import Blueprint, send_file, jsonify, request, after_this_request
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm, inch
from reportlab.platypus import Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from services.db.report_db import ReportDB
from utils.logger import get_logger
import os
import datetime
import re
from urllib.parse import quote
import matplotlib
matplotlib.use('Agg')  # GUI 없이 사용
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from io import BytesIO
import base64
from PIL import Image

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
    """실제 리포트 데이터를 기반으로 PDF 생성 (프로토타입 레이아웃 기반)"""
    report_data = pdf_data.get('report_data', {})
    
    # 데이터 추출 (스냅샷에서 가져오기)
    summary = report_data.get('summary', {})
    insight = report_data.get('insight', {})
    solution = report_data.get('solution', {})
    channel_trends = report_data.get('channel_trends', {})
    
    logger.info(f"PDF 생성 데이터 확인 - summary: {bool(summary)}, channel_trends: {len(channel_trends) if channel_trends else 0}개")
    
    # Canvas 생성
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    right_margin = width - (1 * cm)
    
    company_name = pdf_data.get("company_name", "ClaraCS")
    report_date = pdf_data.get("date", datetime.date.today().strftime("%Y.%m.%d"))
    
    # ========== 페이지 1: 데이터 요약 ==========
    draw_page_header(c, "ClaraCS AI 분석 리포트", company_name, report_date, width, height, right_margin)
    draw_page1_summary(c, summary, width, height)
    
    # ========== 페이지 2: 채널별 추이 (모든 채널, 크게) ==========
    c.showPage()
    draw_page_header(c, "ClaraCS AI 분석 리포트 - 채널별 추이", company_name, report_date, width, height, right_margin)
    draw_page2_all_channel_trends(c, channel_trends, width, height, company_name, report_date, right_margin)
    
    # ========== 페이지 3: 인사이트 도출 ==========
    c.showPage()
    draw_insights_page(c, insight, width, height, company_name, report_date, right_margin)
    
    # ========== 페이지 4: 솔루션 제안 ==========
    c.showPage()
    draw_solutions_page(c, solution, width, height, company_name, report_date, right_margin)
    
    # PDF 저장
    c.save()
    logger.info("PDF 생성 완료 (메모리)")


def draw_page_header(c, title, company_name, report_date, width, height, right_margin):
    """페이지 상단 헤더"""
    c.setFont(FONT_NAME_BOLD, 14)
    c.drawCentredString(width/2, height - 1 * cm, title)
    c.setFont(FONT_NAME, 10)
    c.drawCentredString(width/2, height - 1.5 * cm, company_name)
    c.drawRightString(right_margin, height - 1 * cm, report_date)


def draw_page2_all_channel_trends(c, channel_trends, width, height, company_name, report_date, right_margin):
    """페이지 2: 모든 채널별 추이 그래프 (한 줄에 하나씩, 크게)"""
    y_start = height - 1.5 * inch
    
    c.setFillColor(colors.black)
    c.setFont(FONT_NAME_BOLD, 18)
    c.drawString(1 * inch, y_start, "📈 채널별 추이")
    
    if not channel_trends or len(channel_trends) == 0:
        c.setFont(FONT_NAME, 11)
        c.setFillColor(colors.grey)
        c.drawString(1.2*inch, y_start - 0.5*inch, "채널별 추이 데이터가 없습니다.")
        c.setFillColor(colors.black)
        return
    
    y_pos = y_start - 0.3*inch  # 제목과 그래프 간격 축소
    chart_width = 6.5 * inch  # 전체 너비 사용
    chart_height = 2.3 * inch  # 높이 조정 (한 페이지에 3개 들어가도록)
    is_first = True
    
    for channel, trend_data in channel_trends.items():
        # 첫 번째가 아니고 페이지 공간이 부족하면 새 페이지
        if not is_first and y_pos < chart_height + 0.8*inch:
            c.showPage()
            draw_page_header(c, "ClaraCS AI 분석 리포트 - 채널별 추이 (계속)", 
                           company_name, report_date, width, height, right_margin)
            y_pos = height - 1.5*inch
        
        is_first = False
        
        # 차트 제목
        c.setFillColor(colors.black)
        c.setFont(FONT_NAME_BOLD, 12)
        c.drawString(1 * inch, y_pos, f"{channel} 채널")
        y_pos -= 0.15*inch  # 제목과 그래프 간격 축소
        
        # 차트 이미지 생성 및 삽입
        chart_image = create_channel_chart_image(channel, trend_data)
        
        if chart_image:
            c.drawImage(chart_image, 1*inch, y_pos - chart_height,
                       width=chart_width, height=chart_height, preserveAspectRatio=True)
        else:
            # 차트 생성 실패 시 회색 박스
            c.setFillColor(colors.HexColor('#F0F0F0'))
            c.setStrokeColor(colors.lightgrey)
            c.rect(1*inch, y_pos - chart_height, chart_width, chart_height, fill=1, stroke=1)
            c.setFillColor(colors.darkgrey)
            c.setFont(FONT_NAME, 12)
            c.drawCentredString(4.25*inch, y_pos - chart_height/2, f"{channel} 채널 데이터")
            c.setFillColor(colors.black)
        
        y_pos -= (chart_height + 0.2*inch)  # 그래프와 다음 제목 간격 축소


def draw_page1_summary(c, summary, width, height):
    """페이지 1: 데이터 요약"""
    y_start = height - 2.2 * inch
    
    # 제목을 한 줄로 표시 (베이스라인 정렬)
    c.setFont(FONT_NAME_BOLD, 16)
    c.drawString(1 * inch, y_start, "📊 데이터 요약  ")
    
    # 괄호 부분을 데이터 요약의 아래부분에 맞춤
    c.setFont(FONT_NAME, 9)
    c.setFillColor(colors.grey)
    c.drawString(2.5 * inch, y_start, "(전체 CS 데이터를 요약하여 보여줍니다)")
    c.setFillColor(colors.black)
    
    y_pos = y_start - 0.4*inch
    
    # 전체 CS 건수
    total_cs = summary.get('total_cs_count', 0)
    c.setFont(FONT_NAME_BOLD, 14)
    c.drawString(1.2*inch, y_pos, f"전체 CS 건수: {total_cs:,}건")
    y_pos -= 0.4*inch
    
    # 카테고리별 데이터 (상위 5개)
    categories = summary.get('categories', [])
    if categories:
        c.setFont(FONT_NAME_BOLD, 12)
        c.drawString(1.2*inch, y_pos, "카테고리별 분포 (TOP 5)")
        y_pos -= 0.3*inch
        
        table_data = [['카테고리', '건수', '비율']]
        for cat in categories[:5]:
            table_data.append([
                cat.get('category_name', '-'),
                f"{cat.get('count', 0):,}건",
                f"{cat.get('percentage', 0):.1f}%"
            ])
        
        category_table = Table(table_data, colWidths=[2*inch, 1.2*inch, 0.8*inch])
        category_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        
        category_table.wrapOn(c, width, height)
        category_table.drawOn(c, 1.2*inch, y_pos - len(table_data)*0.24*inch)
        
        y_pos -= (len(table_data) * 0.24*inch + 0.4*inch)
    
    # 채널별 해결률 (상위 5개)
    channels = summary.get('channels', [])
    if channels and y_pos > 1.5*inch:
        c.setFont(FONT_NAME_BOLD, 12)
        c.drawString(1.2*inch, y_pos, "채널별 해결률")
        y_pos -= 0.3*inch
        
        table_data = [['채널', '전체', '해결', '해결률']]
        for ch in channels[:5]:
            table_data.append([
                ch.get('channel', '-'),
                f"{ch.get('total', 0):,}건",
                f"{ch.get('resolved', 0):,}건",
                f"{ch.get('resolution_rate', 0):.1f}%"
            ])
        
        channel_table = Table(table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch])
        channel_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), FONT_NAME_BOLD),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ]))
        
        channel_table.wrapOn(c, width, height)
        channel_table.drawOn(c, 1.2*inch, y_pos - len(table_data)*0.24*inch)


def draw_page2_additional_charts(c, channel_trends, summary, width, height):
    """페이지 2: 추가 채널 그래프"""
    y_start = height - 2.2 * inch
    
    c.setFillColor(colors.black)
    c.setFont(FONT_NAME_BOLD, 16)
    c.drawString(1 * inch, y_start, "📈 채널별 세부 추이")
    
    if channel_trends and len(channel_trends) > 2:
        # 3번째 이후 채널들
        channels = list(channel_trends.items())[2:]
        
        y_pos = y_start - 0.5*inch
        
        for idx, (channel, trend_data) in enumerate(channels[:3]):  # 최대 3개 더
            if y_pos < 2*inch:
                break
            
            chart_image = create_channel_chart_image(channel, trend_data)
            
            # 차트 제목
            c.setFont(FONT_NAME_BOLD, 12)
            c.drawString(1.2*inch, y_pos, f"{channel} 채널")
            
            if chart_image:
                c.drawImage(chart_image, 1*inch, y_pos - 2.2*inch,
                           width=6.5*inch, height=2*inch, preserveAspectRatio=True)
            else:
                c.setFillColor(colors.HexColor('#F0F0F0'))
                c.setStrokeColor(colors.lightgrey)
                c.rect(1*inch, y_pos - 2.2*inch, 6.5*inch, 2*inch, fill=1, stroke=1)
                c.setFillColor(colors.darkgrey)
                c.setFont(FONT_NAME, 10)
                c.drawCentredString(4.25*inch, y_pos - 1.2*inch, f"{channel} 데이터")
                c.setFillColor(colors.black)
            
            y_pos -= 2.6*inch
    else:
        # 추가 채널이 없을 때
        c.setFont(FONT_NAME, 11)
        c.setFillColor(colors.grey)
        c.drawString(1.2*inch, y_start - 0.5*inch, "추가 채널 데이터가 없습니다.")
        c.setFillColor(colors.black)


def draw_left_column_data(c, summary, channel_trends, width, height):
    """왼쪽 컬럼: 분석한 데이터"""
    c.setFont(FONT_NAME_BOLD, 16)
    c.drawString(1 * inch, height - 2.0 * inch, "분석한 데이터")
    
    c.setFont(FONT_NAME, 9)
    c.setFillColor(colors.grey)
    c.drawString(1 * inch, height - 2.2 * inch, "분석한 데이터를 나타냅니다.")
    
    # 구분선
    c.setStrokeColor(colors.lightgrey)
    c.line(1 * inch, height - 2.3 * inch, 3.5 * inch, height - 2.3 * inch)
    
    c.setFillColor(colors.black)
    y_pos = height - 2.8 * inch
    
    # 채널별 데이터
    c.setFont(FONT_NAME_BOLD, 12)
    c.drawString(1.2 * inch, y_pos, "채널별 데이터")
    y_pos -= 0.2 * inch
    
    c.setFont(FONT_NAME, 9)
    channels = summary.get('channels', [])
    for ch in channels[:5]:
        channel_name = ch.get('channel', '-')
        total = ch.get('total', 0)
        resolved = ch.get('resolved', 0)
        resolution_rate = ch.get('resolution_rate', 0)
        
        c.drawString(1.3 * inch, y_pos, f"{channel_name}: {total:,}건")
        y_pos -= 0.15 * inch
        c.setFont(FONT_NAME, 8)
        c.setFillColor(colors.grey)
        c.drawString(1.5 * inch, y_pos, f"(해결: {resolved:,}건, 해결률: {resolution_rate:.1f}%)")
        c.setFillColor(colors.black)
        y_pos -= 0.2 * inch
        c.setFont(FONT_NAME, 9)
    
    # 카테고리별 데이터
    y_pos -= 0.2 * inch
    c.setFont(FONT_NAME_BOLD, 12)
    c.drawString(1.2 * inch, y_pos, "카테고리별 데이터")
    y_pos -= 0.2 * inch
    
    c.setFont(FONT_NAME, 9)
    categories = summary.get('categories', [])
    for cat in categories[:5]:
        cat_name = cat.get('category_name', '-')
        count = cat.get('count', 0)
        percentage = cat.get('percentage', 0)
        
        c.drawString(1.3 * inch, y_pos, f"{cat_name}: {count:,}건 ({percentage:.1f}%)")
        y_pos -= 0.18 * inch


def draw_right_column_summary(c, summary, width, height):
    """오른쪽 컬럼: 데이터 요약 표"""
    c.setFont(FONT_NAME_BOLD, 16)
    c.drawString(4.5 * inch, height - 2.0 * inch, "데이터 요약")
    
    c.setFont(FONT_NAME, 9)
    c.setFillColor(colors.grey)
    c.drawString(4.5 * inch, height - 2.2 * inch, "분석한 데이터를 보기 쉽게 요약한 내용입니다.")
    
    c.setStrokeColor(colors.lightgrey)
    c.line(4.5 * inch, height - 2.3 * inch, 7.5 * inch, height - 2.3 * inch)
    
    c.setFillColor(colors.black)
    
    # 테이블 데이터 구성
    total_cs = summary.get('total_cs_count', 0)
    categories = summary.get('categories', [])
    channels = summary.get('channels', [])
    
    table_data = [
        ['분석 데이터', f'{total_cs:,}건', None],
    ]
    
    # 채널별 데이터 (상위 3개)
    for ch in channels[:3]:
        channel = ch.get('channel', '-')
        total = ch.get('total', 0)
        percentage = (total / total_cs * 100) if total_cs > 0 else 0
        resolution_rate = ch.get('resolution_rate', 0)
        table_data.append([
            channel,
            f'{total:,}건 ({percentage:.1f}%)',
            f'해결률 {resolution_rate:.1f}%'
        ])
    
    # 카테고리별 데이터 (상위 5개)
    for cat in categories[:5]:
        cat_name = cat.get('category_name', '-')
        count = cat.get('count', 0)
        percentage = cat.get('percentage', 0)
        table_data.append([
            cat_name,
            f'{count:,}건 ({percentage:.1f}%)',
            '-'
        ])
    
    summary_table = Table(table_data, colWidths=[0.9*inch, 1.2*inch, 0.9*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('SPAN', (1, 0), (2, 0)),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), FONT_NAME_BOLD),
        ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
    ]))
    
    table_x = 4.5 * inch
    table_y = height - 5.5 * inch
    summary_table.wrapOn(c, width, height)
    summary_table.drawOn(c, table_x, table_y)


def draw_bottom_charts(c, channel_trends, width, height):
    """하단: 채널별 추이 차트"""
    c.setFillColor(colors.black)
    c.setFont(FONT_NAME_BOLD, 16)
    c.drawString(1 * inch, 3.0 * inch, "채널별 추이 그래프")
    
    if channel_trends and len(channel_trends) > 0:
        # 상위 1개 채널 그래프만 표시
        channel, trend_data = list(channel_trends.items())[0]
        chart_image = create_channel_chart_image(channel, trend_data)
        
        if chart_image:
            c.drawImage(chart_image, 1 * inch, 1.2 * inch, 
                       width=6.5 * inch, height=1.6 * inch, preserveAspectRatio=True)
        else:
            # 차트 생성 실패 시 회색 박스
            c.setFillColor(colors.HexColor('#F0F0F0'))
            c.setStrokeColor(colors.lightgrey)
            c.rect(1 * inch, 1.2 * inch, 6.5 * inch, 1.6 * inch, fill=1, stroke=1)
            c.setFillColor(colors.darkgrey)
            c.setFont(FONT_NAME, 12)
            c.drawCentredString(4.25 * inch, 2.0 * inch, f"{channel} 채널 데이터")
    else:
        # 데이터 없을 때
        c.setFillColor(colors.HexColor('#F0F0F0'))
        c.setStrokeColor(colors.lightgrey)
        c.rect(1 * inch, 1.2 * inch, 6.5 * inch, 1.6 * inch, fill=1, stroke=1)
        c.setFillColor(colors.darkgrey)
        c.setFont(FONT_NAME, 12)
        c.drawCentredString(4.25 * inch, 2.0 * inch, "(채널별 추이 데이터)")


def draw_insights_page(c, insight, width, height, company_name, report_date, right_margin):
    """페이지 2: 인사이트 도출"""
    # 헤더
    c.setFont(FONT_NAME_BOLD, 14)
    c.drawCentredString(width/2, height - 1 * cm, "ClaraCS AI 분석 리포트 - 인사이트 도출")
    c.setFont(FONT_NAME, 10)
    c.drawCentredString(width/2, height - 1.5 * cm, company_name)
    c.drawRightString(right_margin, height - 1 * cm, report_date)
    
    y_pos = height - 2.5 * inch
    
    # 종합 분석 요약
    overall = insight.get('overall', {})
    if overall and overall.get('summary'):
        c.setFont(FONT_NAME_BOLD, 14)
        c.drawString(1 * inch, y_pos, "💡 종합 분석 요약")
        y_pos -= 0.3 * inch
        
        c.setFont(FONT_NAME, 10)
        summary_text = overall.get('summary', '')
        lines = wrap_text(c, summary_text, 6.5*inch, FONT_NAME, 10)
        for line in lines[:6]:
            c.drawString(1.2 * inch, y_pos, line)
            y_pos -= 0.2 * inch
        
        y_pos -= 0.2 * inch
    
    # 주요 이슈
    notable_issues = overall.get('notable_issues', [])
    if notable_issues:
        c.setFont(FONT_NAME_BOLD, 12)
        c.drawString(1 * inch, y_pos, "⚠️ 주요 이슈")
        y_pos -= 0.25 * inch
        
        c.setFont(FONT_NAME, 9)
        for issue in notable_issues[:5]:
            wrapped_lines = wrap_text(c, f"• {issue}", 6.3*inch, FONT_NAME, 9)
            for line in wrapped_lines[:2]:
                c.drawString(1.2 * inch, y_pos, line)
                y_pos -= 0.18 * inch
        
        y_pos -= 0.2 * inch
    
    # 카테고리별 인사이트
    by_category = insight.get('by_category', [])
    if by_category:
        c.setFont(FONT_NAME_BOLD, 12)
        c.drawString(1 * inch, y_pos, "📊 카테고리별 세부 인사이트")
        y_pos -= 0.3 * inch
        
        for cat in by_category[:4]:
            if y_pos < 1.5 * inch:
                break
            
            priority_icon = '🔴' if cat.get('priority') == 'high' else '🟡' if cat.get('priority') == 'medium' else '🟢'
            
            c.setFont(FONT_NAME_BOLD, 10)
            c.drawString(1.2 * inch, y_pos, f"{priority_icon} {cat.get('category_name', '')}")
            y_pos -= 0.2 * inch
            
            c.setFont(FONT_NAME, 8)
            problem_lines = wrap_text(c, f"문제점: {cat.get('problem', '-')}", 6*inch, FONT_NAME, 8)
            for line in problem_lines[:2]:
                c.drawString(1.4 * inch, y_pos, line)
                y_pos -= 0.16 * inch
            
            goal_lines = wrap_text(c, f"단기 목표: {cat.get('short_term_goal', '-')}", 6*inch, FONT_NAME, 8)
            for line in goal_lines[:2]:
                c.drawString(1.4 * inch, y_pos, line)
                y_pos -= 0.16 * inch
            
            y_pos -= 0.15 * inch


def draw_solutions_page(c, solution, width, height, company_name, report_date, right_margin):
    """페이지 3: 솔루션 제안"""
    # 헤더
    c.setFont(FONT_NAME_BOLD, 14)
    c.drawCentredString(width/2, height - 1 * cm, "ClaraCS AI 분석 리포트 - 솔루션 제안")
    c.setFont(FONT_NAME, 10)
    c.drawCentredString(width/2, height - 1.5 * cm, company_name)
    c.drawRightString(right_margin, height - 1 * cm, report_date)
    
    y_pos = height - 2.5 * inch
    
    # 현황 및 문제점
    current_status = solution.get('current_status_and_problems', {})
    if current_status:
        c.setFont(FONT_NAME_BOLD, 14)
        c.drawString(1 * inch, y_pos, "🎯 핵심 현황 및 우선순위")
        y_pos -= 0.3 * inch
        
        c.setFont(FONT_NAME, 10)
        if current_status.get('status'):
            c.setFont(FONT_NAME_BOLD, 9)
            c.drawString(1.2 * inch, y_pos, "현황:")
            y_pos -= 0.2 * inch
            c.setFont(FONT_NAME, 9)
            lines = wrap_text(c, current_status['status'], 6.3*inch, FONT_NAME, 9)
            for line in lines[:3]:
                c.drawString(1.3 * inch, y_pos, line)
                y_pos -= 0.18 * inch
        
        if current_status.get('problems'):
            c.setFont(FONT_NAME_BOLD, 9)
            c.drawString(1.2 * inch, y_pos, "문제점:")
            y_pos -= 0.2 * inch
            c.setFont(FONT_NAME, 9)
            lines = wrap_text(c, current_status['problems'], 6.3*inch, FONT_NAME, 9)
            for line in lines[:3]:
                c.drawString(1.3 * inch, y_pos, line)
                y_pos -= 0.18 * inch
        
        y_pos -= 0.2 * inch
    
    # 단기/중기/장기 솔루션
    periods = [
        ('단기 (1-6개월)', solution.get('short_term', {})),
        ('중기 (6-12개월)', solution.get('mid_term', {})),
        ('장기 (12개월+)', solution.get('long_term', {}))
    ]
    
    for period_name, period_data in periods:
        if not period_data or y_pos < 2 * inch:
            break
        
        c.setFont(FONT_NAME_BOLD, 12)
        c.drawString(1 * inch, y_pos, f"📅 {period_name}")
        y_pos -= 0.25 * inch
        
        c.setFont(FONT_NAME, 9)
        if period_data.get('goal_kpi'):
            c.setFont(FONT_NAME_BOLD, 8)
            c.drawString(1.2 * inch, y_pos, "목표:")
            y_pos -= 0.18 * inch
            c.setFont(FONT_NAME, 8)
            lines = wrap_text(c, period_data['goal_kpi'], 6*inch, FONT_NAME, 8)
            for line in lines[:2]:
                c.drawString(1.3 * inch, y_pos, line)
                y_pos -= 0.16 * inch
        
        actions = period_data.get('actions', [])
        if actions:
            c.setFont(FONT_NAME_BOLD, 8)
            c.drawString(1.2 * inch, y_pos, "액션 플랜:")
            y_pos -= 0.18 * inch
            c.setFont(FONT_NAME, 8)
            for action in actions[:3]:
                wrapped = wrap_text(c, f"• {action}", 5.8*inch, FONT_NAME, 8)
                for line in wrapped[:1]:
                    c.drawString(1.3 * inch, y_pos, line)
                    y_pos -= 0.16 * inch
        
        y_pos -= 0.2 * inch


# 기존 함수들 제거 (사용하지 않음)


def create_channel_chart_image(channel, trend_data):
    """채널별 그래프 이미지 생성 (matplotlib) - ImageReader 반환"""
    try:
        # 한글 폰트 설정
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.unicode_minus'] = False
        
        dates = trend_data.get('dates', [])
        categories = trend_data.get('categories', [])
        data_matrix = trend_data.get('data', [])
        
        if not dates or not data_matrix:
            return None
        
        # 그래프 생성 (크기 조정)
        fig, ax = plt.subplots(figsize=(10, 3.5))
        
        # 스택 막대 그래프
        bottom = [0] * len(dates)
        colors_list = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#f7b731', '#feca57']
        
        for i, category in enumerate(categories):
            category_data = [row[i] if i < len(row) else 0 for row in data_matrix]
            ax.bar(dates, category_data, bottom=bottom, label=category, 
                  color=colors_list[i % len(colors_list)], alpha=0.8)
            bottom = [b + d for b, d in zip(bottom, category_data)]
        
        # 전체 합계 선 그래프
        total_data = [sum(row) for row in data_matrix]
        ax.plot(dates, total_data, color='#e74c3c', linewidth=2, marker='o', 
               markersize=4, label='Total', zorder=10)
        
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('Count', fontsize=11)
        ax.legend(fontsize=9, loc='upper left', ncol=2)  # 2열로 범례 표시
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(fontsize=10)
        plt.tight_layout(pad=0.5)  # 여백 최소화
        
        # BytesIO로 저장 후 ImageReader로 변환
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        # ImageReader로 변환 (reportlab이 인식 가능)
        image_reader = ImageReader(img_buffer)
        
        return image_reader
        
    except Exception as e:
        logger.error(f"차트 이미지 생성 실패: {e}")
        return None


def draw_insights_section(c, insight, width, height):
    """인사이트 도출 섹션"""
    y_start = height - 1*inch
    
    # 섹션 제목
    c.setFillColor(colors.HexColor('#667eea'))
    c.setFont(FONT_NAME_BOLD, 18)
    c.drawString(1*inch, y_start, "💡 인사이트 도출")
    
    # 구분선
    c.setStrokeColor(colors.HexColor('#667eea'))
    c.setLineWidth(2)
    c.line(1*inch, y_start - 0.1*inch, 7.5*inch, y_start - 0.1*inch)
    
    y_position = y_start - 0.4*inch
    
    # 종합 분석 요약 (강조 박스)
    overall = insight.get('overall', {})
    if overall and overall.get('summary'):
        c.setFillColor(colors.HexColor('#f0f0ff'))
        c.rect(1*inch, y_position - 1.2*inch, 6.5*inch, 1.2*inch, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#667eea'))
        c.setFont(FONT_NAME_BOLD, 12)
        c.drawString(1.2*inch, y_position - 0.3*inch, "종합 분석 요약")
        
        # 텍스트 래핑
        summary_text = overall.get('summary', '')
        c.setFillColor(colors.black)
        c.setFont(FONT_NAME, 10)
        lines = wrap_text(c, summary_text, 6*inch, FONT_NAME, 10)
        
        text_y = y_position - 0.55*inch
        for line in lines[:4]:
            c.drawString(1.3*inch, text_y, line)
            text_y -= 0.18*inch
        
        y_position -= 1.5*inch
    
    # 주요 이슈
    notable_issues = overall.get('notable_issues', [])
    if notable_issues:
        c.setFillColor(colors.HexColor('#e74c3c'))
        c.setFont(FONT_NAME_BOLD, 12)
        c.drawString(1.2*inch, y_position, "⚠️ 주요 이슈")
        y_position -= 0.25*inch
        
        c.setFillColor(colors.black)
        c.setFont(FONT_NAME, 10)
        for issue in notable_issues[:5]:
            c.drawString(1.4*inch, y_position, f"• {issue}")
            y_position -= 0.2*inch
        
        y_position -= 0.2*inch
    
    # 카테고리별 인사이트
    by_category = insight.get('by_category', [])
    if by_category:
        c.setFillColor(colors.black)
        c.setFont(FONT_NAME_BOLD, 12)
        c.drawString(1.2*inch, y_position, "카테고리별 세부 인사이트")
        y_position -= 0.3*inch
        
        for cat in by_category[:3]:
            if y_position < 2*inch:
                break
                
            priority_icon = '🔴' if cat.get('priority') == 'high' else '🟡' if cat.get('priority') == 'medium' else '🟢'
            
            c.setFont(FONT_NAME_BOLD, 11)
            c.drawString(1.4*inch, y_position, f"{priority_icon} {cat.get('category_name', '')}")
            y_position -= 0.2*inch
            
            c.setFont(FONT_NAME, 9)
            c.drawString(1.6*inch, y_position, f"현황 및 문제점: {cat.get('problem', '-')[:80]}")
            y_position -= 0.18*inch
            c.drawString(1.6*inch, y_position, f"단기 목표: {cat.get('short_term_goal', '-')[:80]}")
            y_position -= 0.25*inch


def draw_solutions_section(c, solution, width, height):
    """솔루션 제안 섹션"""
    y_start = height - 1*inch
    
    # 섹션 제목
    c.setFillColor(colors.HexColor('#f5576c'))
    c.setFont(FONT_NAME_BOLD, 18)
    c.drawString(1*inch, y_start, "🎯 솔루션 제안")
    
    # 구분선
    c.setStrokeColor(colors.HexColor('#f5576c'))
    c.setLineWidth(2)
    c.line(1*inch, y_start - 0.1*inch, 7.5*inch, y_start - 0.1*inch)
    
    y_position = y_start - 0.4*inch
    
    # 현황 및 문제점: (강조 박스)
    current_status = solution.get('current_status_and_problems', {})
    if current_status:
        c.setFillColor(colors.HexColor('#fff5f5'))
        c.rect(1*inch, y_position - 1*inch, 6.5*inch, 1*inch, fill=1, stroke=0)
        
        c.setFillColor(colors.HexColor('#f5576c'))
        c.setFont(FONT_NAME_BOLD, 12)
        c.drawString(1.2*inch, y_position - 0.25*inch, "핵심 현황 및 우선순위")
        
        c.setFillColor(colors.black)
        c.setFont(FONT_NAME, 10)
        
        if current_status.get('status'):
            lines = wrap_text(c, f"현황: {current_status['status']}", 6*inch, FONT_NAME, 10)
            text_y = y_position - 0.5*inch
            for line in lines[:2]:
                c.drawString(1.3*inch, text_y, line)
                text_y -= 0.18*inch
        
        if current_status.get('problems'):
            lines = wrap_text(c, f"문제: {current_status['problems']}", 6*inch, FONT_NAME, 10)
            text_y = y_position - 0.75*inch
            for line in lines[:2]:
                c.drawString(1.3*inch, text_y, line)
                text_y -= 0.18*inch
        
        y_position -= 1.3*inch
    
    # 단기 솔루션
    short_term = solution.get('short_term', {})
    if short_term:
        draw_solution_period(c, "단기 (1-6개월)", short_term, y_position, width)
        y_position -= 1.2*inch
    
    # 중기 솔루션
    mid_term = solution.get('mid_term', {})
    if mid_term and y_position > 3*inch:
        draw_solution_period(c, "중기 (6-12개월)", mid_term, y_position, width)
        y_position -= 1.2*inch
    
    # 장기 솔루션
    long_term = solution.get('long_term', {})
    if long_term and y_position > 3*inch:
        draw_solution_period(c, "장기 (12개월+)", long_term, y_position, width)


def draw_solution_period(c, period_name, period_data, y_position, width):
    """솔루션 기간별 섹션 그리기"""
    c.setFillColor(colors.HexColor('#764ba2'))
    c.setFont(FONT_NAME_BOLD, 11)
    c.drawString(1.2*inch, y_position, period_name)
    y_position -= 0.22*inch
    
    c.setFillColor(colors.black)
    c.setFont(FONT_NAME, 9)
    
    if period_data.get('goal_kpi'):
        lines = wrap_text(c, f"목표: {period_data['goal_kpi']}", 5.5*inch, FONT_NAME, 9)
        for line in lines[:2]:
            c.drawString(1.4*inch, y_position, line)
            y_position -= 0.16*inch
    
    actions = period_data.get('actions', [])
    if actions:
        c.drawString(1.4*inch, y_position, "액션 플랜:")
        y_position -= 0.16*inch
        for action in actions[:3]:
            c.drawString(1.6*inch, y_position, f"• {action[:70]}")
            y_position -= 0.16*inch


def wrap_text(c, text, max_width, font_name, font_size):
    """텍스트를 지정된 너비에 맞게 줄바꿈"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, font_name, font_size) < max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines


# --- [수정] 함수를 직접 테스트할 때도 임시 데이터를 넣어줍니다 ---
if __name__ == "__main__":
    test_data = {
        "company_name": "XX(주)",
        "date": "2025.10.03"
    }
    create_prototype_report("test_report.pdf", test_data)