# UI 페이지 분리 및 routes 폴더 마이그레이션 완료

## 🔄 변경 사항 요약

### 1. Import 경로 수정

- ✅ `app.py`: `from routes.mapping` → `from controllers.mapping`
- ✅ `app.py`: `from controllers.export_to_pdf import create_prototype_report` 추가

### 2. HTML 페이지 분리

새로 생성된 페이지들:

- ✅ `templates/dashboard.html` - 대시보드 (/)
- ✅ `templates/upload.html` - 데이터 업로드 + 컬럼 매핑 (/upload)
- ✅ `templates/classify.html` - 자동 분류 (/classify)
- ✅ `templates/report.html` - 분석 리포트 + PDF 내보내기 (/report)
- ✅ `templates/settings.html` - 설정 도움말 (/settings)

### 3. CSS 파일 생성

각 페이지별 전용 CSS 파일:

- ✅ `static/css/dashboard.css`
- ✅ `static/css/upload.css`
- ✅ `static/css/classify.css`
- ✅ `static/css/report.css`
- ✅ `static/css/settings.css`

### 4. JavaScript 수정

- ✅ `static/js/sidebar.js`: 해시 스크롤 → 실제 페이지 이동으로 변경
- ✅ `static/js/report.js`: 버튼 셀렉터 수정 (#btn-generate-report, #btn-template-select)
- ✅ `static/js/pdf_export.js`: PDF 다운로드 기능 개선 및 메시지 표시 추가
- ✅ `static/js/settings.js`: 설정 페이지 전용 JS 파일 생성

### 5. 버튼 동작 수정

- ✅ 리포트 생성 버튼: ID 추가 (#btn-generate-report)
- ✅ 템플릿 선택 버튼: ID 추가 (#btn-template-select)
- ✅ PDF 내보내기 버튼: 텍스트 변경 및 기능 개선

### 6. 파일 위치 변경

✅ routes 폴더 → controllers 폴더로 이동:

- `export_to_pdf.py` → `controllers/export_to_pdf.py`
- `mapping.py` → `controllers/mapping.py`

## 📂 최종 디렉토리 구조

```
ClaraCS/
├── controllers/
│   ├── auto_classify.py
│   ├── export_to_pdf.py  ← 이동됨
│   ├── main.py
│   ├── mapping.py         ← 이동됨
│   └── report.py
├── templates/
│   ├── dashboard.html     ← 신규
│   ├── upload.html        ← 신규
│   ├── classify.html      ← 신규
│   ├── report.html        ← 신규
│   ├── settings.html      ← 신규
│   └── index.html         (기존, 사용 안 함)
├── static/
│   ├── css/
│   │   ├── dashboard.css  ← 신규
│   │   ├── upload.css     ← 신규
│   │   ├── classify.css   ← 신규
│   │   ├── report.css     ← 신규
│   │   ├── settings.css   ← 신규
│   │   └── style.css
│   └── js/
│       ├── sidebar.js     ← 수정
│       ├── report.js      ← 수정
│       ├── pdf_export.js  ← 수정
│       └── settings.js    ← 신규
└── app.py                 ← 수정
```

## 🎯 페이지 라우팅

| 경로        | 페이지         | 설명                       |
| ----------- | -------------- | -------------------------- |
| `/`         | dashboard.html | 대시보드                   |
| `/upload`   | upload.html    | 데이터 업로드 + 컬럼 매핑  |
| `/classify` | classify.html  | 자동 분류                  |
| `/report`   | report.html    | 분석 리포트 + PDF 내보내기 |
| `/settings` | settings.html  | 설정 도움말                |

## ✅ 동작 확인 사항

### 리포트 생성 버튼

- 버튼 ID: `#btn-generate-report`
- API 엔드포인트: `/api/report/generate`
- 동작: POST 요청으로 리포트 생성 및 화면에 렌더링

### PDF 내보내기 버튼

- 버튼 ID: `#btn-export-pdf`
- API 엔드포인트: `/download-pdf?file_id=file_12345`
- 동작: PDF 파일 생성 및 다운로드

### 사이드바 네비게이션

- 각 메뉴 클릭 시 해당 페이지로 이동
- 현재 페이지의 메뉴 항목이 자동으로 active 상태로 표시

## 🔧 기존 기능 유지

- ✅ 모든 UI 요소와 스타일 유지
- ✅ JavaScript 기능 동작 유지
- ✅ API 엔드포인트 변경 없음
- ✅ 데이터베이스 연동 기능 유지

## 📝 주의사항

1. **루트의 index.html**: templates/index.html이 사용되지 않으므로 필요시 삭제 가능
2. **routes 폴더**: 이미 삭제되었으며, 모든 기능이 controllers로 이동됨
3. **Python 환경**: 변경사항 적용 위해 Flask 서버 재시작 필요

## 🚀 다음 단계

서버를 재시작하여 변경사항을 확인하세요:

```bash
python app.py
```

각 페이지 URL에 접속하여 정상 동작 확인:

- http://localhost:5000/
- http://localhost:5000/upload
- http://localhost:5000/classify
- http://localhost:5000/report
- http://localhost:5000/settings
