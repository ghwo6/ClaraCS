# 🔧 DB Connection Pool 고갈 문제 해결 가이드

## 🚨 문제 상황

```
Failed getting connection; pool exhausted
```

**원인**:

1. ❌ **커넥션 풀 크기가 너무 작음** (pool_size=5)
2. ❌ **커넥션을 제대로 반환하지 않음** (connection.close() 누락)
3. ❌ **재시도 로직 없음** (일시적 오류 시 바로 실패)
4. ❌ **긴 작업에서 커넥션 오래 점유** (자동분류, 리포트 생성)

---

## ✅ 해결 방법

### 1️⃣ 커넥션 풀 크기 증가

**수정 전**:

```python
pool_size=5  # 너무 작음!
```

**수정 후**:

```python
pool_size=20  # 5 → 20으로 증가
```

### 2️⃣ 재시도 로직 추가

**기능**:

- 커넥션 실패 시 **최대 3회 재시도**
- **지수 백오프** (1초 → 2초 → 4초 대기)
- Pool 고갈 시 자동 재시도

**구현** (`utils/database.py`):

```python
def get_connection(self, max_retries=3, retry_delay=1):
    """Connection Pool에서 연결 가져오기 (재시도 로직 추가)"""
    for attempt in range(max_retries):
        try:
            connection = self.connection_pool.get_connection()
            if connection.is_connected():
                return connection
            else:
                connection.reconnect(attempts=3, delay=1)
                return connection
        except mysql.connector.errors.PoolError as e:
            logger.warning(f"Connection Pool 고갈 (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # 지수 백오프

    raise Exception(f"데이터베이스 연결 실패 ({max_retries}회 재시도)")
```

### 3️⃣ Context Manager 추가

**안전한 연결 관리** (자동으로 connection 반환):

```python
@contextmanager
def get_connection_context(self):
    """Context Manager를 사용한 안전한 연결 관리"""
    connection = None
    try:
        connection = self.get_connection()
        yield connection
    except Exception as e:
        if connection:
            connection.rollback()
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()  # 자동 반환!
```

**사용 예시**:

```python
# ❌ 잘못된 방법 (connection이 반환되지 않을 수 있음)
connection = self.db_manager.get_connection()
cursor = connection.cursor()
cursor.execute("SELECT ...")
# connection.close() 누락 가능성!

# ✅ 올바른 방법 (자동으로 반환됨)
with self.db_manager.get_connection_context() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    # connection은 자동으로 반환됨!
```

### 4️⃣ 재시도 데코레이터

**DB 작업에 자동 재시도 적용**:

```python
from utils.database import db_retry_decorator

@db_retry_decorator(max_retries=3, retry_delay=1)
def insert_tickets(self, tickets):
    """티켓 삽입 (자동 재시도)"""
    connection = self.db_manager.get_connection()
    try:
        cursor = connection.cursor()
        cursor.executemany("INSERT INTO ...", tickets)
        connection.commit()
    finally:
        cursor.close()
        connection.close()
```

---

## 🔍 주요 수정 사항

### utils/database.py

| **변경 사항**     | **수정 전**   | **수정 후**                   |
| ----------------- | ------------- | ----------------------------- |
| Pool 크기         | `pool_size=5` | `pool_size=20`                |
| 재시도 로직       | ❌ 없음       | ✅ 최대 3회, 지수 백오프      |
| Context Manager   | ❌ 없음       | ✅ `get_connection_context()` |
| 재시도 데코레이터 | ❌ 없음       | ✅ `@db_retry_decorator`      |

---

## 📝 코딩 가이드라인

### ✅ DO (권장)

1. **항상 finally 블록에서 connection 닫기**:

```python
connection = self.db_manager.get_connection()
cursor = None
try:
    cursor = connection.cursor()
    cursor.execute("SELECT ...")
    connection.commit()
finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()  # 필수!
```

2. **Context Manager 사용 (더 안전)**:

```python
with self.db_manager.get_connection_context() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT ...")
    conn.commit()
    cursor.close()
```

3. **긴 작업은 여러 개의 작은 트랜잭션으로 분리**:

```python
# ❌ 나쁜 예: 하나의 커넥션으로 2000건 처리
for i in range(2000):
    cursor.execute("INSERT ...")

# ✅ 좋은 예: 배치 처리 (100건씩 커밋)
for i in range(0, 2000, 100):
    batch = tickets[i:i+100]
    cursor.executemany("INSERT ...", batch)
    connection.commit()
```

