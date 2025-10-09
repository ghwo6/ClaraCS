# 자동 분류 로직 상세 설명

## 📋 목차

1. [전체 흐름 개요](#전체-흐름-개요)
2. [단계별 상세 설명](#단계별-상세-설명)
3. [규칙 기반 분류 로직](#규칙-기반-분류-로직)
4. [AI 기반 분류 로직](#ai-기반-분류-로직)
5. [데이터 저장 구조](#데이터-저장-구조)

---

## 전체 흐름 개요

```
사용자가 "분류 실행" 버튼 클릭
    ↓
[1단계] DB에서 티켓 조회 (file_id 기준)
    ↓
[2단계] 각 티켓을 하나씩 분류
    ├─ 규칙 기반: inquiry_type + 키워드 매칭
    └─ AI 기반: Hugging Face 모델 추론
    ↓
[3단계] 분류 결과를 각 티켓에 저장 (tb_ticket 업데이트)
    ├─ classified_category_id
    ├─ classification_confidence
    ├─ classification_keywords
    └─ classified_at
    ↓
[4단계] 전체 집계 계산
    ├─ 카테고리별 집계 (tb_classification_category_result)
    ├─ 채널별 집계 (tb_classification_channel_result)
    └─ 신뢰도 통계 (tb_classification_reliability_result)
    ↓
[5단계] 프론트엔드로 JSON 응답
    ├─ 카테고리별 통계
    ├─ 채널별 도넛 차트 데이터
    ├─ 신뢰도 정보
    └─ 티켓 샘플 (카테고리별 상위 3개)
```

---

## 단계별 상세 설명

### **1단계: DB에서 티켓 조회**

**파일:** `services/db/auto_classify_db.py`

```python
def get_tickets_by_file(self, file_id: int) -> List[Dict]:
    """
    특정 파일에 속한 모든 티켓 조회

    SELECT ticket_id, body, title, inquiry_type, channel, received_at
    FROM tb_ticket
    WHERE file_id = ?
    ORDER BY received_at DESC
    """
```

**예시:**

```python
tickets = [
    {
        'ticket_id': 1001,
        'body': '배송이 너무 늦어요',
        'title': '배송 문의',
        'inquiry_type': '배송',
        'channel': '챗봇',
        'received_at': '2025-10-01'
    },
    {
        'ticket_id': 1002,
        'body': '환불하고 싶어요',
        'title': '환불 요청',
        'inquiry_type': '환불',
        'channel': '전화',
        'received_at': '2025-10-02'
    },
    # ... 500건
]
```

---

### **2단계: 각 티켓 분류**

**파일:** `services/auto_classify.py` (70~85줄)

```python
for ticket in tickets:
    # 분류기(규칙 기반 또는 AI)로 분류
    result = self.classifier.classify_ticket(ticket)

    classification_results.append({
        'ticket_id': ticket['ticket_id'],
        'classification': result
    })

    # 즉시 DB에 저장
    self.db.update_ticket_classification(ticket['ticket_id'], result)
```

---

## 규칙 기반 분류 로직

**파일:** `utils/classifiers/rule_based_classifier.py`

### **흐름도**

```
티켓 입력
    ↓
[Step 1] inquiry_type 필드 확인
    ├─ "배송" → "배송 문의" (신뢰도 0.9) ✓
    ├─ "환불" → "환불/교환" (신뢰도 0.9) ✓
    └─ 없음/매칭 실패 → Step 2로
    ↓
[Step 2] 본문/제목에서 키워드 검색
    ├─ "배송", "택배" 발견 → "배송 문의" (신뢰도 0.5~0.8)
    ├─ "환불", "취소" 발견 → "환불/교환" (신뢰도 0.5~0.8)
    └─ 키워드 없음 → Step 3로
    ↓
[Step 3] 기본값
    └─ "기타" (신뢰도 0.5)
    ↓
결과 반환: {category_id, category_name, confidence, keywords}
```

### **상세 코드 설명**

#### **Step 1: inquiry_type 매핑**

```python
# 미리 정의된 매핑 규칙
inquiry_rules = {
    '배송': '배송 문의',
    '배송지연': '배송 문의',
    '택배': '배송 문의',
    '환불': '환불/교환',
    '교환': '환불/교환',
    '취소': '환불/교환',
    'AS': '기술 지원',
    '불만': '불만/클레임',
    # ...
}

# inquiry_type이 "배송"이면
if inquiry_type == '배송':
    category_name = inquiry_rules['배송']  # '배송 문의'
    confidence = 0.9
    matched_keywords = ['배송']
```

**예시:**

```python
티켓 = {'inquiry_type': '배송지연', 'body': '택배가 너무 늦어요'}
    ↓
inquiry_rules['배송지연'] = '배송 문의'
    ↓
결과: category_name='배송 문의', confidence=0.9, keywords=['배송지연']
```

#### **Step 2: 키워드 기반 분류**

```python
# 카테고리별 대표 키워드 (미리 정의)
keyword_patterns = {
    '배송 문의': ['배송', '택배', '운송', '배달', '지연', '추적', '도착'],
    '환불/교환': ['환불', '교환', '반품', '취소', '결제', '승인', '카드'],
    '상품 문의': ['상품', '제품', '스펙', '정보', '재고', '가격', '할인'],
    '기술 지원': ['사용법', '고장', 'AS', '수리', '설치'],
    '불만/클레임': ['불만', '클레임', '화남', '불량', '파손', '품질'],
    '기타': ['문의', '확인', '안내', '질문']
}

# 본문 분석
text = body + ' ' + title  # "배송이 너무 늦어요 택배 추적이 안돼요"

# 각 카테고리별로 키워드 매칭 횟수 계산
category_scores = {}
for category, keywords in keyword_patterns.items():
    score = 0
    matched = []
    for keyword in keywords:
        if keyword in text:
            score += 1
            matched.append(keyword)

    if score > 0:
        category_scores[category] = score
        category_matched_keywords[category] = matched

# 가장 많이 매칭된 카테고리 선택
# category_scores = {'배송 문의': 3}  # '배송', '택배', '추적' 3개 매칭
best_category = '배송 문의'
confidence = 0.5 + (3 * 0.1) = 0.8
matched_keywords = ['배송', '택배', '추적']
```

**예시:**

```python
티켓 = {
    'inquiry_type': None,  # inquiry_type이 없음
    'body': '배송이 너무 늦어요. 택배 추적이 안됩니다.'
}
    ↓
텍스트 분석: "배송이 너무 늦어요. 택배 추적이 안됩니다."
    ↓
키워드 매칭:
  - '배송 문의': ['배송', '택배', '추적'] → 3개 매칭 ✓
  - '환불/교환': [] → 0개
  - '상품 문의': [] → 0개
    ↓
결과: category='배송 문의', confidence=0.8, keywords=['배송', '택배', '추적']
```

#### **Step 3: 기본값 (기타)**

```python
if not category_name:
    category_name = '기타'
    confidence = 0.5
    matched_keywords = ['미분류']
```

---

## AI 기반 분류 로직

**파일:** `utils/classifiers/ai_classifier.py`

### **흐름도**

```
티켓 입력
    ↓
[Step 1] Hugging Face 모델 로딩 (최초 1회)
    ├─ beomi/kcbert-base (한국어 BERT)
    └─ Zero-shot classification 파이프라인
    ↓
[Step 2] 텍스트 준비
    └─ text = title + " " + body (최대 500자)
    ↓
[Step 3] AI 모델 추론
    ├─ 입력: "배송이 너무 늦어요"
    ├─ 후보 카테고리: ['배송 문의', '환불/교환', '상품 문의', ...]
    └─ 출력: [
          {'label': '배송 문의', 'score': 0.92},
          {'label': '환불/교환', 'score': 0.05},
          {'label': '상품 문의', 'score': 0.02},
          ...
        ]
    ↓
[Step 4] 최고 점수 카테고리 선택
    └─ category='배송 문의', confidence=0.92
    ↓
[Step 5] 키워드 확인 (선택)
    └─ 본문에서 해당 카테고리 키워드 추출
    ↓
결과 반환
```

### **상세 코드 설명**

```python
def classify_ticket(self, ticket):
    # 1. 모델 로딩 (지연 로딩)
    if not self.pipeline:
        self.pipeline = pipeline(
            "zero-shot-classification",
            model='beomi/kcbert-base',
            device=0 if torch.cuda.is_available() else -1
        )

    # 2. 텍스트 준비
    text = f"{ticket['title']} {ticket['body']}".strip()[:500]

    # 3. Zero-shot classification 실행
    result = self.pipeline(
        text,
        candidate_labels=['배송 문의', '환불/교환', '상품 문의', '기술 지원', '불만/클레임', '기타'],
        hypothesis_template="이 문의는 {}에 관한 것이다."  # 한국어 템플릿
    )

    # 4. 결과 파싱
    # result = {
    #     'labels': ['배송 문의', '환불/교환', '상품 문의', ...],
    #     'scores': [0.92, 0.05, 0.02, ...]
    # }

    best_label = result['labels'][0]      # '배송 문의'
    best_score = result['scores'][0]      # 0.92

    return {
        'category_id': category_id,
        'category_name': best_label,
        'confidence': float(best_score),
        'keywords': extracted_keywords,
        'method': 'ai_huggingface'
    }
```

**예시:**

```python
티켓 = {
    'title': '배송 문의',
    'body': '주문한 상품이 아직 도착하지 않았는데 언제 오나요?'
}
    ↓
BERT 모델 추론:
  입력: "배송 문의 주문한 상품이 아직 도착하지 않았는데 언제 오나요?"
  후보: ['배송 문의', '환불/교환', '상품 문의', '기술 지원', '불만/클레임', '기타']
    ↓
AI 추론 결과:
  1위: 배송 문의 (92%)
  2위: 상품 문의 (5%)
  3위: 기타 (2%)
    ↓
최종 결과: category='배송 문의', confidence=0.92
```

---

## 3단계: 분류 결과 저장

### **개별 티켓 업데이트**

**파일:** `services/db/auto_classify_db.py` (108~139줄)

```python
def update_ticket_classification(ticket_id, classification):
    """
    UPDATE tb_ticket
    SET classified_category_id = ?,
        classification_confidence = ?,
        classification_keywords = ?,
        classified_at = NOW()
    WHERE ticket_id = ?
    """
```

**예시:**

```sql
-- ticket_id=1001
UPDATE tb_ticket
SET classified_category_id = 1,          -- 배송 문의
    classification_confidence = 0.9,
    classification_keywords = '["배송", "지연"]',
    classified_at = '2025-10-05 10:00:00'
WHERE ticket_id = 1001;
```

### **분류 실행 메타 정보 저장**

```python
# tb_classification_result 테이블
{
    'class_result_id': 1,
    'file_id': 123,
    'user_id': 1,
    'engine_name': 'rule_based_v1',  # 또는 'ai_huggingface_kcbert-base'
    'total_tickets': 500,
    'period_from': '2025-09-01',
    'period_to': '2025-09-30',
    'classified_at': '2025-10-05 10:00:00'
}
```

---

## 4단계: 집계 데이터 계산

### **카테고리별 집계**

**파일:** `services/auto_classify.py` (122~154줄)

```python
# 모든 티켓의 분류 결과를 카테고리별로 집계
category_counts = defaultdict(int)
category_keywords = defaultdict(set)

for item in classification_results:
    cls = item['classification']
    cat_id = cls['category_id']

    # 카운트 증가
    category_counts[cat_id] += 1

    # 키워드 수집 (중복 제거)
    for kw in cls.get('keywords', []):
        category_keywords[cat_id].add(kw)

# 결과 생성
results = []
total = len(tickets)
for cat_id, count in category_counts.items():
    results.append({
        'category_id': cat_id,
        'category_name': category_mapping[cat_id],
        'count': count,
        'ratio': count / total,
        'keywords': list(category_keywords[cat_id])[:10]
    })
```

**예시:**

```python
# 500건의 티켓 분류 결과
[
    {'category': '배송 문의', 'count': 210, 'ratio': 0.42, 'keywords': ['배송', '지연', '택배', '추적']},
    {'category': '환불/교환', 'count': 150, 'ratio': 0.30, 'keywords': ['환불', '취소', '반품']},
    {'category': '상품 문의', 'count': 100, 'ratio': 0.20, 'keywords': ['상품', '재고', '가격']},
    {'category': '기술 지원', 'count': 30, 'ratio': 0.06, 'keywords': ['AS', '수리']},
    {'category': '기타', 'count': 10, 'ratio': 0.02, 'keywords': ['문의']}
]
```

### **채널별 집계**

```python
# 채널 + 카테고리 조합별 카운트
channel_category_counts = defaultdict(lambda: defaultdict(int))

for item in classification_results:
    ticket = ticket_map[item['ticket_id']]
    channel = ticket['channel']      # '챗봇'
    cat_id = item['classification']['category_id']  # 1

    channel_category_counts[channel][cat_id] += 1

# 결과: {'챗봇': {1: 80, 2: 50}, '전화': {1: 60, 2: 40}, ...}
```

**예시:**

```python
[
    {
        'channel': '챗봇',
        'category_id': 1,  # 배송 문의
        'count': 80,
        'ratio': 0.35      # 챗봇 전체 중 35%
    },
    {
        'channel': '챗봇',
        'category_id': 2,  # 환불/교환
        'count': 50,
        'ratio': 0.22
    },
    # ...
]
```

---

## 5단계: 프론트엔드 응답

**파일:** `services/auto_classify.py` (210~264줄)

```python
response = {
    'return_code': 1,
    'class_result_id': 1,
    'period': {'from': '2025-09-01', 'to': '2025-09-30'},
    'meta': {
        'user_id': 1,
        'file_id': 123,
        'total_tickets': 500,
        'classified_at': '2025-10-05T10:00:00',
        'engine_name': 'rule_based_v1'  # 또는 'ai_huggingface_kcbert-base'
    },
    'category_info': [
        {'category': '배송 문의', 'count': 210, 'ratio': 0.42, 'keywords': [...]},
        # ...
    ],
    'channel_info': [
        {'channel': '챗봯', 'count': 150, 'by_category': {'배송 문의': 80, ...}},
        # ...
    ],
    'reliability_info': {
        'accuracy': 0.85,
        'macro_f1': 0.81,
        'micro_f1': 0.83
    },
    'tickets': {
        'top3_by_category': {
            '배송 문의': [티켓1, 티켓2, 티켓3],
            # ...
        }
    }
}
```

---

## 요약: 규칙 기반 vs AI 기반

| 단계              | 규칙 기반               | AI 기반             |
| ----------------- | ----------------------- | ------------------- |
| **1. 입력**       | inquiry_type + body     | body + title        |
| **2. 분류**       | 매핑 규칙 + 키워드 매칭 | BERT 모델 추론      |
| **3. 신뢰도**     | 0.5 ~ 0.9 (규칙 기반)   | 0.0 ~ 1.0 (확률)    |
| **4. 키워드**     | 실제 매칭된 키워드      | 본문에서 추출       |
| **5. 속도**       | 매우 빠름 (1000건/초)   | 느림 (10~50건/초)   |
| **6. 정확도**     | 70~85%                  | 85~95%              |
| **7. 라이브러리** | 없음 (순수 Python)      | transformers, torch |

---

## 핵심 정리

### ✅ **키워드는 분류의 근거**

**Before (잘못된 방식):**

```
1. 키워드로 카테고리 분류
2. 분류 후 다시 키워드 추출 ❌ (순환 논리)
```

**After (올바른 방식):**

```
1. 키워드로 카테고리 분류 + 동시에 매칭된 키워드 수집 ✅
2. 수집된 키워드를 "예시 키워드"로 표시
```

### 📌 **예시 키워드의 의미**

> "이 카테고리로 분류하는 데 **실제로 사용된 키워드**"

- 규칙 기반: inquiry_type 또는 본문에서 실제로 매칭된 키워드
- AI 기반: 분류 후 본문에서 확인된 대표 키워드

### 🎯 **전체 과정 한 줄 요약**

```
티켓 읽기 → 분류 (규칙/AI) → 결과 저장 → 집계 → 화면 표시
```

---

이제 이해되셨나요? 😊
