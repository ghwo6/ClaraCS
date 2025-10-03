# generate_cs_dummy_v3_nopandas.py
# -*- coding: utf-8 -*-
"""
Generate CS dummy dataset (v3, no external deps)
- 500 rows
- 9 columns: received_date, serial_number, source, customer_email, category, title, message, agent_name, status
- message <= 100 chars, all unique; and first 7 chars (prefix) unique across all rows
- Date range: 2025-07-01 ~ 2025-09-30
"""

import csv, json, random, string
from datetime import datetime, timedelta

def generate(n_rows=500, seed=303):
    random.seed(seed)

    sources = ["1:1문의게시판","챗봇문의","전화상담","이메일상담","SNS 상담","자율게시판"]
    source_weights = [0.24,0.2,0.16,0.2,0.1,0.1]

    categories = {
        "배송문의": ["배송 지연", "오배송", "배송 상태 불만"],
        "상품문의": ["품질 문제", "사이즈/규격", "색상/디자인", "단순 변심"],
        "결제/환불문의": ["환불 관련", "할인/쿠폰 문제", "결제 관련"],
        "계정/서비스문의": ["회원 관련", "서비스 이용"],
        "기타문의": ["제품 정보 요청", "AS/보증 관련", "기타 건의/제안"],
    }

    status_choices = ["대기","완료","진행중"]
    status_weights = [0.22,0.48,0.30]

    agents = [
        "김민수","이서연","박지훈","최유진","정예원",
        "장하늘","윤도현","서민지","오지민","한수진",
        "정민호","문정연","강태현","조은별","유지호",
        "배가은","임세진","권민재","신예린","노유진",
    ]

    products = [
        ("스트라이프티셔츠_free", 10001),
        ("반다나_블랙", 30001),
        ("반다나_레드", 30002),
        ("후드티_90", 11090),
        ("후드티_100", 11100),
        ("후드티_110", 11110),
        ("카고팬츠_s", 20001),
        ("카고팬츠_m", 20002),
        ("카고팬츠_L", 20003),
    ]
    product_weights = [0.12,0.1,0.1,0.12,0.14,0.12,0.1,0.1,0.1]

    start_date = datetime(2025,7,1)
    end_date = datetime(2025,9,30)
    def rand_date_str():
        span = (end_date - start_date).days
        d = start_date + timedelta(days=random.randint(0, span))
        return d.strftime("%Y-%m-%d")

    openings = {
        "배송 지연": ["예상보다 배송이 늦어","도착 일정이 궁금하여","수령일 안내 요청","발송 여부 확인 필요","배송 지연으로 문의"],
        "오배송": ["수령 상품이 다릅니다","주문과 다른 물건 수령","오배송 건 접수","교환 필요한 오배송","상품이 바뀌어 문의"],
        "배송 상태 불만": ["상자 파손으로 우려","포장 눌림 확인","외관 손상 때문에","택배 포장 문제","배송 상태가 좋지 않아"],
        "품질 문제": ["품질 이슈 발견","초기불량 의심","하자 확인 요청","불량 증상 문의","수령 직후 이상"],
        "사이즈/규격": ["사이즈가 안내와 달라","실측이 표기와 달라","규격 문의","치수 차이로 교환","착용감이 타이트"],
        "색상/디자인": ["색감이 상세와 달라","디자인 배치 차이","사진 대비 색상 오차","색상 교환 문의","디자인 관련 문의"],
        "단순 변심": ["마음이 바뀌어 반품","미개봉 상태로 교환","선물용이 맞지 않아","스타일이 달라 환불","변심으로 처리 요청"],
        "환불 관련": ["환불 진행 상태 문의","입금 지연 확인 요청","환불 금액 검토","환불 처리 일정 확인","환불 관련 문의"],
        "할인/쿠폰 문제": ["쿠폰 적용 실패","프로모션 반영 안 됨","할인 혜택 미적용","앱/웹 할인 불일치","쿠폰 사용 오류"],
        "결제 관련": ["이중결제 의심","간편결제 중단","무이자 청구 불일치","결제 오류 확인","결제 상태 모호"],
        "회원 관련": ["로그인 문제 발생","회원정보 저장 실패","휴면 해제 후 문제","비밀번호 재설정 실패","계정 관련 문의"],
        "서비스 이용": ["앱 오류 반복","페이지 로딩 지연","알림 과다 수신","사용법 안내 필요","접속 불편 지속"],
        "제품 정보 요청": ["재입고 일정 문의","소재·세탁 정보 문의","제조국/보증 안내 요청","상세 스펙 확인","입고 계획 문의"],
        "AS/보증 관련": ["무상 AS 가능 여부를 확인 부탁드립니다.","절차와 소요 기간을 안내해 주세요.","왕복 배송비 기준이 궁금합니다.","사진을 첨부했습니다.","접수 방법을 알려주세요."],
        "기타 건의/제안": ["검토해 주시면 감사하겠습니다.","향후 반영 계획이 궁금합니다.","사용자 경험 향상에 도움이 될 것 같습니다.","내부 공유 부탁드립니다.","건의사항 전달드립니다."],
    }

    title_map = {
        "배송 지연": ["배송 지연 문의","도착 일정 문의","언제 받을까요"],
        "오배송": ["오배송 처리요청","다른 상품 수령","교환 요청"],
        "배송 상태 불만": ["포장/파손 불만","상자 파손 문의","배송 상태 불만"],
        "품질 문제": ["품질 이슈 문의","하자 발생 문의","불량 의심"],
        "사이즈/규격": ["사이즈 문의","실측/규격 확인","사이즈 교환 문의"],
        "색상/디자인": ["색상/디자인 문의","색 차이 문의","디자인 관련"],
        "단순 변심": ["변심 반품 문의","교환 원합니다","환불/반품 문의"],
        "환불 관련": ["환불 문의","환불 진행 확인","환불 지연"],
        "할인/쿠폰 문제": ["쿠폰 오류","프로모션 문의","할인 미적용"],
        "결제 관련": ["결제 오류","이중결제 의심","결제 수단 문의"],
        "회원 관련": ["계정/로그인 문제","비밀번호/정보 수정","회원 관련 문의"],
        "서비스 이용": ["앱/웹 오류","사용법 문의","접속 불편"],
        "제품 정보 요청": ["제품 정보 요청","재고/입고 문의","소재/세탁 문의"],
        "AS/보증 관련": ["AS/보증 문의","수선 가능 문의","지퍼/수선 문의"],
        "기타 건의/제안": ["서비스 건의","불편 개선 제안","기타 의견"],
    }

    def order_code():
        return "OD-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    def lead_phrase(i):
        choices = []
        m = random.choice([7,8,9]); d = random.randint(1,28)
        h = random.randint(8,21); minute = random.randint(0,59)
        choices.append(f"{m}/{d} 주문 ")
        choices.append(f"{h:02}:{minute:02} 접수 ")
        choices.append(f"{m}월 구매건 ")
        choices.append(f"최근 주문 {d} ")
        choices += ["앱 결제 건 ", "웹 결제 건 ", "전화 접수 건 ", "재구매 건 ", "첫 구매 건 "]
        return random.choice(choices)

    def make_message(reason, pname, pcode, i):
        op = random.choice(openings[reason])
        cont = random.choice([
            "현재 위치와 도착 예정일 안내 부탁드립니다.", "금주 수령 가능 여부가 궁금합니다.", "배송 현황이 멈춰 있어 확인 바랍니다.",
            "지연 사유와 대안 일정을 부탁드립니다.", "빠른 확인 요청드립니다.",
            "교환 또는 재배송 절차를 안내해 주세요.", "회수 후 재배송 부탁드립니다.", "사진 첨부했고 빠른 교환 요청드립니다.",
            "반품 없이 교환 가능할까요?", "정확한 상품으로 다시 보내주세요.",
            "제품 손상 가능성이 있어 조치 부탁드립니다.", "재포장 교환 또는 보상 기준 안내 바랍니다.", "내부 구성품 확인이 필요합니다.",
            "파손 정도 확인 후 대응 부탁드립니다.", "재발 방지 방안도 알려주세요.",
            "교환 또는 점검이 필요합니다.", "초기불량 처리 가능 여부가 궁금합니다.", "사진과 함께 접수했습니다.",
            "AS가 적절한지 판단 부탁드립니다.", "빠른 확인 부탁드립니다.",
            "한 치수 교환 가능할까요?", "교환 시 배송비 기준을 알려주세요.", "상세 치수 재안내 바랍니다.",
            "반품/교환 절차를 안내해 주세요.", "다른 사이즈 재고를 확인 부탁드립니다.",
            "교환 또는 반품 안내 부탁드립니다.", "정상 범주인지 확인 바랍니다.", "색상 교환이 가능한지 알고 싶습니다.",
            "반품 기준과 절차를 알려주세요.", "사진 비교를 검토 부탁드립니다.",
            "절차와 비용을 안내해 주세요.", "반품 가능 여부를 확인 부탁드립니다.", "교환 가능하면 진행하고 싶습니다.",
            "환불로 진행하려 합니다.", "택배 수거가 가능한지 궁금합니다.",
            "처리 일정과 금액을 확인 부탁드립니다.", "내역 검토 후 안내 부탁드립니다.", "언제 입금되는지 궁금합니다.",
            "환불 방식 변경이 가능할까요?", "지연 사유를 알려주세요.",
            "조건을 충족했는데 반영되지 않았습니다.", "사후 적용이 가능한지 문의드립니다.", "원인 확인과 재적용을 부탁드립니다.",
            "동일 조건에서 웹/앱 차이가 있습니다.", "결제 중 에러가 발생했습니다.",
            "취소 및 정정 처리를 부탁드립니다.", "주문 상태 확인이 필요합니다.", "청구서와 안내가 달라 보입니다.",
            "결제 내역 확인 부탁드립니다.", "재결제 없이 해결될까요?",
            "원인 확인과 조치를 부탁드립니다.", "정보 변경이 반영되지 않습니다.", "주문 내역 복구가 필요합니다.",
            "계정 보안 점검도 부탁드립니다.", "연락처 변경을 도와주세요.",
            "재현 방법을 안내드릴 수 있습니다.", "개선 가능 여부를 알려주세요.", "설정 방법을 알려주시면 감사하겠습니다.",
            "브라우저/앱 모두 동일합니다.", "오류 코드 공유 가능합니다.",
            "색상별 입고 일정도 부탁드립니다.", "손세탁 가능 여부가 궁금합니다.", "보증기간도 함께 안내 부탁드립니다.",
            "상세 스펙 문서를 받을 수 있을까요?", "출고 일정이 있다면 알려주세요.",
            "무상 AS 가능 여부를 확인 부탁드립니다.", "절차와 소요 기간을 안내해 주세요.", "왕복 배송비 기준이 궁금합니다.",
            "사진을 첨부했습니다.", "접수 방법을 알려주세요.",
            "검토해 주시면 감사하겠습니다.", "향후 반영 계획이 궁금합니다.", "사용자 경험 향상에 도움이 될 것 같습니다.",
            "내부 공유 부탁드립니다.", "건의사항 전달드립니다."
        ])
        detail = random.choice([f"{pname}({pcode})", f"{pname}", "해당 주문"])
        msg = f"{lead_phrase(i)}{op} {detail}. {cont}"
        if random.random() < 0.3:
            msg += f" 주문번호 {order_code()}."
        return msg[:100] if len(msg) > 100 else msg

    rows = []
    prefix7_seen = set()
    messages_seen = set()
    repeat_emails = [f"repeat{idx}@example.com" for idx in range(1,13)]

    for i in range(n_rows):
        received_date = rand_date_str()
        pname, pcode = random.choices(products, weights=product_weights, k=1)[0]
        category = random.choice(list(categories.keys()))
        reason = random.choice(categories[category])
        title = random.choice(title_map[reason])[:20]
        source = random.choices(sources, weights=source_weights, k=1)[0]
        status = random.choices(status_choices, weights=status_weights, k=1)[0]
        agent = random.choice(agents)

        tries = 0
        while True:
            message = make_message(reason, pname, pcode, i + tries)
            pre7 = message[:7]
            if pre7 not in prefix7_seen and message not in messages_seen:
                prefix7_seen.add(pre7)
                messages_seen.add(message)
                break
            tries += 1
            if tries > 60:
                addon = random.choice([" 오늘 접수했습니다."," 사진 첨부했습니다."," 고객센터 연결이 어려웠습니다."," 빠른 회신 부탁드립니다."])
                message = (message[: max(0, 100 - len(addon))] + addon)
                pre7 = message[:7]
                if pre7 not in prefix7_seen and message not in messages_seen:
                    prefix7_seen.add(pre7)
                    messages_seen.add(message)
                    break

        if i < 40:
            customer_email = repeat_emails[i % len(repeat_emails)]
        else:
            customer_email = f"user{i}{random.choice('abcxyz')}{random.randint(100,999)}@" + \
                             random.choice(["example.com","mail.com","shopper.net","customer.io"])

        rows.append({
            "received_date": received_date,
            "serial_number": pcode,
            "source": source,
            "customer_email": customer_email,
            "category": category,
            "title": title,
            "message": message,
            "agent_name": agent,
            "status": status,
        })

    csv_path = "cs_dummy_data_v3_500_prefix7uniq.csv"
    json_path = "cs_dummy_data_v3_500_prefix7uniq.json"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["received_date","serial_number","source","customer_email","category","title","message","agent_name","status"])
        w.writeheader()
        w.writerows(rows)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("Saved:", csv_path, "/", json_path)

if __name__ == "__main__":
    generate()
