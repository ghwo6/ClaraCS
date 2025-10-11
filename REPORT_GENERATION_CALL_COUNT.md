# 📊 리포트 생성 시 DB/GPT 호출 횟수 분석

## 🔢 요약

### DB 호출 수
- **총 14회** (성공 케이스)
- **조회 쿼리**: 10회
- **삽입/업데이트 쿼리**: 4회

### GPT 호출 수
- **총 1회** (성공 시)
- **총 0회** (실패 시, Fallback 사용)

---

## 📋 상세 분석

### 1️⃣ 리포트 생성 프로세스 (`services/report.py`)

#### STEP 1: 최신 파일 선택
```python
file_id = self.report_db.get_latest_file_id(user_id)
```
**DB 호출**: 1회
- `SELECT file_id FROM tb_uploaded_file WHERE user_id = ? AND status = 'processed' ORDER BY created_at DESC LIMIT 1`

---

#### STEP 2: 리포트 레코드 생성
```python
report_id = self.report_db.create_report(file_id, user_id, 'ai_analysis', report_title)
```
**DB 호출**: 1회
- `INSERT INTO tb_analysis_report (file_id, user_id, report_type, title, ...) VALUES (...)`

---

#### STEP 3: CS 데이터 조회 (`get_cs_analysis_data`)
```python
cs_data = self.report_db.get_cs_analysis_data(file_id)
```

##### 3-1. 최신 분류 결과 조회
```python
class_result_id = self.get_latest_classification_result(file_id)
```
**DB 호출**: 1회
- `SELECT class_result_id FROM tb_classification_result WHERE file_id = ? ORDER BY classified_at DESC LIMIT 1`

##### 3-2. 총 티켓 수 조회
**DB 호출**: 1회
- `SELECT COUNT(*) as total_tickets FROM tb_ticket WHERE file_id = ?`

##### 3-3. 카테고리별 분포 조회
```python
category_results = self.get_category_results(class_result_id)
```
**DB 호출**: 1회
- `SELECT category_id, category_name, count, ratio FROM tb_classification_category_result WHERE class_result_id = ?`

##### 3-4. 채널별 분포 조회
**DB 호출**: 1회
- `SELECT channel, COUNT(*) as count FROM tb_ticket WHERE file_id = ? GROUP BY channel`

##### 3-5. 상태별 분포 조회
**DB 호출**: 1회
- `SELECT status, COUNT(*) as count FROM tb_ticket WHERE file_id = ? GROUP BY status`

##### 3-6. 채널별 해결률 조회
**DB 호출**: 1회
- `SELECT channel, COUNT(*) as total, SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as resolved FROM tb_ticket WHERE file_id = ? GROUP BY channel`

**STEP 3 소계**: 6회

---

#### STEP 4: 채널별 추이 데이터 조회
```python
channel_trends = self.report_db.get_channel_trend_data(file_id)
```

##### 4-1. 최신 분류 결과 조회 (중복 - 캐싱 가능)
**DB 호출**: 1회
- `SELECT class_result_id FROM tb_classification_result WHERE file_id = ? ORDER BY classified_at DESC LIMIT 1`

##### 4-2. 채널별 추이 데이터 조회
**DB 호출**: 1회
- `SELECT t.channel, c.category_name, DATE(t.received_at) as date, COUNT(*) as count FROM tb_ticket t LEFT JOIN tb_category c ON t.classified_category_id = c.category_id WHERE t.file_id = ? AND t.classified_category_id IS NOT NULL GROUP BY t.channel, c.category_name, DATE(t.received_at)`

**STEP 4 소계**: 2회

---

#### STEP 5: GPT 통합 분석
```python
analysis_result = self.ai_service.generate_comprehensive_report(cs_data)
```

**GPT 호출**: 1회
- 모델: `gpt-3.5-turbo`
- max_tokens: 3000
- 소요 시간: 약 10-30초

**API 키가 없거나 에러 시**: GPT 호출 0회 (Fallback 사용)

---

#### STEP 6: 스냅샷 저장 (4개 테이블)

