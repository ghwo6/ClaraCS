# "마지막 파일만 처리되는 문제" 해결 완료

## 🐛 문제 상황

**사용자 보고:**

> "file_id가 마지막인거로만 동작되는데?"

**원인:**

- 자동분류/리포트 실행 시 파라미터가 없으면 **"최신 파일 1개"만** 자동 선택
- 파일 3개를 업로드해도 **가장 나중에 업로드한 파일 1개만** 처리됨

---

## ✅ 해결 방법

### 자동 선택 우선순위 변경

**변경 전:**

```
파라미터 없음 → 최신 파일 1개 선택 (file_id=103)
→ 파일 3개 중 마지막 것만 처리
```

**변경 후:**

```
파라미터 없음 → 1순위: 최신 배치 선택 (batch_id=1)
                2순위: 배치 없으면 최신 파일 선택
→ 배치로 업로드했으면 3개 파일 모두 통합 처리!
```

---

## 🔧 수정된 로직

### 1️⃣ 자동분류 API (`/api/classifications/run`)

**파일:** `controllers/auto_classify.py`

```python
# 변경 전 (문제)
if not file_id:
    file_id = get_latest_file_id(user_id)  # 마지막 파일만!

# 변경 후 (해결)
if not file_id and not batch_id:
    # 1순위: 최신 배치 선택
    batch_id = get_latest_batch_id(user_id)

    if not batch_id:
        # 2순위: 배치가 없으면 최신 파일 선택
        file_id = get_latest_file_id(user_id)
```

### 2️⃣ 리포트 생성 API (`/api/report/generate`)

**파일:** `services/report.py`

```python
# 변경 전 (문제)
if not file_id:
    file_id = get_latest_file_id(user_id)  # 마지막 파일만!

# 변경 후 (해결)
if not file_id and not batch_id:
    # 1순위: 최신 배치 선택
    batch_id = get_latest_batch_id(user_id)

    if not batch_id:
        # 2순위: 배치가 없으면 최신 파일 선택
        file_id = get_latest_file_id(user_id)
```

### 3️⃣ 최신 파일 조회 로직 개선

**파일:** `services/db/auto_classify_db.py`, `services/db/report_db.py`

```python
# 변경 전
def get_latest_file_id(user_id):
    SELECT file_id FROM tb_uploaded_file
    WHERE user_id = %s
    ORDER BY created_at DESC LIMIT 1
    # → 배치에 속한 파일도 포함 (중복 처리 문제)

# 변경 후
def get_latest_file_id(user_id):
    SELECT file_id FROM tb_uploaded_file
    WHERE user_id = %s
      AND batch_id IS NULL  # ← 배치에 속하지 않은 파일만!
    ORDER BY created_at DESC LIMIT 1
```

---

## 📊 시나리오별 동작

### 시나리오 1: 배치 업로드 (3개 파일)

```javascript
// 1. 파일 3개를 배치로 업로드
POST /api/upload/batch
Body: { files: [file1, file2, file3] }

→ batch_id = 1 생성
→ file_id = 101, 102, 103 (모두 batch_id=1)

// 2. 자동분류 (파라미터 없음)
POST /api/classifications/run
Body: {}

→ 🎯 최신 배치 자동 선택: batch_id = 1
→ ✅ 3개 파일 모두 통합 분류!

// 3. 리포트 생성 (파라미터 없음)
POST /api/report/generate
Body: {}

→ 🎯 최신 배치 자동 선택: batch_id = 1
→ ✅ 3개 파일 모두 통합 리포트!
```

### 시나리오 2: 개별 파일 업로드 (3번)

```javascript
// 1. 파일을 개별로 3번 업로드
POST /api/upload  (file1) → file_id = 101, batch_id = NULL
POST /api/upload  (file2) → file_id = 102, batch_id = NULL
POST /api/upload  (file3) → file_id = 103, batch_id = NULL

// 2. 자동분류 (파라미터 없음)
POST /api/classifications/run
Body: {}

→ 배치 없음 → 최신 파일 선택: file_id = 103
→ ⚠️ 마지막 파일만 처리 (기존 동작)

// 3. 리포트 생성 (파라미터 없음)
POST /api/report/generate
Body: {}

→ 배치 없음 → 최신 파일 선택: file_id = 103
→ ⚠️ 마지막 파일만 처리 (기존 동작)
```

**해결 방법:**

