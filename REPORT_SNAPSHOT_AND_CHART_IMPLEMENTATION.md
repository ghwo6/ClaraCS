# 📊 리포트 스냅샷 저장 및 차트 구현 완료

## ✅ 구현 완료 사항

### 1️⃣ **3개 스냅샷 테이블 저장**

- ✅ `tb_analysis_summary_snapshot` - 데이터 요약 저장
- ✅ `tb_analysis_insight_snapshot` - 인사이트 저장
- ✅ `tb_analysis_solution_snapshot` - 솔루션 저장
- ✅ `tb_analysis_channel_snapshot` - 채널별 추이 저장

### 2️⃣ **Chart.js 기반 채널별 추이 그래프**

- ✅ 스택 막대그래프 (카테고리별)
- ✅ 꺾은선 그래프 (전체 합계)
- ✅ 채널 수만큼 그래프 생성
- ✅ X축: 시간순, Y축: CS 개수

---

## 📊 1. 스냅샷 테이블 저장

### 저장 흐름

```python
# services/report.py → _save_analysis_snapshot()

def _save_analysis_snapshot(report_id, analysis_result, channel_trends):
    # 1. Summary 스냅샷
    summary_snapshot = {
        'total_tickets': summary['total_cs_count'],
        'resolved_count': summary['resolution_rate'],
        'category_ratios': summary['category_ratio'],
        'repeat_rate': 0.0
    }
    report_db.save_summary_snapshot(report_id, summary_snapshot)

    # 2. Insight 스냅샷
    insight_snapshot = {
        'insight': analysis_result['insight'],
        'overall_insight': analysis_result['overall_insight']
    }
    report_db.save_insight_snapshot(report_id, insight_snapshot)

    # 3. Solution 스냅샷
    solution = analysis_result['solution']
    report_db.save_solution_snapshot(report_id, solution)

    # 4. Channel 스냅샷 (평면화하여 저장)
    report_db.save_channel_snapshot(report_id, channel_trends)
```

---

### 테이블별 저장 데이터

#### 1. `tb_analysis_summary_snapshot`

**SQL**:

```sql
INSERT INTO tb_analysis_summary_snapshot
(report_id, total_tickets, resolved_count, category_ratios, repeat_rate, created_at)
VALUES (456, 2000, '{"게시판": "70%", "챗봇": "62%"}', '{"제품 하자": "40%"}', 0.0, NOW())
```

**저장 데이터**:

```json
{
  "report_id": 456,
  "total_tickets": 2000,
  "resolved_count": { "게시판": "70%", "챗봇": "62%", "전화": "85%" },
  "category_ratios": { "제품 하자": "40%", "네트워크 불량": "35%" },
  "repeat_rate": 0.0
}
```

---

#### 2. `tb_analysis_insight_snapshot`

**SQL**:

```sql
INSERT INTO tb_analysis_insight_snapshot
(report_id, insight_payload, created_at)
VALUES (456, '{"insight": {...}, "overall_insight": {...}}', NOW())
```

**저장 데이터**:

```json
{
  "insight": {
    "제품 하자": {
      "issue": "음성, 상담 의존 높음",
      "short_term": "제품별 FAQ 제공",
      "long_term": "R&D 피드백 체계"
    }
  },
  "overall_insight": {
    "short_term": "채널별 감정상태 분석 → 자동 분류",
    "long_term": "실시간 피드백 체계 구축",
    "notable": "중복 CS 12%"
  }
}
```

---

#### 3. `tb_analysis_solution_snapshot`

**SQL**:

```sql
INSERT INTO tb_analysis_solution_snapshot
(report_id, solution_payload, created_at)
VALUES (456, '{"short_term": [...], "long_term": [...]}', NOW())
```

**저장 데이터**:

