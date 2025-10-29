import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage 
from email import encoders
from email.utils import formataddr
from email.header import Header
from config import Config
from datetime import datetime

def send_email_with_pdf(to_email, pdf_buffer, filename=None):

    msg = MIMEMultipart('related')
    msg['From'] = formataddr((str(Header("TEAM.CLARA", "utf-8")), Config.SMTP_USER))
    msg['To'] = to_email
    msg['Subject'] = 'ClaraCS AI 분석 리포트'


    html_content = """
    <html>
        <body>
            <p>ClaraCS AI 분석 리포트(PDF)가 첨부되어 있습니다.<br>
            첨부된 리포트를 검토하시어 분석 결과와 주요 인사이트, 그리고 ClaraCS가 제안 드리는 솔루션을 참고하시기 바랍니다.</p>
            <br><br><br><br><br><br><br><br><br>
            <p>TEAM.CLARA</p>
            <p><img src="cid:clara_image" width="240"></p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    now = datetime.now()
    timestamp = now.strftime("%Y.%m.%d.%H:%M")
    filename = f"{timestamp}_ClaraCS AI 분석 리포트.pdf"

    try:
        pdf_buffer.seek(0)  # 처음 위치로 이동
    except Exception as e:
        print(f"[WARN] pdf_buffer.seek(0) 실패: {e}")

    part = MIMEBase('application', 'pdf') 
    part.set_payload(pdf_buffer.read())
    encoders.encode_base64(part)

    part.add_header(
        'Content-Disposition',
        'attachment',
        filename=str(Header(filename, 'utf-8'))
    )

    msg.attach(part)

    # 이미지 첨부
    image_path = 'static/images/ClaraCS_email.jpg'
    try:
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
            image_part = MIMEImage(img_data)
            image_part.add_header('Content-ID', '<clara_image>')
            image_part.add_header(
                'Content-Disposition',
                'inline',
                filename=str(Header('ClaraCS_email.jpg', 'utf-8'))
            )
            msg.attach(image_part)
    except Exception as e:
        print(f"[ERROR] 이미지 첨부 실패: {e}")

    with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
        server.starttls()
        server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        server.send_message(msg)