### ❌ DON'T (금지)

1. **connection을 닫지 않음**:

```python
# ❌ 위험!
connection = self.db_manager.get_connection()
cursor = connection.cursor()
cursor.execute("SELECT ...")
# connection.close() 없음! (Pool 고갈)
```

2. **예외 처리 없이 사용**:

```python
# ❌ 위험!
connection = self.db_manager.get_connection()
cursor.execute("SELECT ...")  # 오류 발생 시 connection 누수
```

3. **긴 작업에서 커넥션 오래 점유**:

```python
# ❌ 위험!
connection = self.db_manager.get_connection()
time.sleep(60)  # 커넥션을 1분간 점유!
cursor.execute("SELECT ...")
```

---

## 🧪 테스트 방법

### 1. Connection Pool 상태 확인

```python
# utils/database.py에 추가
def get_pool_status(self):
    """Connection Pool 상태 확인"""
    try:
        pool = self.connection_pool
        return {
            'pool_name': pool.pool_name,
            'pool_size': pool._pool_size,
            'pool_used': len(pool._cnx_queue._queue)
        }
    except Exception as e:
        return {'error': str(e)}
```

### 2. 스트레스 테스트

```python
import threading

def test_concurrent_connections():
    """동시 연결 테스트"""
    def worker():
        with db_manager.get_connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SLEEP(1)")
            cursor.close()

    threads = []
    for i in range(30):  # 30개 동시 요청
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("스트레스 테스트 완료!")
```

---

## 📊 성능 개선 효과

| **지표**        | **수정 전** | **수정 후** | **개선률**   |
| --------------- | ----------- | ----------- | ------------ |
| Pool 크기       | 5           | 20          | **+300%**    |
| 재시도 횟수     | 0회         | 최대 3회    | **안정성 ↑** |
| Connection 누수 | 자주 발생   | 거의 없음   | **안정성 ↑** |
| 오류 복구       | 수동 재시작 | 자동 재시도 | **가용성 ↑** |

---

## 🔥 자주 발생하는 문제와 해결

### Q1: "Pool exhausted" 에러가 계속 발생해요

**원인**: Connection이 제대로 반환되지 않음

**해결**:

1. 모든 DB 작업 코드에서 `finally` 블록 확인
2. `connection.close()` 호출 확인
3. 또는 Context Manager 사용

### Q2: 자동분류/리포트 생성 시 에러가 나요

**원인**: 긴 작업에서 많은 커넥션 사용

**해결**:

1. 배치 처리로 변경 (한 번에 100건씩)
2. 커넥션을 작업별로 새로 가져오기
3. `@db_retry_decorator` 사용

### Q3: 간헐적으로 연결이 끊어져요

**원인**: MySQL wait_timeout 또는 네트워크 불안정

**해결**:

1. `get_connection()`의 재시도 로직이 자동으로 재연결
2. `connection.reconnect()` 자동 호출됨
3. Pool 재생성 옵션 활성화됨 (`pool_reset_session=True`)

---

## 📌 체크리스트

리포트 생성 및 자동분류 작업 전 확인:

- [ ] `utils/database.py`: pool_size=20 확인
- [ ] 모든 DB 작업: `finally` 블록에서 `connection.close()` 확인
- [ ] 긴 작업: 배치 처리로 변경
- [ ] 재시도 로직: `@db_retry_decorator` 적용
- [ ] Context Manager: `with get_connection_context()` 사용

---

## 🚀 적용 우선순위

### High Priority (즉시 적용)

1. ✅ `utils/database.py` 수정 (이미 완료)
2. 🔄 `services/db/auto_classify_db.py` - connection 반환 확인
3. 🔄 `services/db/report_db.py` - connection 반환 확인
4. 🔄 `services/db/upload_db.py` - connection 반환 확인

### Medium Priority (권장)

5. Context Manager로 마이그레이션
6. 배치 처리 적용
7. 스트레스 테스트 수행

### Low Priority (선택)

8. 모니터링 대시보드 추가
9. Connection Pool 메트릭 수집

---

**생성일**: 2025-10-11  
**작성자**: ClaraCS Development Team

**다음 단계**: 주요 DB 파일들의 connection.close() 확인 및 수정