```json
{
  "short_term": [
    {
      "suggestion": "게시판 자동 분류",
      "expected_effect": "응답시간 30% 단축"
    },
    { "suggestion": "챗봇 FAQ 강화", "expected_effect": "해결률 15% 상승" }
  ],
  "long_term": [
    { "suggestion": "예방형 품질 관리", "expected_effect": "불량률 지속 감소" }
  ]
}
```

---

#### 4. `tb_analysis_channel_snapshot` (평면화 저장)

**입력 데이터** (channel_trends):

```json
{
  "게시판": {
    "categories": ["배송", "환불", "품질"],
    "dates": ["10-01", "10-02", "10-03"],
    "data": [
      [10, 5, 3], // 10-01: 배송 10건, 환불 5건, 품질 3건
      [12, 7, 4], // 10-02
      [8, 6, 5] // 10-03
    ]
  }
}
```

**평면화 후 저장** (9건의 레코드):

```sql
INSERT INTO tb_analysis_channel_snapshot
(report_id, channel, time_period, category_id, count)
VALUES
(456, '게시판', '10-01', 1, 10),  -- 배송
(456, '게시판', '10-01', 2, 5),   -- 환불
(456, '게시판', '10-01', 3, 3),   -- 품질
(456, '게시판', '10-02', 1, 12),
(456, '게시판', '10-02', 2, 7),
(456, '게시판', '10-02', 3, 4),
(456, '게시판', '10-03', 1, 8),
(456, '게시판', '10-03', 2, 6),
(456, '게시판', '10-03', 3, 5)
```

---

## 📈 2. Chart.js 기반 채널별 추이 그래프

### 그래프 구조

**chart.html 참고** → **스택 막대 + 꺾은선 복합 차트**

```javascript
// 데이터셋 구성
datasets = [
  // 1. 카테고리별 스택 막대
  {
    type: "bar",
    label: "배송",
    data: [10, 12, 8],
    backgroundColor: "#ff6b6b",
    stack: "stack1",
  },
  {
    type: "bar",
    label: "환불",
    data: [5, 7, 6],
    backgroundColor: "#4ecdc4",
    stack: "stack1",
  },
  // 2. 전체 합계 꺾은선
  {
    type: "line",
    label: "전체 합계",
    data: [18, 23, 19], // 각 날짜의 합계
    borderColor: "#e74c3c",
    tension: 0.3,
  },
];
```

### 그래프 특징

| 요소       | 설명                                          |
| ---------- | --------------------------------------------- |
| **X축**    | 날짜 (시간순) - `['10-01', '10-02', '10-03']` |
| **Y축**    | CS 건수 - 0부터 시작                          |
| **막대**   | 카테고리별로 색상 구분, 스택형                |
| **꺾은선** | 전체 합계 (빨간색)                            |
| **개수**   | 채널 수만큼 생성 (게시판, 챗봇, 전화 등)      |

### 카테고리 색상 매핑

```javascript
{
  '배송': '#ff6b6b',          // 빨강
  '환불/교환': '#4ecdc4',     // 청록
  '품질/하자': '#45b7d1',     // 파랑
  '제품 하자': '#45b7d1',
  '기술 지원': '#96ceb4',     // 초록
  '상품 문의': '#f7b731',     // 노랑
  '네트워크 불량': '#a29bfe',  // 보라
  '불만/클레임': '#ee5a6f',   // 분홍
  '기타': '#feca57'           // 주황
}
```

### 렌더링 예시

```
┌─────────────────────────────────────────┐
│ 게시판                                    │
├─────────────────────────────────────────┤
│  50│                              ▓▓▓  │ ← 전체 합계 (빨간선)
│  40│         ▓▓▓      ▓▓▓         ▓▓▓  │
│  30│    ███  ███ ███  ███    ███  ███  │
│  20│    ███  ███ ███  ███    ███  ███  │
│  10│    ███  ███ ███  ███    ███  ███  │
│   0└────────────────────────────────────│
│     10-01 10-02 10-03 10-04 10-05 10-06│
│                                          │
│  ■ 배송  ■ 환불  ■ 품질  ━ 전체 합계    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 챗봇                                      │
├─────────────────────────────────────────┤
│  ... (동일한 구조)                        │
└─────────────────────────────────────────┘
```

