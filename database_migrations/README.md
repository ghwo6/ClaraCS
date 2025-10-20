# 데이터베이스 마이그레이션 가이드

## 📋 파일 배치 기능 마이그레이션

### 1️⃣ 정상 실행 (처음 실행하는 경우)

```bash
mysql -u root -p clara_cs < add_file_batch_support.sql
```

**예상 결과:**

```
Query OK, 0 rows affected
Query OK, 0 rows affected
Query OK, 0 rows affected
...
Query OK, 1 row affected
```

---

### 2️⃣ 부분 실패 후 재실행

마이그레이션이 중간에 실패한 경우, 두 가지 방법이 있습니다.

#### 방법 A: 롤백 후 재실행 (권장)

```bash
# 1. 기존 변경사항 롤백
mysql -u root -p clara_cs < rollback_file_batch_support.sql

# 2. 다시 마이그레이션 실행
mysql -u root -p clara_cs < add_file_batch_support.sql
```

#### 방법 B: 수동으로 누락된 부분만 실행

```sql
-- MySQL에 접속
mysql -u root -p clara_cs

-- 1. 컬럼 존재 여부 확인
DESCRIBE tb_uploaded_file;
DESCRIBE tb_classification_result;
DESCRIBE tb_analysis_report;

-- 2. batch_id 컬럼이 없으면 추가
-- tb_uploaded_file
ALTER TABLE `tb_uploaded_file`
ADD COLUMN `batch_id` INT COMMENT '파일이 속한 배치 ID';

ALTER TABLE `tb_uploaded_file`
ADD INDEX idx_uploaded_file_batch_id (batch_id);

-- tb_classification_result
ALTER TABLE `tb_classification_result`
ADD COLUMN `batch_id` INT COMMENT '분류 대상 배치 ID';

ALTER TABLE `tb_classification_result`
ADD INDEX idx_classification_batch_id (batch_id);

-- tb_analysis_report
ALTER TABLE `tb_analysis_report`
ADD COLUMN `batch_id` INT COMMENT '리포트 대상 배치 ID';

ALTER TABLE `tb_analysis_report`
ADD INDEX idx_report_batch_id (batch_id);

-- 3. 뷰 생성
CREATE OR REPLACE VIEW v_batch_summary AS
SELECT
    b.batch_id,
    b.user_id,
    b.batch_name,
    b.file_count,
    b.total_row_count,
    b.status,
    b.created_at,
    b.completed_at,
    COUNT(DISTINCT f.file_id) as actual_file_count,
    SUM(f.row_count) as actual_row_count,
    COUNT(DISTINCT t.ticket_id) as total_tickets,
    COUNT(DISTINCT cr.class_result_id) as classification_count,
    COUNT(DISTINCT ar.report_id) as report_count
FROM tb_file_batch b
LEFT JOIN tb_uploaded_file f ON f.batch_id = b.batch_id
LEFT JOIN tb_ticket t ON t.file_id = f.file_id
LEFT JOIN tb_classification_result cr ON cr.batch_id = b.batch_id
LEFT JOIN tb_analysis_report ar ON ar.batch_id = b.batch_id
GROUP BY b.batch_id
ORDER BY b.created_at DESC;
```

---

### 3️⃣ 컬럼 중복 오류 발생 시

```
Error Code: 1060 - Duplicate column name 'batch_id'
```

**원인:** 컬럼이 이미 존재함

**해결:**

```sql
-- 해당 테이블은 이미 batch_id가 있으므로 건너뛰고 다음 단계 실행
-- 또는 롤백 후 재실행
```

---

### 4️⃣ 인덱스 중복 오류 발생 시

```
Error Code: 1061 - Duplicate key name 'idx_uploaded_file_batch_id'
```

**원인:** 인덱스가 이미 존재함

**해결:**

```sql
-- 인덱스가 이미 있으므로 건너뛰기
-- 또는 인덱스 삭제 후 재생성
ALTER TABLE tb_uploaded_file DROP INDEX idx_uploaded_file_batch_id;
ALTER TABLE tb_uploaded_file ADD INDEX idx_uploaded_file_batch_id (batch_id);
```

---

## 🔍 마이그레이션 확인

### 테이블 확인

```sql
-- tb_file_batch 테이블 존재 확인
SHOW TABLES LIKE 'tb_file_batch';

-- tb_file_batch 구조 확인
DESCRIBE tb_file_batch;

-- batch_id 컬럼 확인
DESCRIBE tb_uploaded_file;
DESCRIBE tb_classification_result;
DESCRIBE tb_analysis_report;
```

### 뷰 확인

```sql
-- 뷰 존재 확인
SHOW FULL TABLES WHERE TABLE_TYPE = 'VIEW';

-- 뷰 데이터 조회
SELECT * FROM v_batch_summary;
```

### 인덱스 확인

```sql
-- 각 테이블의 인덱스 확인
SHOW INDEX FROM tb_uploaded_file WHERE Key_name LIKE '%batch%';
SHOW INDEX FROM tb_classification_result WHERE Key_name LIKE '%batch%';
SHOW INDEX FROM tb_analysis_report WHERE Key_name LIKE '%batch%';
```

---

## ⚠️ 주의사항

### MySQL 버전 호환성

- **MySQL 5.7:** `IF NOT EXISTS` 구문 미지원 → 현재 스크립트는 5.7 호환
- **MySQL 8.0+:** 모든 기능 지원

### 외래키 제약조건

현재는 외래키를 설정하지 않았습니다. 필요한 경우 아래 명령 실행:

```sql
-- tb_uploaded_file
ALTER TABLE `tb_uploaded_file`
ADD CONSTRAINT fk_uploaded_file_batch
FOREIGN KEY (batch_id) REFERENCES tb_file_batch(batch_id) ON DELETE SET NULL;

-- tb_classification_result
ALTER TABLE `tb_classification_result`
ADD CONSTRAINT fk_classification_batch
FOREIGN KEY (batch_id) REFERENCES tb_file_batch(batch_id) ON DELETE SET NULL;

-- tb_analysis_report
ALTER TABLE `tb_analysis_report`
ADD CONSTRAINT fk_report_batch
FOREIGN KEY (batch_id) REFERENCES tb_file_batch(batch_id) ON DELETE SET NULL;
```

### 기존 데이터

- 기존 파일 데이터의 `batch_id`는 `NULL`로 유지됩니다.
- 레거시 데이터를 배치로 변환하려면 `add_file_batch_support.sql`의 5번 섹션 주석 해제

---

## 🐛 문제 해결

### 1. 마이그레이션 전체 실패

```bash
# 롤백 후 재실행
mysql -u root -p clara_cs < rollback_file_batch_support.sql
mysql -u root -p clara_cs < add_file_batch_support.sql
```

### 2. 특정 단계만 실패

위의 "방법 B: 수동으로 누락된 부분만 실행" 참고

### 3. 권한 오류

```
Error: Access denied
```

**해결:**

```bash
# root 계정으로 실행
mysql -u root -p clara_cs < add_file_batch_support.sql

# 또는 권한이 있는 계정 사용
mysql -u admin_user -p clara_cs < add_file_batch_support.sql
```

---

## 📚 관련 파일

- `add_file_batch_support.sql` - 배치 기능 추가 마이그레이션
- `rollback_file_batch_support.sql` - 롤백 스크립트
- `../database_schema.sql` - 전체 DB 스키마 (배치 기능 포함)

---

**작성일:** 2025-10-20  
**버전:** 1.0
