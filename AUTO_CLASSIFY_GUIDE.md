# 자동 분류 기능 사용 가이드

## 📋 개요

ClaraCS의 자동 분류 기능은 업로드된 CS 티켓을 자동으로 카테고리별로 분류하는 기능입니다.

### 현재 구현 상태

- ✅ **규칙 기반 분류** (inquiry_type 필드 기반)
- ✅ DB 연동 완료
- ✅ 분류 결과 저장
- ✅ 집계 데이터 계산
- 🔜 **AI 기반 분류** (향후 구현 예정)

---

## 🚀 시작하기

### 1. DB 마이그레이션 실행

```bash
# 현재 DB 백업 (필수!)
mysqldump -u root -p clara_cs > clara_cs_backup_$(date +%Y%m%d).sql

# 마이그레이션 실행
mysql -u root -p clara_cs < database_migration_auto_classify.sql

# 변경사항 확인
mysql -u root -p clara_cs
> DESC tb_ticket;
> DESC tb_classification_result;
> SHOW INDEX FROM tb_ticket;
```

### 2. 코드성 데이터 삽입 (최초 1회)

```bash
mysql -u root -p clara_cs < database_insert_code_data.sql
```

이 스크립트는 다음 데이터를 생성합니다:

- 파일 확장자 코드 (csv, xlsx, xls)
- 컬럼 매핑 코드 (접수일, 채널, 본문 등)
- **카테고리 데이터** (배송 문의, 환불/교환, 상품 문의, 기술 지원, 불만/클레임, 기타)
- 테스트 사용자

### 3. 애플리케이션 재시작

```bash
# 개발 환경
python app.py

# 또는 프로덕션 환경 (gunicorn 등)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 📊 데이터 흐름

```
1. 파일 업로드
   ↓
   tb_uploaded_file에 파일 정보 저장
   ↓
   tb_ticket에 티켓 데이터 저장 (본문, 채널, inquiry_type 등)

2. 자동 분류 실행 (사용자가 버튼 클릭)
   ↓
   tb_ticket에서 file_id로 티켓 조회
   ↓
   RuleBasedClassifier로 각 티켓 분류
   ├─ inquiry_type 필드 매핑
   ├─ 본문/제목 키워드 분석
   └─ 카테고리 ID, 신뢰도, 키워드 반환
   ↓
   tb_ticket 업데이트 (classified_category_id, confidence, keywords)
   ↓
   tb_classification_result에 분류 실행 정보 저장
   ↓
   tb_classification_category_result에 카테고리별 집계 저장
   ↓
   tb_classification_channel_result에 채널별 집계 저장
   ↓
   tb_classification_reliability_result에 신뢰도 저장
   ↓
   프론트엔드에 JSON 응답 반환
```

---

## 🔧 규칙 기반 분류 로직

### inquiry_type 매핑 규칙

`utils/classifiers/rule_based_classifier.py`의 `inquiry_rules`에서 관리됩니다:

```python
{
    '배송': '배송 문의',
    '배송지연': '배송 문의',
    '환불': '환불/교환',
    '교환': '환불/교환',
    '상품문의': '상품 문의',
    'AS': '기술 지원',
    '불만': '불만/클레임',
    # ...
}
```

### 분류 우선순위

1. **inquiry_type 정확 매칭** (신뢰도 0.9)

   - inquiry_type이 매핑 규칙과 정확히 일치하는 경우

2. **inquiry_type 부분 매칭** (신뢰도 0.9)

   - inquiry_type에 매핑 규칙 키워드가 포함된 경우

3. **본문/제목 키워드 기반 추론** (신뢰도 0.5~0.8)

   - inquiry_type 매칭 실패 시 본문/제목의 키워드로 분류

4. **기타 카테고리** (신뢰도 0.5)
   - 모든 매칭 실패 시 '기타'로 분류

### 키워드 추출

카테고리별로 미리 정의된 키워드 패턴:

```python
keyword_patterns = {
    '배송 문의': ['배송', '택배', '운송', '배달', '지연', '추적', '도착'],
    '환불/교환': ['환불', '교환', '반품', '취소', '결제', '승인', '카드'],
    '상품 문의': ['상품', '제품', '스펙', '정보', '재고', '가격', '할인'],
    # ...
}
```

---

## 🧪 테스트 방법

### 1. 샘플 데이터 업로드

`uploads/` 폴더에 있는 샘플 파일을 사용하거나, 아래 형식의 CSV/Excel 파일을 준비:

```csv
접수일,채널,고객ID,상품코드,문의 유형,제목,본문,담당자,처리 상태
2025-10-01,챗봇,C001,P001,배송,배송이 늦어요,주문한 상품이 아직 도착하지 않았습니다,김철수,처리중
2025-10-02,전화,C002,P002,환불,환불 요청,단순변심으로 환불하고 싶습니다,이영희,완료
2025-10-03,이메일,C003,P003,상품문의,재고 확인,이 상품 재고 있나요?,박민수,신규
```

### 2. 자동 분류 실행

**방법 A: 웹 UI**

1. http://localhost:5000/classify 접속
2. "분류 실행" 버튼 클릭
3. 결과 확인

**방법 B: API 직접 호출**

```bash
curl -X POST http://localhost:5000/api/classifications/run \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "file_id": 1}'
```

### 3. 결과 확인

```sql
-- 분류된 티켓 확인
SELECT
    ticket_id,
    inquiry_type,
    classified_category_id,
    classification_confidence,
    classification_keywords
FROM tb_ticket
WHERE file_id = 1
LIMIT 10;

-- 분류 실행 이력
SELECT * FROM tb_classification_result
ORDER BY classified_at DESC;