---

## 🔄 데이터 흐름

### Step 1: DB 조회

```sql
SELECT
    t.channel,
    c.category_name,
    DATE(t.received_at) as date,
    COUNT(*) as count
FROM tb_ticket t
LEFT JOIN tb_category c ON t.classified_category_id = c.category_id
WHERE t.file_id = 12
  AND t.classified_category_id IS NOT NULL
GROUP BY t.channel, c.category_name, DATE(t.received_at)
```

**결과**:

```
channel | category_name | date       | count
--------|---------------|------------|------
게시판   | 배송          | 2024-10-01 | 10
게시판   | 환불          | 2024-10-01 | 5
게시판   | 배송          | 2024-10-02 | 12
...
```

### Step 2: 데이터 변환 (Python)

```python
channel_trends = {
    "게시판": {
        "categories": ["배송", "환불", "품질"],
        "dates": ["10-01", "10-02", "10-03"],
        "data": [
            [10, 5, 3],
            [12, 7, 4],
            [8, 6, 5]
        ]
    },
    "챗봇": { ... }
}
```

### Step 3: JSON 응답

```json
{
  "channel_trends": {
    "게시판": {
      "categories": ["배송", "환불", "품질"],
      "dates": ["10-01", "10-02", "10-03"],
      "data": [
        [10, 5, 3],
        [12, 7, 4],
        [8, 6, 5]
      ]
    }
  }
}
```

### Step 4: Chart.js 렌더링 (JavaScript)

```javascript
// 채널별로 순회
Object.entries(channel_trends).forEach(([channel, data]) => {
  createChannelChart(channel, data);
});

// 각 차트 생성
function createChannelChart(channel, data) {
  // 1. Canvas 생성
  // 2. 데이터셋 구성 (막대 + 꺾은선)
  // 3. Chart.js 초기화
  new Chart(ctx, config);
}
```

---

## 🗄️ 스냅샷 저장 예시

### 실행 예시

**입력**:

```json
{
  "summary": {
    "total_cs_count": 2000,
    "category_ratio": {"제품 하자": "40%"},
    "resolution_rate": {"게시판": "70%"}
  },
  "insight": { ... },
  "solution": { ... }
}
```

**DB 저장 결과**:

#### tb_analysis_summary_snapshot

| summary_snapshot_id | report_id | total_tickets | resolved_count     | category_ratios       | repeat_rate |
| ------------------- | --------- | ------------- | ------------------ | --------------------- | ----------- |
| 1                   | 456       | 2000          | `{"게시판":"70%"}` | `{"제품 하자":"40%"}` | 0.0         |

#### tb_analysis_insight_snapshot

| insight_id | report_id | insight_payload                             |
| ---------- | --------- | ------------------------------------------- |
| 1          | 456       | `{"insight":{...},"overall_insight":{...}}` |

#### tb_analysis_solution_snapshot

| solution_id | report_id | solution_payload                         |
| ----------- | --------- | ---------------------------------------- |
| 1           | 456       | `{"short_term":[...],"long_term":[...]}` |

#### tb_analysis_channel_snapshot (9건)

| channel_snapshot_id | report_id | channel | time_period | category_id | count |
| ------------------- | --------- | ------- | ----------- | ----------- | ----- |
| 1                   | 456       | 게시판  | 10-01       | 1           | 10    |
| 2                   | 456       | 게시판  | 10-01       | 2           | 5     |
| 3                   | 456       | 게시판  | 10-01       | 3           | 3     |
| ...                 | ...       | ...     | ...         | ...         | ...   |

---

## 📈 2. 차트 구현 상세

### HTML 구조