- 여러 파일을 통합하려면 **배치 업로드 API 사용** 필수!

---

## 🎯 사용 방법

### ✅ 올바른 방법 (여러 파일 통합)

```javascript
// 파일 3개를 배치로 업로드
const formData = new FormData();
formData.append("files", file1);
formData.append("files", file2);
formData.append("files", file3);
formData.append("batch_name", "2024 Q1");

const result = await fetch("/api/upload/batch", {
  method: "POST",
  body: formData,
});

const batch_id = result.data.batch_id;

// 자동분류 (자동으로 배치 전체 처리)
await fetch("/api/classifications/run", {
  method: "POST",
  body: JSON.stringify({}), // 파라미터 없어도 배치 자동 선택
});

// 리포트 생성 (자동으로 배치 전체 처리)
await fetch("/api/report/generate", {
  method: "POST",
  body: JSON.stringify({}), // 파라미터 없어도 배치 자동 선택
});
```

### ❌ 잘못된 방법 (마지막 파일만 처리)

```javascript
// 파일을 개별로 3번 업로드
await fetch("/api/upload", { body: file1 });
await fetch("/api/upload", { body: file2 });
await fetch("/api/upload", { body: file3 });

// 자동분류 (마지막 파일만 처리)
await fetch("/api/classifications/run", {
  method: "POST",
  body: JSON.stringify({}),
});
// → file_id=103만 처리 ❌
```

---

## 📋 수정된 파일 목록

### 핵심 수정

| 파일                              | 수정 내용                                                                                               |
| --------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `controllers/auto_classify.py`    | ✅ 최신 배치 우선 선택 로직 추가                                                                        |
| `controllers/report.py`           | ✅ batch_id 파라미터 지원                                                                               |
| `services/auto_classify.py`       | ✅ batch 지원 (이미 완료)                                                                               |
| `services/report.py`              | ✅ 최신 배치 우선 선택 + batch 지원                                                                     |
| `services/db/auto_classify_db.py` | ✅ `get_latest_batch_id()` 추가                                                                         |
| `services/db/report_db.py`        | ✅ `get_latest_batch_id()`, `get_cs_analysis_data_by_batch()`, `get_channel_trend_data_by_batch()` 추가 |

---

## 🚀 배포 단계

### 1. DB 마이그레이션 (수정된 버전)

```bash
mysql -u root -p clara_cs < database_migrations/add_file_batch_support.sql
```

**주의:** `IF NOT EXISTS` 오류가 발생하면 이미 수정된 버전입니다.

### 2. 애플리케이션 재시작

```bash
# Flask 서버 재시작
python app.py
```

### 3. 테스트

```bash
# 배치 업로드 테스트
curl -X POST http://localhost:5000/api/upload/batch \
  -F "files=@file1.csv" \
  -F "files=@file2.csv" \
  -F "files=@file3.csv" \
  -F "user_id=1"

# 자동분류 (자동으로 최신 배치 선택)
curl -X POST http://localhost:5000/api/classifications/run \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'

# 리포트 생성 (자동으로 최신 배치 선택)
curl -X POST http://localhost:5000/api/report/generate \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

---

## 💡 핵심 포인트

### ✅ 이제 작동하는 방식

1. **배치 업로드** (`/api/upload/batch`) 사용

   - 여러 파일을 한 번에 업로드
   - `batch_id` 자동 생성

2. **자동분류** (`/api/classifications/run`)

   - 파라미터 없으면 **최신 배치 우선 선택**
   - 배치가 있으면 → 배치 전체 처리 ✅
   - 배치가 없으면 → 최신 파일 1개 처리

3. **리포트 생성** (`/api/report/generate`)
   - 파라미터 없으면 **최신 배치 우선 선택**
   - 배치가 있으면 → 배치 전체 통합 분석 ✅
   - 배치가 없으면 → 최신 파일 1개 분석

### 🔑 핵심 규칙

**"여러 파일을 통합 처리하려면 반드시 배치 업로드 API 사용!"**

---

## 📚 관련 문서

1. [배치 업로드 가이드](./batch_upload_guide.md)
2. [구현 완료 보고서](./IMPLEMENTATION_SUMMARY.md)
3. [마이그레이션 가이드](../database_migrations/README.md)

---

**작성일:** 2025-10-20  
**버전:** 1.1 (최신 배치 우선 선택 로직 추가)
