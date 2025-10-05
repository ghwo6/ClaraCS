# 로컬 DB 연동 가이드

## 📋 개요

ClaraCS 프로젝트를 로컬 MySQL 데이터베이스와 연동하는 방법을 설명합니다.

## 🎯 핵심 구조 이해

### data_repository vs ReportDB

```
더미데이터 사용 시:
services/report.py
    └─> utils/dummydata/report_dummy.py (data_repository) ❌ 실제 DB 사용 시 불필요

실제 DB 사용 시:
services/report.py
    └─> services/db/report_db.py (ReportDB)
            └─> utils/database.py (db_manager)
                    └─> MySQL 데이터베이스 ✅ 이 구조 사용
```

**결론**: `data_repository`는 더미데이터 전용이므로 실제 DB 사용 시에는 필요 없습니다!

## 📦 1. 필요한 패키지 설치

```bash
pip install mysql-connector-python python-dotenv pandas
```

## 🗄️ 2. 데이터베이스 설정

### 2.1 MySQL 설치 및 실행

MySQL이 설치되어 있지 않다면:

- Windows: [MySQL Installer](https://dev.mysql.com/downloads/installer/)
- Mac: `brew install mysql`
- Linux: `sudo apt-get install mysql-server`

### 2.2 데이터베이스 생성

```bash
# MySQL 접속
mysql -u root -p

# 또는 MySQL Workbench 사용
```

프로젝트 루트에 제공된 `database_schema.sql` 파일을 실행:

```sql
-- MySQL 콘솔에서 실행
source database_schema.sql;

-- 또는 명령줄에서 실행
mysql -u root -p < database_schema.sql
```

이 스크립트는 자동으로:

- ✅ `clara_cs` 데이터베이스 생성
- ✅ 5개 테이블 생성 (cs_tickets, classified_data, tb_column_mapping, users, report_history)
- ✅ 샘플 데이터 삽입

### 2.3 데이터베이스 확인

```sql
USE clara_cs;

-- 테이블 목록 확인
SHOW TABLES;

-- 샘플 데이터 확인
SELECT * FROM cs_tickets;
SELECT * FROM classified_data;
SELECT * FROM users;
```

## 🔐 3. 환경 변수 설정

프로젝트 루트에 `.env` 파일 생성:

```env
# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=clara_cs

# OpenAI API (AI 기능 사용 시)
OPENAI_API_KEY=your_openai_api_key_here
```

**주의**: `.env` 파일은 `.gitignore`에 추가하여 Git에 올라가지 않도록 하세요!

## 📝 4. 코드 구조 확인

### 4.1 utils/database.py

- Connection Pool을 사용한 효율적인 DB 연결 관리
- 환경변수에서 DB 설정 자동 로드
- 싱글톤 패턴으로 전역 `db_manager` 인스턴스 제공

```python
from utils.database import db_manager

# 연결 테스트
db_manager.test_connection()
```

### 4.2 services/db/report_db.py

- 모든 DB 쿼리를 처리하는 Repository 클래스
- 주요 메서드:
  - `get_channel_trend_data()`: 채널별 추이 데이터
  - `get_summary_data()`: 요약 통계
  - `get_ai_analysis_data()`: AI 분석용 데이터
  - `get_cs_tickets_by_user()`: 사용자별 티켓 조회
  - `get_classified_data_by_user()`: 사용자별 분류 데이터 조회

### 4.3 services/report.py

- 비즈니스 로직 처리
- `ReportDB`만 사용 (data_repository 사용 안 함)
- AI 서비스와 연동하여 인사이트 생성

## 🧪 5. 연결 테스트

간단한 테스트 스크립트 작성 (`test_db_connection.py`):

```python
from utils.database import db_manager
from services.db.report_db import ReportDB

# 1. DB 연결 테스트
print("=== DB 연결 테스트 ===")
if db_manager.test_connection():
    print("✅ DB 연결 성공!")
else:
    print("❌ DB 연결 실패")
    exit(1)

# 2. 데이터 조회 테스트
print("\n=== 데이터 조회 테스트 ===")
report_db = ReportDB()

# 사용자 티켓 조회
tickets = report_db.get_cs_tickets_by_user('user_001')
print(f"✅ 티켓 데이터 {len(tickets)}건 조회 성공")

# 요약 데이터 조회
summary = report_db.get_summary_data('user_001')
print(f"✅ 요약 데이터 조회 성공: 총 {summary['total_tickets']}건")

# 채널별 추이 조회
channel_trends = report_db.get_channel_trend_data('user_001')
print(f"✅ 채널별 추이 데이터 {len(channel_trends)}개 채널 조회 성공")

print("\n모든 테스트 완료! 🎉")
```

실행:

```bash
python test_db_connection.py
```

## 🚀 6. Flask 애플리케이션 실행

```bash
python app.py
```

브라우저에서 접속:

- 대시보드: http://localhost:5000/
- 리포트: http://localhost:5000/report

리포트 페이지에서 "리포트 생성" 버튼을 클릭하면 실제 DB 데이터를 기반으로 리포트가 생성됩니다!

## 📊 7. 데이터베이스 스키마

### 주요 테이블

#### cs_tickets (CS 티켓)

```sql
ticket_id          VARCHAR(50)   - 티켓 ID (PK)
user_id            VARCHAR(50)   - 사용자 ID
created_at         DATETIME      - 생성 시각
channel            VARCHAR(50)   - 접수 채널
customer_id        VARCHAR(100)  - 고객 ID
title              VARCHAR(255)  - 제목
content            TEXT          - 내용
status             VARCHAR(20)   - 처리 상태
priority           VARCHAR(20)   - 우선순위
category           VARCHAR(100)  - 카테고리
resolution_time    FLOAT         - 해결 시간 (시간)
```

#### classified_data (자동 분류 결과)

```sql
classification_id   VARCHAR(50)   - 분류 ID (PK)
user_id            VARCHAR(50)   - 사용자 ID
ticket_id          VARCHAR(50)   - 티켓 ID (FK)
classified_at      DATETIME      - 분류 시각
predicted_category VARCHAR(100)  - 예측 카테고리
confidence_score   FLOAT         - 신뢰도 (0.0~1.0)
keywords           TEXT          - 키워드
sentiment          VARCHAR(20)   - 감정 (긍정/부정/중립)
urgency_level      INT           - 긴급도 (1~5)
```

## 🔧 8. 트러블슈팅

### 문제: 연결 거부 (Connection refused)

**해결방법**:

```bash
# MySQL 서비스 상태 확인
# Windows
net start MySQL80

# Mac/Linux
sudo systemctl start mysql
sudo service mysql start
```

### 문제: 인증 실패 (Authentication failed)

**해결방법**:

```sql
-- MySQL 8.0+에서 인증 방식 변경
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
FLUSH PRIVILEGES;
```

### 문제: 데이터베이스가 존재하지 않음

**해결방법**:

```bash
# database_schema.sql 다시 실행
mysql -u root -p < database_schema.sql
```

### 문제: 빈 데이터 반환

**해결방법**:

```sql
-- 샘플 데이터 확인
USE clara_cs;
SELECT COUNT(*) FROM cs_tickets;
SELECT COUNT(*) FROM classified_data;

-- 데이터가 없다면 database_schema.sql의 INSERT 문 실행
```

## 📚 9. 추가 정보

### 샘플 데이터 추가하기

더 많은 샘플 데이터가 필요하다면:

```sql
INSERT INTO cs_tickets (ticket_id, user_id, created_at, channel, customer_id, title, content, status, category) VALUES
('TICKET_009', 'user_001', NOW(), '전화', 'cust_1009', '추가 문의', '문의 내용...', '신규', '기타문의');
```

### 데이터 초기화

```sql
-- 모든 데이터 삭제 (테이블 구조는 유지)
TRUNCATE TABLE classified_data;
TRUNCATE TABLE cs_tickets;
TRUNCATE TABLE users;

-- 샘플 데이터 다시 삽입
source database_schema.sql;
```

## ✅ 체크리스트

- [ ] MySQL 설치 및 실행
- [ ] `database_schema.sql` 실행하여 DB/테이블 생성
- [ ] `.env` 파일 생성 및 DB 정보 입력
- [ ] `pip install mysql-connector-python python-dotenv pandas`
- [ ] `test_db_connection.py` 실행하여 연결 확인
- [ ] Flask 애플리케이션 실행
- [ ] 브라우저에서 리포트 생성 테스트

모든 체크리스트를 완료하면 로컬 DB 연동이 완료됩니다! 🎉