```html
<div class="card" id="channel-trends-card">
  <strong>채널별 추이</strong>
  <div class="chart-box" id="channel-charts-container">
    <!-- 동적 생성 영역 -->
    <div class="channel-chart-wrapper">
      <h4>게시판</h4>
      <canvas id="chart-게시판"></canvas>
    </div>
    <div class="channel-chart-wrapper">
      <h4>챗봇</h4>
      <canvas id="chart-챗봇"></canvas>
    </div>
  </div>
</div>
```

### JavaScript 구현

```javascript
class ReportManager {
  constructor() {
    this.chartInstances = {}; // Chart 객체 저장
  }

  renderChannelTrends(channelTrends) {
    // 1. 기존 차트 제거
    Object.values(this.chartInstances).forEach((chart) => chart.destroy());

    // 2. 채널별로 차트 생성
    Object.entries(channelTrends).forEach(([channel, data]) => {
      this.createChannelChart(container, channel, data);
    });
  }

  createChannelChart(container, channel, trendData) {
    const { categories, dates, data } = trendData;

    // 데이터셋 구성
    const datasets = [];

    // 스택 막대 (카테고리별)
    categories.forEach((cat, idx) => {
      datasets.push({
        type: "bar",
        label: cat,
        data: data.map((row) => row[idx]),
        backgroundColor: this.getCategoryColors()[cat],
        stack: "stack1",
      });
    });

    // 꺾은선 (전체 합계)
    const totals = data.map((row) => row.reduce((a, b) => a + b, 0));
    datasets.push({
      type: "line",
      label: "전체 합계",
      data: totals,
      borderColor: "#e74c3c",
    });

    // Chart.js 생성
    new Chart(ctx, {
      type: "bar",
      data: { labels: dates, datasets },
      options: {
        scales: {
          x: { stacked: true },
          y: { stacked: true, beginAtZero: true },
        },
      },
    });
  }
}
```

### CSS 스타일

```css
/* 차트 컨테이너 */
#channel-charts-container {
  padding: 20px;
  max-height: 800px;
  overflow-y: auto;
}

.channel-chart-wrapper {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.channel-chart-wrapper h4 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid #3498db;
}
```

---

## 🔍 주요 수정 파일

### Backend

| 파일                       | 수정 내용                                                  |
| -------------------------- | ---------------------------------------------------------- |
| `services/report.py`       | ✅ `_save_analysis_snapshot()` - 3개 테이블 저장           |
| `services/db/report_db.py` | ✅ `save_channel_snapshot()` - 평면화 로직 추가            |
| `services/db/report_db.py` | ✅ `get_channel_trend_data()` - 쿼리 수정 (JOIN 오류 수정) |

### Frontend

| 파일                    | 수정 내용                                   |
| ----------------------- | ------------------------------------------- |
| `templates/report.html` | ✅ Chart.js CDN 추가                        |
| `static/js/report.js`   | ✅ `renderChannelTrends()` - 차트 렌더링    |
| `static/js/report.js`   | ✅ `createChannelChart()` - Chart.js 초기화 |
| `static/css/report.css` | ✅ 차트 스타일 추가                         |

---

## 🎯 핵심 개선 사항

### Before vs After

| 항목            | Before            | After                                        |
| --------------- | ----------------- | -------------------------------------------- |
| **스냅샷 저장** | ❌ Insight만 저장 | ✅ 3개 테이블 모두 저장                      |
| **채널 데이터** | ❌ 저장 안 됨     | ✅ 평면화하여 저장                           |
| **차트**        | ❌ 텍스트만 표시  | ✅ Chart.js 복합 차트                        |
| **쿼리**        | ❌ 잘못된 JOIN    | ✅ 올바른 JOIN (classified_category_id 사용) |

---

## 🚀 실행 예시

### 1. 리포트 생성 API 호출

```bash
POST /api/report/generate
{
  "user_id": 1
}
```

### 2. 응답 데이터