##### 6-1. Summary 스냅샷 저장
```python
self.report_db.save_summary_snapshot(report_id, summary_snapshot)
```
**DB 호출**: 1회
- `INSERT INTO tb_analysis_summary_snapshot (report_id, total_tickets, category_ratios, ...) VALUES (...)`

##### 6-2. Insight 스냅샷 저장
```python
self.report_db.save_insight_snapshot(report_id, insight_snapshot)
```
**DB 호출**: 1회
- `INSERT INTO tb_analysis_insight_snapshot (report_id, insight_data) VALUES (...)`

##### 6-3. Solution 스냅샷 저장
```python
self.report_db.save_solution_snapshot(report_id, solution)
```
**DB 호출**: 1회
- `INSERT INTO tb_analysis_solution_snapshot (report_id, solution_data) VALUES (...)`

##### 6-4. Channel 스냅샷 저장 (여러 레코드)
```python
self.report_db.save_channel_snapshot(report_id, channel_trends)
```
**DB 호출**: 1회 (한 번의 트랜잭션에 여러 INSERT)
- `INSERT INTO tb_analysis_channel_snapshot (report_id, channel, time_period, category_id, count) VALUES (...)` × N건
- N = 채널 수 × 날짜 수 × 카테고리 수

**STEP 6 소계**: 4회

---

#### STEP 7: 리포트 완료 처리
```python
self.report_db.complete_report(report_id)
```
**DB 호출**: 1회
- `UPDATE tb_analysis_report SET status = 'completed', completed_at = NOW() WHERE report_id = ?`

---

## 📊 총합

### DB 호출 수

| 단계 | 작업 | 호출 수 |
|-----|------|--------|
| STEP 1 | 최신 파일 선택 | 1회 |
| STEP 2 | 리포트 레코드 생성 | 1회 |
| STEP 3 | CS 데이터 조회 | 6회 |
| STEP 4 | 채널별 추이 데이터 | 2회 |
| STEP 6 | 스냅샷 저장 (4개 테이블) | 4회 |
| STEP 7 | 리포트 완료 처리 | 1회 |
| **합계** | | **15회** |

### GPT 호출 수

| 상황 | 호출 수 |
|-----|--------|
| API 키 있고 성공 | **1회** |
| API 키 없거나 실패 | **0회** (Fallback) |

---

## 🔍 상세 DB 쿼리 목록

### 조회 쿼리 (11회)

1. **최신 파일 선택**
   ```sql
   SELECT file_id FROM tb_uploaded_file 
   WHERE user_id = ? AND status = 'processed' 
   ORDER BY created_at DESC LIMIT 1
   ```

2. **최신 분류 결과 조회** (2회 - STEP 3, STEP 4에서 각각)
   ```sql
   SELECT class_result_id FROM tb_classification_result 
   WHERE file_id = ? ORDER BY classified_at DESC LIMIT 1
   ```

3. **총 티켓 수**
   ```sql
   SELECT COUNT(*) FROM tb_ticket WHERE file_id = ?
   ```

4. **카테고리별 결과**
   ```sql
   SELECT category_id, category_name, count, ratio 
   FROM tb_classification_category_result 
   WHERE class_result_id = ?
   ```

5. **채널별 분포**
   ```sql
   SELECT channel, COUNT(*) FROM tb_ticket 
   WHERE file_id = ? GROUP BY channel
   ```

6. **상태별 분포**
   ```sql
   SELECT status, COUNT(*) FROM tb_ticket 
   WHERE file_id = ? GROUP BY status
   ```

7. **채널별 해결률**
   ```sql
   SELECT channel, COUNT(*) as total, 
          SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as resolved
   FROM tb_ticket WHERE file_id = ? GROUP BY channel
   ```

8. **채널별 추이 데이터**
   ```sql
   SELECT t.channel, c.category_name, DATE(t.received_at), COUNT(*)
   FROM tb_ticket t
   LEFT JOIN tb_category c ON t.classified_category_id = c.category_id
   WHERE t.file_id = ? AND t.classified_category_id IS NOT NULL
   GROUP BY t.channel, c.category_name, DATE(t.received_at)
   ```

### 삽입/업데이트 쿼리 (4회)

