# 파일 배치 업로드 기능 가이드

## 📋 개요

여러 파일을 하나의 그룹(배치)으로 묶어서 **통합 분류 및 리포트 생성**이 가능합니다.

### ✨ 주요 기능

- ✅ 여러 파일을 한 번에 업로드
- ✅ 배치 단위로 그룹 관리
- ✅ 배치 전체에 대한 통합 자동분류
- ✅ 배치 기반 통합 리포트 생성
- ✅ 기존 단일 파일 업로드도 계속 지원

---

## 🚀 사용 방법

### 1️⃣ DB 마이그레이션 실행

먼저 배치 기능을 위한 DB 스키마를 추가합니다.

```bash
mysql -u root -p clara_cs < database_migrations/add_file_batch_support.sql
```

**추가되는 테이블:**

- `tb_file_batch` - 파일 배치 정보
- `tb_uploaded_file`에 `batch_id` 컬럼 추가
- `tb_classification_result`에 `batch_id` 컬럼 추가
- `tb_analysis_report`에 `batch_id` 컬럼 추가

---

### 2️⃣ API 사용 예시

#### 📤 배치 업로드 API

**엔드포인트:** `POST /api/upload/batch`

**요청 (multipart/form-data):**

```javascript
const formData = new FormData();
formData.append("files", file1); // 여러 파일 추가
formData.append("files", file2);
formData.append("files", file3);
formData.append("user_id", 1);
formData.append("batch_name", "2024년 1분기 CS 데이터"); // 선택사항

fetch("/api/upload/batch", {
  method: "POST",
  body: formData,
})
  .then((res) => res.json())
  .then((data) => {
    console.log("Batch ID:", data.data.batch_id);
    console.log("성공:", data.data.successful_files);
    console.log("실패:", data.data.failed_files);
  });
```

**응답 예시:**

```json
{
  "success": true,
  "message": "3개 파일 업로드 완료 (0개 실패)",
  "data": {
    "batch_id": 1,
    "batch_name": "2024년 1분기 CS 데이터",
    "total_files": 3,
    "successful_files": 3,
    "failed_files": 0,
    "total_rows": 1500,
    "uploaded_files": [
      {
        "file_id": 101,
        "original_filename": "jan_2024.csv",
        "row_count": 500,
        "tickets_inserted": 500
      },
      {
        "file_id": 102,
        "original_filename": "feb_2024.csv",
        "row_count": 500,
        "tickets_inserted": 500
      },
      {
        "file_id": 103,
        "original_filename": "mar_2024.csv",
        "row_count": 500,
        "tickets_inserted": 500
      }
    ],
    "errors": []
  }
}
```

---

#### 🔍 배치 자동분류 API

**엔드포인트:** `POST /api/classifications/run`

**요청 (JSON):**

```json
{
  "user_id": 1,
  "batch_id": 1, // 배치 ID 사용
  "engine": "rule" // 'rule' 또는 'ai'
}
```

**응답:**

- 배치에 속한 모든 파일의 티켓을 통합하여 분류
- `meta.batch_id`에 배치 ID 포함

```json
{
    "return_code": 1,
    "class_result_id": 201,
    "meta": {
        "user_id": 1,
        "file_id": null,
        "batch_id": 1,
        "total_tickets": 1500,
        "engine_name": "rule_based_v1"
    },
    "category_info": [...],
    "channel_info": [...],
    "reliability_info": {
        "total_tickets": 1500,
        "average_confidence": 0.85,
        "high_confidence_count": 1200,
        "low_confidence_count": 50
    }
}
```

---

#### 📊 배치 리포트 생성 API

**엔드포인트:** `POST /api/report/generate`

**요청 (JSON):**

```json
{
  "user_id": 1,
  "batch_id": 1 // 배치 ID 사용
}
```

**응답:**

- 배치 전체에 대한 통합 리포트 생성

---

### 3️⃣ 단일 파일 vs 배치 비교

| 기능           | 단일 파일          | 배치 (여러 파일)         |
| -------------- | ------------------ | ------------------------ |
| **업로드 API** | `POST /api/upload` | `POST /api/upload/batch` |
| **파라미터**   | `file` (하나)      | `files` (여러 개)        |
| **식별자**     | `file_id`          | `batch_id`               |
| **자동분류**   | `{"file_id": 10}`  | `{"batch_id": 1}`        |
| **리포트**     | `{"file_id": 10}`  | `{"batch_id": 1}`        |
| **티켓 수**    | 단일 파일의 티켓   | 배치 전체 티켓 통합      |

---

## 📊 DB 구조

### tb_file_batch