```json
{
  "success": true,
  "data": {
    "report_id": 456,
    "file_id": 12,
    "channel_trends": {
      "게시판": {
        "categories": ["배송", "환불", "품질"],
        "dates": ["10-01", "10-02", "10-03"],
        "data": [[10, 5, 3], [12, 7, 4], [8, 6, 5]]
      },
      "챗봇": { ... }
    },
    "summary": { ... },
    "insight": { ... },
    "solution": { ... }
  }
}
```

### 3. DB 저장 결과

- ✅ `tb_analysis_report`: status='completed'
- ✅ `tb_analysis_summary_snapshot`: 1건
- ✅ `tb_analysis_insight_snapshot`: 1건
- ✅ `tb_analysis_solution_snapshot`: 1건
- ✅ `tb_analysis_channel_snapshot`: 9건 (채널별×날짜별×카테고리별)

### 4. 프론트엔드 렌더링

- ✅ **채널별 추이**: Chart.js 복합 차트 (채널 수만큼)
- ✅ **데이터 요약**: 리스트 형태
- ✅ **인사이트**: 카테고리별 + 종합
- ✅ **솔루션**: 단기 + 장기

---

## 📊 차트 예시 (게시판)

```
┌────────────────────────────────────────────┐
│ 게시판                                      │
├────────────────────────────────────────────┤
│                                             │
│  50│                         ●             │
│    │                    ●                  │
│  40│               ●                       │
│    │          ●                            │
│  30│     ██████ ██████ ██████ ██████       │
│    │     ██████ ██████ ██████ ██████       │
│  20│     ██████ ██████ ██████ ██████       │
│    │     ██████ ██████ ██████ ██████       │
│  10│     ██████ ██████ ██████ ██████       │
│    │     ██████ ██████ ██████ ██████       │
│   0└─────┬─────┬─────┬─────┬─────┬────────│
│        10-01 10-02 10-03 10-04 10-05       │
│                                             │
│  ■ 배송  ■ 환불  ■ 품질  ● 전체 합계        │
└────────────────────────────────────────────┘
```

**특징**:

- 🟥 빨간 막대: 배송
- 🟦 파란 막대: 환불
- 🟩 초록 막대: 품질
- 🔴 빨간 선: 전체 합계 (스택 막대 위)

---

## ✅ 체크리스트

### Backend

- [x] `tb_analysis_summary_snapshot` 저장 구현
- [x] `tb_analysis_insight_snapshot` 저장 구현
- [x] `tb_analysis_solution_snapshot` 저장 구현
- [x] `tb_analysis_channel_snapshot` 평면화 저장 구현
- [x] 쿼리 수정 (tb_ticket.classified_category_id 사용)

### Frontend

- [x] Chart.js CDN 추가
- [x] 채널별 차트 렌더링 메서드
- [x] 스택 막대 + 꺾은선 복합 차트
- [x] 카테고리 색상 매핑
- [x] CSS 스타일 추가

### DB

- [x] Connection Pool 크기 20으로 증가
- [x] 모든 메서드 connection.close() 추가
- [x] 재시도 로직 추가

---

## 🎉 완료!

### ✅ 구현 완료

1. **3개 스냅샷 테이블에 데이터 저장** → `tb_analysis_*_snapshot`
2. **채널별 추이 그래프** → Chart.js 스택 막대 + 꺾은선
3. **DB Connection 안정성** → Pool 크기 20, 재시도 로직

### 🚀 사용 방법

```bash
# 1. 서버 실행
.\run_app.ps1

# 2. 순서대로 실행
POST /api/upload          # 파일 업로드
POST /api/classifications/run  # 자동 분류 (필수!)
POST /api/report/generate      # 리포트 생성

# 3. 결과 확인
→ 채널별 차트 (스택 막대 + 꺾은선)
→ 데이터 요약
→ 인사이트 도출
→ 솔루션 제안
```

---

**구현 완료일**: 2025-10-11  
**작성자**: ClaraCS Development Team  
**상태**: ✅ Production Ready
