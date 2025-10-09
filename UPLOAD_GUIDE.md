# 데이터 업로드 기능 가이드

## 목차

1. [개요](#개요)
2. [사전 준비](#사전-준비)
3. [사용 방법](#사용-방법)
4. [주요 기능](#주요-기능)
5. [문제 해결](#문제-해결)

---

## 개요

ClaraCS의 데이터 업로드 기능은 CSV 및 Excel 파일을 업로드하여 CS 티켓 데이터를 시스템에 저장하고 분석할 수 있도록 지원합니다.

### 주요 특징

- CSV, XLSX, XLS 파일 형식 지원
- 컬럼 매핑 기능으로 다양한 형식의 파일 처리
- 자동 파싱 및 데이터 정제
- 실시간 업로드 진행 상황 표시

---

## 사전 준비

### 1. 데이터베이스 설정

먼저 데이터베이스에 코드성 데이터를 삽입해야 합니다.

```bash
# MySQL에 접속
mysql -u root -p

# 데이터베이스 선택
USE clara_cs;

# 코드성 데이터 삽입
source database_insert_code_data.sql
```

### 2. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일에 다음 내용을 설정합니다:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=clara_cs
```

---

## 사용 방법

### 1단계: 컬럼 매핑 설정

업로드할 파일의 컬럼명과 시스템 필드를 매핑합니다.

#### 기본 8개 필수 컬럼

- **접수일**: 티켓 접수 날짜/시간
- **고객ID**: 고객 고유 식별자
- **채널**: CS 문의 채널 (전화, 이메일, 게시판 등)
- **상품코드**: 제품/상품 고유 코드
- **문의 유형**: 문의 카테고리/유형
- **본문**: 문의 내용 본문
- **담당자**: 처리 담당자
- **처리 상태**: 티켓 처리 상태

#### 매핑 방법

1. 업로드 페이지의 "컬럼 매핑" 섹션으로 이동
2. 좌측에 원본 파일의 컬럼명 입력
3. 우측 드롭다운에서 매핑할 시스템 필드 선택
4. 토글 스위치로 활성화/비활성화 설정
5. **"컬럼 저장"** 버튼 클릭

```
예시:
created_at → 접수일
customer_ID → 고객ID
channel → 채널
product_ID → 상품코드
category → 문의 유형
message → 본문
assignee → 담당자
status → 처리 상태
```

### 2단계: 파일 업로드

#### 방법 1: 드래그 앤 드롭

1. CSV 또는 Excel 파일을 "데이터 업로드" 영역으로 드래그
2. 파일이 추가되면 파일 목록에 표시됨

#### 방법 2: 파일 선택

1. **"파일 첨부"** 버튼 클릭
2. 파일 선택 대화상자에서 파일 선택
3. 여러 파일을 동시에 선택 가능

### 3단계: 데이터 처리

1. 업로드할 파일 확인
2. **"정제 실행"** 버튼 클릭
3. 파일이 서버로 전송되고 자동으로 처리됨
4. 처리 완료 메시지 확인

---

## 주요 기능

### 1. 컬럼 매핑 자동 적용

컬럼 매핑을 한 번 저장하면, 다음 업로드 시 자동으로 적용됩니다.

### 2. 파일 형식 자동 감지

- CSV: UTF-8 인코딩 자동 처리
- XLSX/XLS: Excel 파일 자동 파싱

### 3. 데이터 검증

- 필수 컬럼 누락 체크
- 날짜 형식 검증
- 데이터 타입 자동 변환

### 4. 에러 처리

- 파일 형식 오류 시 명확한 에러 메시지 표시
- 업로드 실패 시 롤백 처리
- 로그 기록으로 문제 추적 가능

---

## 데이터베이스 스키마

### tb_uploaded_file

업로드된 파일 정보를 저장합니다.

| 컬럼명            | 타입     | 설명                |
| ----------------- | -------- | ------------------- |
| file_id           | INT      | 파일 고유 ID (PK)   |
| user_id           | INT      | 업로드한 사용자 ID  |
| original_filename | VARCHAR  | 원본 파일명         |
| storage_path      | VARCHAR  | 저장 경로           |
| extension_code_id | INT      | 파일 확장자 코드 ID |
| row_count         | INT      | 행 개수             |
| status            | VARCHAR  | 처리 상태           |
| created_at        | DATETIME | 생성 일시           |
| processed_at      | DATETIME | 처리 완료 일시      |

### tb_ticket

파일에서 추출된 티켓 데이터를 저장합니다.

| 컬럼명       | 타입     | 설명               |
| ------------ | -------- | ------------------ |
| ticket_id    | INT      | 티켓 고유 ID (PK)  |
| file_id      | INT      | 파일 ID (FK)       |
| user_id      | INT      | 사용자 ID          |
| received_at  | DATETIME | 접수 일시          |
| channel      | VARCHAR  | 채널               |
| customer_id  | VARCHAR  | 고객 ID            |
| product_code | VARCHAR  | 상품 코드          |
| inquiry_type | VARCHAR  | 문의 유형          |
| title        | VARCHAR  | 제목               |
| body         | TEXT     | 본문               |
| status       | VARCHAR  | 처리 상태          |
| raw_data     | JSON     | 원본 데이터 (JSON) |
| created_at   | DATETIME | 생성 일시          |

### tb_column_mapping

컬럼 매핑 정보를 저장합니다.

| 컬럼명          | 타입     | 설명              |
| --------------- | -------- | ----------------- |
| mapping_id      | INT      | 매핑 고유 ID (PK) |
| file_id         | INT      | 파일 ID (FK)      |
| original_column | VARCHAR  | 원본 컬럼명       |
| mapping_code_id | INT      | 매핑 코드 ID (FK) |
| is_activate     | BOOLEAN  | 활성화 여부       |
| created_at      | DATETIME | 생성 일시         |

---

## API 엔드포인트

### 1. 파일 업로드

```
POST /api/upload
Content-Type: multipart/form-data

Parameters:
- file: 업로드할 파일 (required)
- user_id: 사용자 ID (optional, default: 1)

Response:
{
  "success": true,
  "message": "파일 업로드 및 처리가 완료되었습니다.",
  "data": {
    "file_id": 1,
    "original_filename": "sample.csv",
    "row_count": 100,
    "tickets_inserted": 100,
    "created_at": "2025-10-05T12:34:56"
  }
}
```

### 2. 매핑 코드 조회

```
GET /api/mapping/codes

Response:
{
  "success": true,
  "data": [
    {
      "mapping_code_id": 1,
      "code_name": "접수일",
      "description": "티켓 접수 날짜/시간"
    },
    ...
  ]
}
```

### 3. 컬럼 매핑 저장

```
POST /api/mapping/save
Content-Type: application/json

Body:
{
  "mappings": [
    {
      "original_column": "created_at",
      "mapping_code_id": "접수일",
      "file_id": null,
      "is_activate": true
    },
    ...
  ]
}

Response:
{
  "status": "success",
  "msg": "컬럼 매핑이 저장되었습니다.",
  "data": {
    "inserted_count": 8,
    "success": true
  }
}
```

### 4. 마지막 매핑 조회

```
GET /api/mapping/last

Response:
{
  "success": true,
  "mappings": [
    {
      "mapping_id": 1,
      "file_id": null,
      "original_column": "created_at",
      "mapping_code_id": 1,
      "code_name": "접수일",
      "description": "티켓 접수 날짜/시간",
      "is_activate": true,
      "created_at": "2025-10-05T12:34:56"
    },
    ...
  ]
}
```

---

## 문제 해결

### 문제: 파일 업로드 실패

**원인**: 허용되지 않은 파일 형식
**해결**: CSV, XLSX, XLS 파일만 업로드 가능합니다.

### 문제: 컬럼 매핑이 저장되지 않음

**원인**: 필수 필드 누락
**해결**: 원본 컬럼명과 매핑 코드를 모두 입력해야 합니다.

### 문제: 티켓 데이터가 저장되지 않음

**원인**: 컬럼 매핑이 설정되지 않음
**해결**: 먼저 컬럼 매핑을 설정하고 저장한 후 파일을 업로드하세요.

### 문제: 날짜 형식 오류

**원인**: 지원되지 않는 날짜 형식
**해결**: YYYY-MM-DD 또는 YYYY-MM-DD HH:MM:SS 형식을 권장합니다.

---

## 추가 정보

### 로그 확인

```bash
# 로그 파일 위치
logs/app.log

# 실시간 로그 확인
tail -f logs/app.log
```

### 업로드된 파일 위치

```
uploads/
  ├── 20251005_123456_sample.csv
  ├── 20251005_123457_data.xlsx
  └── ...
```

### 테스트 데이터

`utils/dummydata/` 폴더에 테스트용 더미 데이터가 있습니다.

---

## 지원

문제가 발생하거나 질문이 있으시면:

- GitHub Issues: [링크]
- Email: support@claraCS.com
- 문서: [링크]