| 컬럼              | 타입         | 설명                                     |
| ----------------- | ------------ | ---------------------------------------- |
| `batch_id`        | INT          | 배치 ID (PK)                             |
| `user_id`         | INT          | 사용자 ID                                |
| `batch_name`      | VARCHAR(255) | 배치 이름 (선택)                         |
| `file_count`      | INT          | 포함된 파일 수                           |
| `total_row_count` | INT          | 전체 행 수                               |
| `status`          | VARCHAR(20)  | uploading, completed, processing, failed |
| `created_at`      | DATETIME     | 생성 시각                                |
| `completed_at`    | DATETIME     | 완료 시각                                |

### tb_uploaded_file (수정)

```sql
ALTER TABLE tb_uploaded_file
ADD COLUMN batch_id INT;  -- 파일이 속한 배치 ID
```

### tb_classification_result (수정)

```sql
ALTER TABLE tb_classification_result
ADD COLUMN batch_id INT;  -- 분류 대상 배치 ID (file_id와 배타적)
```

### tb_analysis_report (수정)

```sql
ALTER TABLE tb_analysis_report
ADD COLUMN batch_id INT;  -- 리포트 대상 배치 ID
```

---

## 🎯 사용 시나리오

### 시나리오 1: 월별 데이터 통합 분석

```javascript
// 1. 3개월치 파일을 배치로 업로드
const files = [
  jan2024_file, // 1월 데이터
  feb2024_file, // 2월 데이터
  mar2024_file, // 3월 데이터
];

const batchUpload = await uploadBatch(files, {
  batch_name: "2024년 1분기 CS 데이터",
});

// batch_id = 1

// 2. 배치 전체를 자동분류 (3개월치 통합)
const classification = await runClassification({
  batch_id: 1,
});

// 결과: 3개월치 1500개 티켓 통합 분류

// 3. 배치 전체에 대한 리포트 생성
const report = await generateReport({
  batch_id: 1,
});

// 결과: 1분기 전체에 대한 통합 인사이트 및 솔루션
```

### 시나리오 2: 채널별 데이터 통합 분석

```javascript
// 이메일, 전화, 챗봇 채널의 데이터를 별도 파일로 받아서
// 하나의 배치로 통합 분석

const files = [email_data.csv, phone_data.csv, chatbot_data.csv];

const batchUpload = await uploadBatch(files, {
  batch_name: "전체 채널 통합 데이터",
});

// 자동분류 및 리포트 생성
// → 채널별 비교 분석 가능
```

---

## 🔍 배치 조회 쿼리

### 배치 목록 조회

```sql
SELECT * FROM v_batch_summary
WHERE user_id = 1
ORDER BY created_at DESC;
```

### 특정 배치의 파일 목록

```sql
SELECT * FROM tb_uploaded_file
WHERE batch_id = 1;
```

### 특정 배치의 티켓 수

```sql
SELECT COUNT(*) as total_tickets
FROM tb_ticket t
INNER JOIN tb_uploaded_file f ON f.file_id = t.file_id
WHERE f.batch_id = 1;
```

### 배치별 분류 결과 조회

```sql
SELECT * FROM tb_classification_result
WHERE batch_id = 1;
```

---

## ⚠️ 주의사항

### 1. 호환성

- **기존 단일 파일 업로드는 계속 작동**합니다
- 단일 파일 업로드 시 `batch_id`는 `NULL`로 저장됨
- API는 `file_id` 또는 `batch_id` 중 하나를 받음

### 2. 배치 크기 제한

- 파일 개수: 권장 최대 10개
- 전체 티켓 수: 권장 최대 10,000개
- 메모리 및 처리 시간 고려

### 3. 파일 형식

- 배치 내 모든 파일은 **동일한 컬럼 매핑** 사용
- 각 파일은 개별적으로 검증됨
- 일부 파일이 실패해도 나머지는 정상 처리

---

## 🐛 문제 해결

### 배치 업로드 실패

**증상:** 일부 파일만 업로드되고 나머지는 실패

**해결:**

1. 응답의 `errors` 배열 확인
2. 실패한 파일의 오류 메시지 확인
3. 컬럼 매핑 확인
4. 파일 형식(인코딩, 구분자 등) 확인

### 자동분류 시 티켓이 없다고 나옴

**원인:** 배치는 생성되었지만 파일 업로드가 실패함

**해결:**

```sql
SELECT * FROM tb_file_batch WHERE batch_id = 1;
-- file_count가 0이면 파일 업로드 실패

SELECT * FROM tb_uploaded_file WHERE batch_id = 1;
-- 실제 파일 목록 확인
```

---

## 📚 추가 자료

- [데이터베이스 스키마](../database_schema.sql)
- [API 문서](../README.md)
- [신뢰도 측정 로직](./auto_classify_confidence_logic.md)

---

**작성일:** 2025-10-20  
**버전:** 1.0
