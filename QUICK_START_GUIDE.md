# 🚀 ClaraCS 빠른 시작 가이드

## 📋 사전 준비

### 1. 가상환경 생성 (최초 1회만)

```bash
# 프로젝트 상위 폴더에 가상환경 생성
cd C:\Users\minhyeok\Desktop\project\01_study\002_github
python -m venv clara-venv
```

### 2. 의존성 설치

```bash
cd ClaraCS
. ../clara-venv/Scripts/activate  # PowerShell
# 또는
..\clara-venv\Scripts\activate.bat  # CMD

pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일 생성 (프로젝트 루트):

```env
# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=clara_cs

# OpenAI API 키
OPENAI_API_KEY=your_openai_api_key

# Flask 설정
SECRET_KEY=your_secret_key
DEBUG=True
```

---

## 🎯 서버 실행 방법

### 방법 1: 자동 실행 스크립트 (권장)

**PowerShell**:

```powershell
.\run_app.ps1
```

**CMD**:

```cmd
run_app.bat
```

### 방법 2: 수동 실행

**PowerShell**:

```powershell
. ../clara-venv/Scripts/activate
python app.py
```

**CMD**:

```cmd
..\clara-venv\Scripts\activate.bat
python app.py
```

---

## 📊 주요 기능 사용 순서

### 1️⃣ 데이터 업로드

```
POST /api/upload
→ file_id 반환
```

### 2️⃣ 자동 분류 실행

```
POST /api/classifications/run
{
  "user_id": 1,
  "file_id": 12  // 선택사항 (없으면 최신 파일)
}
→ class_result_id 반환
```

### 3️⃣ 리포트 생성

```
POST /api/report/generate
{
  "user_id": 1
}
→ 리포트 데이터 반환 (summary, insight, solution)
```

---

## 🔍 문제 해결

### Q1: "분류된 CS 데이터가 없습니다" 에러

**원인**: 자동 분류를 먼저 실행하지 않음

**해결**:

```bash
# 1. 파일 업로드 확인
POST /api/upload

# 2. 자동 분류 실행
POST /api/classifications/run

# 3. 리포트 생성
POST /api/report/generate
```

### Q2: "Failed getting connection; pool exhausted" 에러

**해결**: 이미 수정 완료! (Pool 크기 20으로 증가 + 재시도 로직)

**확인**:

- `utils/database.py`: pool_size=20 ✅
- 모든 메서드: connection.close() 추가 ✅

### Q3: 가상환경 활성화가 안 돼요

**PowerShell**:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**그래도 안 되면**:

```powershell
. ../clara-venv/Scripts/activate
```

---

## 📁 프로젝트 구조

```
ClaraCS/
├── app.py                 # Flask 메인 앱
├── config.py             # 설정
├── requirements.txt      # 의존성
├── .env                  # 환경 변수 (생성 필요)
├── run_app.ps1          # 실행 스크립트 (PowerShell)
├── run_app.bat          # 실행 스크립트 (CMD)
│
├── controllers/          # API 엔드포인트
│   ├── upload.py
│   ├── auto_classify.py
│   └── report.py
│
├── services/            # 비즈니스 로직
│   ├── upload.py
│   ├── auto_classify.py
│   ├── report.py
│   └── db/             # DB 레이어
│       ├── upload_db.py
│       ├── auto_classify_db.py
│       └── report_db.py
│
├── utils/              # 유틸리티
│   ├── database.py     # DB 커넥션 풀
│   ├── ai_service.py   # GPT 통합
│   └── classifiers/    # 분류 엔진
│
├── static/             # 프론트엔드
│   ├── js/
│   └── css/
│
└── templates/          # HTML 템플릿
```

---

## 🎉 체크리스트

실행 전 확인:

- [ ] 가상환경 생성됨 (`../clara-venv/`)
- [ ] 의존성 설치됨 (`pip install -r requirements.txt`)
- [ ] `.env` 파일 생성 및 설정
- [ ] MySQL 서버 실행 중
- [ ] 데이터베이스 생성 (`clara_cs`)
- [ ] 테이블 생성 (`database_schema.sql` 실행)

---

## 📚 관련 문서

- **리포트 생성 프로세스**: `REPORT_GENERATION_PROCESS.md`
- **DB 커넥션 이슈 해결**: `DB_CONNECTION_ISSUE_RESOLVED.md`
- **DB 코딩 가이드**: `DB_CONNECTION_FIX_GUIDE.md`
- **데이터베이스 스키마**: `database_schema.sql`

---

**작성일**: 2025-10-11  
**버전**: 1.0
