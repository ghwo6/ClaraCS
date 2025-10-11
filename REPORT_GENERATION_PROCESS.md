# 📊 리포트 생성 프로세스 완전 가이드

## 🎯 개요

**ClaraCS AI 분석 리포트 생성 기능**은 최신 업로드된 CS 데이터를 자동으로 선택하여 GPT 기반 종합 분석을 수행합니다.

### ✨ 주요 특징

- ✅ **최신 파일 자동 선택** (file_id 불필요)
- ✅ **GPT 기반 통합 분석** (한 번의 API 호출로 모든 섹션 생성)
- ✅ **구조화된 JSON 응답** (데이터 요약, 인사이트, 솔루션)
- ✅ **DB 스냅샷 저장** (리포트 영구 보관)

---

## 🔄 전체 프로세스 흐름

```
[사용자] "리포트 생성" 버튼 클릭
    ↓
[프론트엔드] POST /api/report/generate { user_id: 1 }
    ↓
[컨트롤러] controllers/report.py → generate_report()
    ↓
[서비스] services/report.py → ReportService.generate_report()
    ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 1: 최신 파일 선택 (자동)                              │
│   - tb_uploaded_file에서 user_id 기준 최신 file_id 조회   │
│   - 결과: file_id = 12                                   │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 2: 리포트 레코드 생성                                 │
│   - tb_analysis_report INSERT                           │
│   - status = 'processing'                               │
│   - 결과: report_id = 456                                │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 3: CS 데이터 조회 (분류 결과 기반)                     │
│   - 총 티켓 수                                            │
│   - 카테고리별 분포 (tb_classification_category_result)  │
│   - 채널별 분포 (tb_ticket)                              │
│   - 채널별 해결률 (status='closed' 기준)                  │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 4: GPT 기반 통합 분석 (핵심!)                         │
│   → utils/ai_service.py                                 │
│   → generate_comprehensive_report(cs_data)              │
│                                                          │
│   [프롬프트 구성]                                         │
│   - 전체 CS 건수                                          │
│   - 카테고리별 분포 (%, 키워드)                           │
│   - 채널별 분포 (%)                                       │
│   - 채널별 해결률 (%)                                     │
│                                                          │
│   [OpenAI API 호출]                                      │
│   - model: gpt-3.5-turbo                                │
│   - max_tokens: 3000                                    │
│   - temperature: 0.7                                    │
│                                                          │
│   [JSON 응답 파싱]                                        │
│   {                                                      │
│     "summary": { ... },                                 │
│     "insight": { ... },                                 │
│     "overall_insight": { ... },                         │
│     "solution": { ... }                                 │
│   }                                                      │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 5: 스냅샷 저장 (DB 영구 보관)                         │
│   - tb_analysis_insight_snapshot INSERT                 │
│   - insight_payload (JSON 전체 저장)                     │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 6: 리포트 완료 처리                                   │
│   - tb_analysis_report UPDATE                           │
│   - status = 'completed'                                │
│   - completed_at = NOW()                                │
└─────────────────────────────────────────────────────────┘
    ↓
[서비스] 응답 데이터 구성 및 반환
    ↓
[컨트롤러] JSON 응답
{
  "success": true,
  "data": {
    "report_id": 456,
    "file_id": 12,
    "summary": { ... },
    "insight": { ... },
    "overall_insight": { ... },
    "solution": { ... },
    "generated_at": "2025-10-11 12:00:00"
  }
}
    ↓
[프론트엔드] 렌더링
  - renderSummary() → 데이터 요약 섹션
  - renderInsights() → 인사이트 도출 섹션
  - renderSolutions() → 솔루션 제안 섹션
    ↓
[사용자] 리포트 확인 완료 ✅
```

---

## 📡 API 명세

### POST /api/report/generate

**요청 (Request)**

```json
{
  "user_id": 1 // 선택사항, 기본값 1
}
```

**응답 (Response)**