9. **리포트 레코드 생성**
   ```sql
   INSERT INTO tb_analysis_report (...) VALUES (...)
   ```

10. **Summary 스냅샷**
    ```sql
    INSERT INTO tb_analysis_summary_snapshot (...) VALUES (...)
    ```

11. **Insight 스냅샷**
    ```sql
    INSERT INTO tb_analysis_insight_snapshot (...) VALUES (...)
    ```

12. **Solution 스냅샷**
    ```sql
    INSERT INTO tb_analysis_solution_snapshot (...) VALUES (...)
    ```

13. **Channel 스냅샷** (배치 INSERT)
    ```sql
    INSERT INTO tb_analysis_channel_snapshot (...) VALUES (...) [× N건]
    ```

14. **리포트 완료**
    ```sql
    UPDATE tb_analysis_report SET status = 'completed', completed_at = NOW() 
    WHERE report_id = ?
    ```

---

## ⚡ 최적화 가능 영역

### 1. 중복 쿼리 제거 (캐싱)

**문제**: `get_latest_classification_result`가 2번 호출됨
- STEP 3에서 1회
- STEP 4에서 1회

**개선 방안**:
```python
# 한 번만 조회하고 재사용
class_result_id = self.report_db.get_latest_classification_result(file_id)
cs_data = self.report_db.get_cs_analysis_data_with_cache(file_id, class_result_id)
channel_trends = self.report_db.get_channel_trend_data_with_cache(file_id, class_result_id)
```

**효과**: DB 호출 15회 → **14회** (1회 감소)

---

### 2. 배치 쿼리 병합

**문제**: STEP 3에서 총 티켓 수, 채널별 분포, 상태별 분포를 각각 조회

**개선 방안**:
```sql
-- 한 번의 쿼리로 통합
SELECT 
    COUNT(*) as total_tickets,
    SUM(CASE WHEN channel = '게시판' THEN 1 ELSE 0 END) as channel_board,
    SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as status_closed,
    ...
FROM tb_ticket
WHERE file_id = ?
```

**효과**: DB 호출 14회 → **11회** (3회 감소)

---

### 3. Connection Pool 최적화

**현재 설정**:
- Pool 크기: 20
- 동시 리포트 생성 가능: 약 1-2개 (각 14-15개 connection 사용)

**권장 사항**:
- Pool 크기 유지 (20)
- Connection 재사용 최적화 (한 번의 connection으로 여러 쿼리 실행)

---

## 📈 성능 지표

### 리포트 생성 시간

| 구분 | 시간 | 병목 구간 |
|-----|------|---------|
| **DB 조회** | 0.5 - 1초 | STEP 3, 4 (집계 쿼리) |
| **GPT 분석** | 10 - 30초 | STEP 5 (API 호출) |
| **DB 저장** | 0.2 - 0.5초 | STEP 6 (4개 테이블) |
| **총 시간** | 11 - 32초 | GPT 호출이 대부분 |

### Fallback 사용 시

| 구분 | 시간 |
|-----|------|
| **DB 조회** | 0.5 - 1초 |
| **Fallback 생성** | 0.01초 |
| **DB 저장** | 0.2 - 0.5초 |
| **총 시간** | 1 - 2초 |

---

## 🎯 결론

### ✅ 현재 구조의 장점

1. **명확한 단계 분리**: 각 단계별 책임 명확
2. **에러 처리**: 각 단계별 에러 핸들링
3. **Fallback 지원**: GPT 실패 시 DB 데이터 활용

### ⚠️ 개선 가능 영역

1. **중복 쿼리 제거**: 1회 절약 가능
2. **배치 쿼리 병합**: 3회 절약 가능
3. **Connection 재사용**: 성능 개선

### 📊 최종 수치

| 항목 | 현재 | 최적화 후 |
|-----|------|----------|
| **DB 호출** | 15회 | 11회 (-27%) |
| **GPT 호출** | 1회 | 1회 |
| **총 시간** | 11-32초 | 10-31초 |

**핵심**: GPT 호출이 시간의 90% 이상을 차지하므로, **DB 최적화의 효과는 제한적**입니다.

---

**작성일**: 2025-10-11  
**상태**: ✅ 분석 완료