-- 카테고리별 집계
SELECT
    cr.class_result_id,
    c.category_name,
    ccr.count,
    ccr.ratio,
    ccr.example_keywords
FROM tb_classification_category_result ccr
JOIN tb_classification_result cr ON ccr.class_result_id = cr.class_result_id
JOIN tb_category c ON ccr.category_id = c.category_id
WHERE cr.file_id = 1;
```

---

## 🎯 향후 AI 분류 구현 가이드

### 준비된 구조

`utils/classifiers/ai_classifier.py` 파일이 준비되어 있습니다.

### 구현 예시

```python
from utils.classifiers import AIClassifier

# AI 분류기 초기화
ai_classifier = AIClassifier(model_name='gpt-4', api_key='your-api-key')

# services/auto_classify.py에서 분류기 교체
self.classifier = ai_classifier  # RuleBasedClassifier 대신
```

### 구현해야 할 메서드

1. **`classify_ticket()`**

   - OpenAI/Anthropic API 호출
   - 프롬프트 엔지니어링
   - 응답 파싱

2. **`classify_batch()`** (선택)
   - 병렬 처리로 성능 최적화
   - Rate limiting 처리

### 프롬프트 예시

```python
prompt = f"""
다음 CS 티켓을 아래 카테고리 중 하나로 분류하세요.

제목: {ticket['title']}
본문: {ticket['body']}
채널: {ticket['channel']}

카테고리:
1. 배송 문의: 배송, 택배, 운송 관련
2. 환불/교환: 환불, 교환, 반품 요청
3. 상품 문의: 상품 정보, 재고, 가격
4. 기술 지원: 사용법, 고장, A/S
5. 불만/클레임: 불만 사항, 품질 문제
6. 기타: 기타 문의

JSON 형식으로 응답:
{{
  "category": "카테고리명",
  "confidence": 0.95,
  "keywords": ["키워드1", "키워드2"],
  "reason": "분류 이유"
}}
"""
```

---

## 🛠️ 커스터마이징

### 1. 카테고리 추가

```sql
-- 새 대분류 카테고리 추가
INSERT INTO tb_category (category_name, parent_category_id, description)
VALUES ('결제 문의', NULL, '결제 및 영수증 관련');
```

`utils/classifiers/rule_based_classifier.py` 업데이트:

```python
self.inquiry_rules['결제'] = '결제 문의'
self.keyword_patterns['결제 문의'] = ['결제', '영수증', '카드', '승인']
```

### 2. 매핑 규칙 수정

`utils/classifiers/rule_based_classifier.py`의 `_build_inquiry_rules()` 메서드에서 수정:

```python
def _build_inquiry_rules(self):
    return {
        # 기존 규칙
        '배송': '배송 문의',

        # 새 규칙 추가
        '배송확인': '배송 문의',
        '택배추적': '배송 문의',
        # ...
    }
```

### 3. 신뢰도 임계값 조정

`services/auto_classify.py`의 `_calculate_importance()` 메서드:

```python
def _calculate_importance(self, confidence: float) -> str:
    if confidence >= 0.95:  # 0.9 → 0.95로 변경
        return '상'
    elif confidence >= 0.80:  # 0.7 → 0.80으로 변경
        return '중'
    else:
        return '하'
```

---

## ❓ 문제 해결

### Q1. "카테고리 데이터가 없습니다" 오류

**원인:** `database_insert_code_data.sql`을 실행하지 않음

**해결:**

```bash
mysql -u root -p clara_cs < database_insert_code_data.sql
```

### Q2. "분류할 티켓이 없습니다" 메시지

**원인:** 해당 file_id에 티켓이 없음

**확인:**

```sql
SELECT COUNT(*) FROM tb_ticket WHERE file_id = 1;
```

**해결:** 데이터 업로드 먼저 수행

### Q3. 모든 티켓이 '기타'로 분류됨

**원인:** inquiry_type 필드가 비어있거나 매핑 규칙과 일치하지 않음

**해결:**

1. inquiry_type 데이터 확인

   ```sql
   SELECT DISTINCT inquiry_type FROM tb_ticket WHERE file_id = 1;
   ```

2. 매핑 규칙 추가
   ```python
   # utils/classifiers/rule_based_classifier.py
   self.inquiry_rules['새로운유형'] = '적절한 카테고리'
   ```

### Q4. 성능이 느림

**원인:** 인덱스 미적용 또는 대량 데이터

**해결:**

1. 마이그레이션 SQL 실행 확인
2. 인덱스 존재 확인

   ```sql
   SHOW INDEX FROM tb_ticket;
   ```

3. 배치 처리 크기 조정 가능 (향후 최적화)

---

## 📚 관련 파일

### 핵심 파일

- `services/auto_classify.py`: 자동 분류 비즈니스 로직
- `services/db/auto_classify_db.py`: DB 작업
- `utils/classifiers/rule_based_classifier.py`: 규칙 기반 분류 엔진
- `utils/classifiers/ai_classifier.py`: AI 분류 엔진 (향후 구현)

### DB 파일

- `database_schema.sql`: 전체 DB 스키마
- `database_migration_auto_classify.sql`: 마이그레이션 SQL
- `database_insert_code_data.sql`: 코드성 데이터

### 프론트엔드

- `templates/classify.html`: 자동 분류 페이지
- `static/js/auto_classify.js`: 프론트엔드 로직

---

## 📞 지원

문제가 발생하면 로그를 확인하세요:

```python
# utils/logger.py에서 로그 레벨 조정
logger.setLevel(logging.DEBUG)
```

로그 위치는 애플리케이션 설정에 따라 다를 수 있습니다.