```json
{
  "success": true,
  "data": {
    "report_id": 456,
    "file_id": 12,
    "summary": {
      "total_cs_count": 2000,
      "category_ratio": {
        "제품 하자": "40%",
        "네트워크 불량": "35%",
        "배송 문제": "25%"
      },
      "resolution_rate": {
        "게시판": "70%",
        "챗봇": "62%",
        "전화": "85%"
      }
    },
    "insight": {
      "제품 하자": {
        "issue": "음성, 상담 의존 높음 -> 전문 대응 필요",
        "short_term": "제품별 FAQ, 영상 가이드 제공",
        "long_term": "하자 데이터 -> R&D 피드백, 불량률 개선"
      }
    },
    "overall_insight": {
      "short_term": "채널별 감정상태 분석 → 게시판 자동 분류, 챗봇 고도화",
      "long_term": "CS 데이터를 기반으로 제품, IT, 물류 부서와 실시간 피드백 체계 구축",
      "notable": "중복 CS 12% → 고객 불편 누적의 주요 원인"
    },
    "solution": {
      "short_term": [
        {
          "suggestion": "게시판 자동 분류 요약",
          "expected_effect": "응답시간 30% 단축"
        },
        {
          "suggestion": "챗봇 FAQ + 자가 진단 기능",
          "expected_effect": "해결률 15% 상승"
        }
      ],
      "long_term": [
        {
          "suggestion": "예방형 품질 관리 체계",
          "expected_effect": "불량률 지속 감소"
        }
      ]
    },
    "generated_at": "2025-10-11 12:00:00"
  }
}
```

**에러 응답**

```json
{
  "success": false,
  "error": "분석할 데이터가 없습니다. 먼저 파일을 업로드하고 자동 분류를 실행하세요."
}
```

---

## 🗄️ 데이터베이스 조회

### 1. 최신 파일 선택

```sql
SELECT file_id
FROM tb_uploaded_file
WHERE user_id = 1
  AND status = 'processed'
  AND (is_deleted IS NULL OR is_deleted = FALSE)
ORDER BY created_at DESC
LIMIT 1
```

**결과**: `file_id = 12`

---

### 2. 최신 분류 결과 조회

```sql
SELECT cr.class_result_id
FROM tb_classification_result cr
WHERE cr.file_id = 12
ORDER BY cr.classified_at DESC
LIMIT 1
```

**결과**: `class_result_id = 789`

---

### 3. CS 데이터 조회 (5개 쿼리)

#### 3-1. 총 티켓 수

```sql
SELECT COUNT(*) as total_tickets
FROM tb_ticket
WHERE file_id = 12
```

→ `2,000건`

#### 3-2. 카테고리별 분포

```sql
SELECT
    ccr.category_id,
    c.category_name,
    ccr.count,
    ccr.ratio,
    ccr.example_keywords
FROM tb_classification_category_result ccr
JOIN tb_category c ON ccr.category_id = c.category_id
WHERE ccr.class_result_id = 789
ORDER BY ccr.count DESC
```

**결과**:

```json
[
  {
    "category_name": "제품 하자",
    "count": 800,
    "percentage": 40.0
  },
  {
    "category_name": "네트워크 불량",
    "count": 700,
    "percentage": 35.0
  },
  {
    "category_name": "배송 문제",
    "count": 500,
    "percentage": 25.0
  }
]
```

#### 3-3. 채널별 분포

```sql
SELECT channel, COUNT(*) as count
FROM tb_ticket
WHERE file_id = 12
GROUP BY channel
ORDER BY count DESC
```

#### 3-4. 상태별 분포

```sql
SELECT status, COUNT(*) as count
FROM tb_ticket
WHERE file_id = 12
GROUP BY status
```

#### 3-5. 채널별 해결률

```sql
SELECT
    channel,
    COUNT(*) as total,
    SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as resolved
FROM tb_ticket
WHERE file_id = 12
GROUP BY channel
```

**결과**:

```json
[
  {
    "channel": "게시판",
    "total": 500,
    "resolved": 350,
    "resolution_rate": 70.0
  },
  {
    "channel": "챗봇",
    "total": 800,
    "resolved": 496,
    "resolution_rate": 62.0
  },
  {
    "channel": "전화",
    "total": 700,
    "resolved": 595,
    "resolution_rate": 85.0
  }
]
```

---

## 🤖 GPT 프롬프트

### 프롬프트 구조

