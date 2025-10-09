# 필요한 라이브러리들을 가져옵니다.
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm, inch
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT # 정렬 옵션
import datetime
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib import colors
from reportlab.graphics.charts.legends import Legend


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



"""
def create_prototype_report(buffer, report_data):
    '''전달받은 데이터를 기반으로 동적 PDF 리포트를 생성합니다.'''

    # 1. 도화지(Canvas)를 준비합니다.
    c = canvas.Canvas(buffer, pagesize=A4)
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
    print(f"'{buffer}' 파일이 성공적으로 생성되었습니다.")


# --- [수정] 함수를 직접 테스트할 때도 임시 데이터를 넣어줍니다 ---
if __name__ == "__main__":
    test_data = {
        "company_name": "XX(주)",
        "date": "2025.10.03"
    }
    create_prototype_report("test_report.pdf", test_data)

    """


def create_prototype_report(buffer, report_data):
    # 1. 문서 템플릿 생성
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    # 'Normal' 스타일을 기반으로 한글용 새 스타일을 만듭니다.
    korean_style = ParagraphStyle(
        name='KoreanNormal',      # 새 스타일의 이름 (아무거나 상관없음)
        parent=korean_style,  # 'Normal' 스타일의 속성을 모두 상속
        fontName='MalgunGothic'   # ✨ 폰트만 'MalgunGothic'으로 변경
    )
    # 기획서 제목 스타일 (볼드체, 24포인트, 가운데 정렬)
    title_style = ParagraphStyle(
        name='ReportTitle',
        fontName=FONT_NAME_BOLD,
        fontSize=24,
        alignment=TA_CENTER, # 가운데 정렬
        spaceAfter=20       # 문단 뒤에 여백 20 추가
    )
    # 부제목 스타일 (보통체, 12포인트, 왼쪽 정렬)
    subtitle_style = ParagraphStyle(
        name='ReportSubTitle',
        fontName=FONT_NAME,
        fontSize=12,
        alignment=TA_LEFT, # 왼쪽 정렬
        spaceAfter=10
    )
    subtitle_centered_style = ParagraphStyle(
        name='ReportSubTitle',
        fontName=FONT_NAME,
        fontSize=12,
        alignment=TA_CENTER, # 중앙 정렬
        spaceAfter=10
    )
    left_title_style = ParagraphStyle(name='Left', fontName=FONT_NAME, fontSize=10, alignment=TA_LEFT)
    center_title_style = ParagraphStyle(name='Center', fontName=FONT_NAME, fontSize=13, alignment=TA_CENTER)
    right_style = ParagraphStyle(name='Right', fontName=FONT_NAME, fontSize=10, alignment=TA_RIGHT)

    content_left = Paragraph("", left_title_style)
    content_center = Paragraph("Clara CS 분석 리포트", center_title_style)
    content_right = Paragraph(datetime.date.today().strftime("%Y.%m.%d"), right_style)

    # [ [첫째 칸, 둘째 칸, 셋째 칸] ]
    three_col_data = [[content_left, content_center, content_right]]

    available_width = A4[0] - 2 * inch 
    # 테이블 생성. 각 칸의 너비를 동일하게 1/3로 나눕니다.
    three_col_table = Table(three_col_data, colWidths=[
        available_width / 3, 
        available_width / 3, 
        available_width / 3
    ])

    three_col_table.setStyle(TableStyle([
    # 첫 번째 칸 (0,0) 내용을 왼쪽 정렬 ('LEFT')
    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
    
    # 두 번째 칸 (1,0) 내용을 가운데 정렬 ('CENTER')
    ('ALIGN', (1, 0), (1, 0), 'CENTER'),

    # 세 번째 칸 (2,0) 내용을 오른쪽 정렬 ('RIGHT')
    ('ALIGN', (2, 0), (2, 0), 'RIGHT'),

    # 모든 칸의 세로 정렬을 가운데('MIDDLE')로 맞춥니다.
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))



    story = []

    story.append(three_col_table)

    story.append(Paragraph("\n\r", subtitle_centered_style))
    story.append(Paragraph(report_data.get("company_name", "회사명 없음"), subtitle_centered_style))

    story.append(Paragraph("1. 분석한 데이터", korean_style))
    story.append(Paragraph("분석한 데이터를 나타냅니다.", korean_style))
    story.append(Paragraph("분석 데이터 15,150건", korean_style))
    story.append(Paragraph("채널별 데이터", korean_style))
    story.append(Paragraph("1:1 상담 105건 (11%) 해결률 88%", korean_style))
    story.append(Paragraph("전화상담 200건 (22%) 해결률 88%", korean_style))
    story.append(Paragraph("카카오톡 150건 (16.6%) 해결률 88%", korean_style))
    story.append(Paragraph("카테고리별 데이터", korean_style))
    story.append(Paragraph("배송 111건 (11%) 해결률 88%", korean_style))
    story.append(Paragraph("환불/취소 222건 (22%) 해결률 88%", korean_style))
    story.append(Paragraph("품질/하자 333건 (33%) 해결률 88%", korean_style))
    story.append(Paragraph("AS/설치 111건 (11%) 해결률 88%", korean_style))
    story.append(Paragraph("기타 111건 (11%) 해결률 88%", korean_style))
    story.append(Paragraph("", korean_style))
    story.append(Paragraph("2. 데이터 요약", korean_style))
    story.append(Paragraph("분석한 데이터를 보기 쉽게 요약한 내용입니다.", korean_style))
    story.append(Paragraph("날짜별 접수된 CS 건 수", korean_style))
    story.append(Paragraph("", korean_style))
    # 1. 차트를 그릴 도화지(Drawing) 만들기 (가로 400, 세로 200 크기)
    drawing = Drawing(width=400, height=200)

    # 2. 차트에 들어갈 데이터 (리스트 안에 리스트 형태)
    # [[10/1, 10/2, 10/3, ...]]
    data = [[10, 20, 25, 15, 30, 45, 22]]
    story.append(Paragraph("채널별 추이", korean_style))
    story.append(Paragraph("이 그래프는 날짜별로(가로) 각 채널별(색깔) 몇개의 CS가 들어왔는지 확인할 수 있는 세로형 누적 막대 그래프 입니다.", korean_style))

    trend_by_channel_chart = VerticalBarChart()
    # X축에 표시될 날짜 (카테고리)
    category_names = ['10/01', '10/02', '10/03', '10/04', '10/05', '10/06', '10/07']
    # 각 채널별, 날짜별 CS 인입 건수 (데이터 계열)
    # data = [ (전화 데이터), (1:1문의 데이터), (카카오톡 데이터), (이메일 데이터) ]
    data = [
        (30, 35, 40, 38, 42, 25, 20),   # '전화' 채널 데이터 (1층)
        (50, 55, 65, 60, 62, 40, 35),   # '1:1문의' 채널 데이터 (2층)
        (40, 42, 50, 45, 55, 30, 28),   # '카카오톡' 채널 데이터 (3층)
        (10, 12, 15, 11, 18, 5, 8),     # '이메일' 채널 데이터 (4층)
    ]

    # 각 채널의 이름과 색상 지정 (범례에 사용)
    channel_info = [
        {'name': '전화', 'color': colors.HexColor('#4A90E2')},
        {'name': '1:1문의', 'color': colors.HexColor('#50E3C2')},
        {'name': '카카오톡', 'color': colors.HexColor('#F8E71C')},
        {'name': '이메일', 'color': colors.HexColor('#B8E986')}
    ]


    # --- 2. 차트 생성 (데이터 적용) ---
    drawing = Drawing(width=500, height=250)
    chart = VerticalBarChart()


    # ✨ 핵심: 스타일을 'stacked'로 설정
    chart.categoryAxis.style = 'stacked'


    chart.x = 50
    chart.y = 50
    chart.height = 180
    chart.width = 380
    chart.data = data # 준비한 데이터 할당


    # X축 설정
    chart.categoryAxis.categoryNames = category_names # 날짜 데이터 할당

    # Y축 설정
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 200 # 모든 데이터의 합보다 넉넉하게 설정
    chart.valueAxis.valueStep = 50


    # 각 데이터 계열(채널)의 색상을 순서대로 적용
    for i, info in enumerate(channel_info):
        chart.bars[i].fillColor = info['color']

    
    # 범례(Legend) 추가
    legend = Legend()
    legend.x = 480
    legend.y = 220
    legend.alignment = 'right'
    legend.colorNamePairs = [(info['color'], info['name']) for info in channel_info]



    # 도화지에 차트와 범례 추가
    drawing.add(chart)
    drawing.add(legend)

    story.append(drawing)


    story.append(Paragraph("", korean_style))
    story.append(Paragraph("", korean_style))


    # 3. story의 내용으로 PDF 문서를 빌드합니다.
    doc.build(story)


# --- [수정] 함수를 직접 테스트할 때도 임시 데이터를 넣어줍니다 ---
if __name__ == "__main__":
    test_data = {
        "company_name": "XX(주)",
        "date": "2025.10.03"
    }
    create_prototype_report("test_report.pdf", test_data)