```
당신은 고객 CS 데이터를 분석하여 자동 분류 및 솔루션을 제안하는 AI 서비스의 분석 전문가입니다.

다음 데이터를 기반으로 아래 4가지 항목에 대해 JSON 형식으로 응답해 주세요.

**CS 데이터:**
- 전체 CS 건수: 2,000건

**카테고리별 분포:**
- 제품 하자: 800건 (40.0%)
- 네트워크 불량: 700건 (35.0%)
- 배송 문제: 500건 (25.0%)

**채널별 분포:**
- 게시판: 500건 (25.0%)
- 챗봇: 800건 (40.0%)
- 전화: 700건 (35.0%)

**채널별 해결률:**
- 게시판: 70.0% (해결 350건 / 전체 500건)
- 챗봇: 62.0% (해결 496건 / 전체 800건)
- 전화: 85.0% (해결 595건 / 전체 700건)

---

**응답 형식:**

1. **summary**: 전체 CS 건수, 카테고리별 비율, 채널별 해결률
2. **insight**: 카테고리별 문제점과 단기/장기 개선 방안
3. **overall_insight**: 단기/장기/특이사항 관점에서 종합 인사이트
4. **solution**: 단기(1~6개월)/장기(6개월~2년) 전략 제안

**중요**: 반드시 순수한 JSON 형식으로만 응답하세요.
```

### GPT 응답 예시

```json
{
  "summary": {
    "total_cs_count": 2000,
    "category_ratio": {
      "제품 하자": "40%",
      "네트워크 불량": "35%",
      "배송 문제": "25%"
    },
    "resolution_rate": {
      "게시판": "70%",
      "챗봇": "62%",
      "전화": "85%"
    }
  },
  "insight": {
    "제품 하자": {
      "issue": "음성, 상담 의존 높음 -> 전문 대응 필요",
      "short_term": "제품별 FAQ, 영상 가이드 제공",
      "long_term": "하자 데이터 -> R&D 피드백, 불량률 개선"
    },
    "네트워크 불량": {
      "issue": "기술적 복잡도 높아 해결 시간 지연",
      "short_term": "네트워크 진단 도구 제공",
      "long_term": "예방적 모니터링 시스템 구축"
    }
  },
  "overall_insight": {
    "short_term": "채널별 감정상태 분석 → 게시판 자동 분류, 챗봇 고도화, 음성 콜백 도입",
    "long_term": "CS 데이터를 기반으로 제품, IT, 물류 부서와 실시간 피드백 체계 구축",
    "notable": "중복 CS 12% → 고객 불편 누적의 주요 원인"
  },
  "solution": {
    "short_term": [
      {
        "suggestion": "게시판 자동 분류 요약",
        "expected_effect": "응답시간 30% 단축"
      },
      {
        "suggestion": "챗봇 FAQ + 자가 진단 기능",
        "expected_effect": "해결률 15% 상승"
      },
      {
        "suggestion": "전화 콜백 예약 시스템",
        "expected_effect": "대기시간 40% 감소"
      }
    ],
    "long_term": [
      {
        "suggestion": "예방형 품질 관리 체계",
        "expected_effect": "불량률 지속 감소"
      },
      {
        "suggestion": "네트워크 예측 알고리즘",
        "expected_effect": "장애 발생 20% 차단"
      }
    ]
  }
}
```

---

## 💾 데이터베이스 저장

### 1. 리포트 레코드 생성

```sql
INSERT INTO tb_analysis_report
(file_id, created_by, report_type, title, status, created_at)
VALUES (12, 1, 'ai_analysis', 'AI 분석 리포트_20251011_120000', 'processing', NOW())
```

**결과**: `report_id = 456`

---

### 2. 스냅샷 저장

```sql
INSERT INTO tb_analysis_insight_snapshot
(report_id, insight_payload, created_at)
VALUES (
    456,
    '{
      "summary": {...},
      "insight": {...},
      "overall_insight": {...},
      "solution": {...}
    }',
    NOW()
)
```

---

### 3. 리포트 완료 처리

```sql
UPDATE tb_analysis_report
SET status = 'completed',
    completed_at = NOW()
WHERE report_id = 456
```

---

## 🎨 프론트엔드 렌더링

### HTML 구조

```html
<section class="section" id="report">
  <div class="head">
    <h2>분석 리포트 (요약/인사이트)</h2>
    <button class="btn save" id="btn-generate-report">리포트 생성</button>
  </div>

  <div class="body grid cols-2">
    <!-- 차트 카드 (숨김) -->
    <div class="card" style="display:none;">
      <strong>채널별 추이</strong>
    </div>

    <!-- 데이터 요약 -->
    <div class="card">
      <strong>데이터 요약</strong>
      <ul class="subtle">
        <!-- 여기에 동적 렌더링 -->
      </ul>
    </div>

    <!-- 인사이트 도출 -->
    <div class="card">
      <strong>인사이트 도출</strong>
      <ol class="subtle">
        <!-- 여기에 동적 렌더링 -->
      </ol>
    </div>

    <!-- 솔루션 제안 -->
    <div class="card">
      <strong>솔루션 제안</strong>
      <ul class="subtle">
        <!-- 여기에 동적 렌더링 -->
      </ul>
    </div>
  </div>
</section>
```

### JavaScript 렌더링 로직

```javascript
// 데이터 요약 렌더링
renderSummary(summary) {
  // 전체 CS 건수
  // 카테고리별 비율 (리스트)
  // 채널별 해결률 (리스트)
}

// 인사이트 렌더링
renderInsights(insight, overallInsight) {
  // 카테고리별 인사이트 (문제점, 단기, 장기)
  // 종합 인사이트 (단기, 장기, 특이사항)
}

// 솔루션 렌더링
renderSolutions(solution) {
  // 단기 솔루션 (1~6개월)
  // 장기 솔루션 (6개월~2년)
}
```

---

## ⚙️ 파일 구조

### 수정된 파일 목록

```
controllers/
  └── report.py ✅ (API 엔드포인트 재정의)

services/
  ├── report.py ✅ (비즈니스 로직 단순화)
  └── db/
      └── report_db.py ✅ (새 메서드 추가)

utils/
  └── ai_service.py ✅ (GPT 프롬프트 메서드 추가)

static/js/
  └── report.js ✅ (프론트엔드 렌더링 수정)
```

---

## 🚀 실행 예시

### 1. 데이터 업로드

```bash
POST /api/upload
→ file_id: 12
```

### 2. 자동 분류

```bash
POST /api/classifications/run
→ class_result_id: 789
```

### 3. 리포트 생성

```bash
POST /api/report/generate
{
  "user_id": 1
}

→ Response:
{
  "success": true,
  "data": {
    "report_id": 456,
    "summary": {...},
    "insight": {...},
    "overall_insight": {...},
    "solution": {...}
  }
}
```

---

## 🔍 주요 특징

### ✅ 자동화

- **파일 자동 선택**: 최신 업로드 파일 자동 사용
- **분류 결과 연동**: 자동 분류 결과 기반 분석
- **스냅샷 저장**: 리포트 자동 영구 보관

### ✅ GPT 통합

- **한 번의 API 호출**: 모든 섹션을 한 번에 생성
- **구조화된 응답**: JSON 형식으로 파싱 보장
- **Fallback 처리**: API 실패 시 기본 리포트 제공

### ✅ 확장성

- **프롬프트 수정 용이**: `_build_comprehensive_report_prompt()` 메서드 수정
- **응답 형식 커스터마이징**: JSON 구조 자유롭게 변경 가능
- **다국어 지원 가능**: 프롬프트 다국어 버전 추가

---

## 📝 요약

| **단계** | **동작**           | **주요 파일**   | **출력**             |
| -------- | ------------------ | --------------- | -------------------- |
| 1        | 최신 파일 선택     | `report_db.py`  | `file_id`            |
| 2        | 리포트 레코드 생성 | `report_db.py`  | `report_id`          |
| 3        | CS 데이터 조회     | `report_db.py`  | `cs_data` (5개 쿼리) |
| 4        | GPT 통합 분석      | `ai_service.py` | JSON (4개 섹션)      |
| 5        | 스냅샷 저장        | `report_db.py`  | DB INSERT            |
| 6        | 리포트 완료        | `report_db.py`  | status='completed'   |
| 7        | 응답 반환          | `report.py`     | JSON 응답            |
| 8        | 프론트엔드 렌더링  | `report.js`     | HTML 업데이트        |

---

**생성일**: 2025-10-11  
**작성자**: ClaraCS Development Team
