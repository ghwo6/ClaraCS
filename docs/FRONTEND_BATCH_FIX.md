# 프론트엔드 배치 업로드 수정 완료

## 🐛 기존 문제

**프론트엔드 코드 (static/js/upload.js):**

```javascript
// 문제: 파일을 하나씩 반복 업로드
for (let i = 0; i < all_files.length; i++) {
  const formData = new FormData();
  formData.append("file", all_files[i]); // 1개씩

  await fetch("/api/upload", {
    // 개별 업로드
    method: "POST",
    body: formData,
  });
}

// 결과:
// file_id = 101 (batch_id = NULL)
// file_id = 102 (batch_id = NULL)
// file_id = 103 (batch_id = NULL)
// → 자동분류/리포트는 마지막 파일(103)만 처리!
```

---

## ✅ 수정 후

**파일 개수에 따라 자동으로 API 선택:**

### 1개 파일: 기존 API 사용

```javascript
const formData = new FormData();
formData.append("file", all_files[0]);

await fetch("/api/upload", {
  // 단일 파일 API
  method: "POST",
  body: formData,
});

// 결과: file_id = 101 (batch_id = NULL)
```

### 2개 이상 파일: 배치 API 사용 ✅

```javascript
const formData = new FormData();

// 모든 파일을 한 번에 추가
for (let i = 0; i < all_files.length; i++) {
  formData.append("files", all_files[i]); // 'files' 복수형!
}
formData.append("batch_name", "업로드 2024-10-20 15:30");

await fetch("/api/upload/batch", {
  // 배치 API
  method: "POST",
  body: formData,
});

// 결과:
// batch_id = 1 생성
// file_id = 101 (batch_id = 1)
// file_id = 102 (batch_id = 1)
// file_id = 103 (batch_id = 1)
// → 자동분류/리포트는 3개 파일 모두 통합 처리! ✅
```

---

## 🔧 수정된 코드

**파일:** `static/js/upload.js`

### 변경 전 (284-353행)

```javascript
for (let i = 0; i < all_files.length; i++) {
  const file = all_files[i];
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/upload", {
    method: "POST",
    body: formData,
  });
  // ... 반복 ...
}
```

### 변경 후 (285-345행)

```javascript
// 파일 1개인 경우: 기존 API 사용
if (totalFiles === 1) {
  const formData = new FormData();
  formData.append("file", all_files[0]);

  const response = await fetch("/api/upload", {
    method: "POST",
    body: formData,
  });
}
// 파일 2개 이상인 경우: 배치 API 사용
else {
  const formData = new FormData();

  for (let i = 0; i < all_files.length; i++) {
    formData.append("files", all_files[i]); // 'files' 복수형
  }
  formData.append("batch_name", `업로드 ${new Date().toLocaleString("ko-KR")}`);

  const response = await fetch("/api/upload/batch", {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  batchId = data.data.batch_id;
  console.log(`🎯 batch_id=${batchId}, ${totalFiles}개 파일`);
}
```

---

## 📊 동작 비교

### 시나리오: 파일 3개 업로드

| 단계         | 기존 방식 (문제)                        | 수정 후 (해결)                               |
| ------------ | --------------------------------------- | -------------------------------------------- |
| **업로드**   | `/api/upload` × 3번 반복                | `/api/upload/batch` 1번                      |
| **결과**     | file_id = 101, 102, 103 (batch_id=NULL) | batch_id = 1, file_id = 101~103 (batch_id=1) |
| **자동분류** | file_id=103만 처리 ❌                   | batch_id=1 전체 처리 ✅                      |
| **리포트**   | file_id=103만 분석 ❌                   | batch_id=1 전체 분석 ✅                      |

---

## 🎯 사용자 경험 개선

### 성공 메시지 개선

**단일 파일 (1개):**

```
🎉 모든 처리가 완료되었습니다!

처리 결과:
• 파일 업로드: 1개
• 티켓 저장: 500건
```

**배치 업로드 (2개 이상):**

```
🎉 모든 처리가 완료되었습니다!

처리 결과:
• 배치 업로드: 3개 파일 (batch_id: 1)
• 티켓 저장: 1500건

💡 자동분류와 리포트는 3개 파일 전체를 통합 처리합니다!
```

---

## ✅ 테스트 시나리오

### 1. 단일 파일 업로드

```
1. 파일 1개 선택
2. "업로드" 버튼 클릭
3. 결과: file_id 생성, batch_id = NULL
4. 자동분류: 해당 file_id만 처리
```

### 2. 여러 파일 배치 업로드

```
1. 파일 3개 선택
2. "업로드" 버튼 클릭
3. 콘솔에 "🎯 batch_id=1, 3개 파일" 출력
4. 결과: batch_id = 1 생성
5. 자동분류: 3개 파일 전체 통합 처리 ✅
6. 리포트: 3개 파일 전체 통합 분석 ✅
```

---

## 🚀 배포 확인

### 1. 서버 재시작

```bash
python app.py
```

### 2. 브라우저에서 테스트

1. 업로드 페이지 접속
2. 파일 3개 선택
3. 업로드 버튼 클릭
4. **브라우저 콘솔 확인:**

   ```
   배치 업로드 성공: {...}
   🎯 batch_id=1, 3개 파일, 1500개 티켓
   ```

5. **성공 메시지 확인:**
   ```
   💡 자동분류와 리포트는 3개 파일 전체를 통합 처리합니다!
   ```

### 3. 자동분류 실행

- 분류 페이지에서 "자동분류 실행" 클릭
- **콘솔 로그 확인:** `🎯 최신 배치 자동 선택: batch_id=1`
- **결과:** 3개 파일 1500개 티켓 모두 분류됨 ✅

### 4. 리포트 생성

- 리포트 페이지에서 "리포트 생성" 클릭
- **콘솔 로그 확인:** `🎯 최신 배치 자동 선택: batch_id=1`
- **결과:** 3개 파일 통합 리포트 생성됨 ✅

---

## 🔑 핵심 변경사항

| 항목         | 변경 전               | 변경 후                   |
| ------------ | --------------------- | ------------------------- |
| **API 호출** | `/api/upload` × N번   | `/api/upload/batch` × 1번 |
| **FormData** | `'file'` (단수) × N번 | `'files'` (복수) × 1번    |
| **batch_id** | NULL (개별 파일)      | 생성됨 (그룹)             |
| **자동분류** | 마지막 파일만         | 전체 파일 통합 ✅         |
| **리포트**   | 마지막 파일만         | 전체 파일 통합 ✅         |

---

## 💡 추가 개선 가능 사항 (향후)

### 1. 배치 이름 입력 UI

```html
<!-- upload.html에 추가 -->
<div class="batch-name-input" style="margin-bottom: 15px;">
  <label>배치 이름 (선택)</label>
  <input type="text" id="batchName" placeholder="예: 2024년 1분기 데이터" />
</div>
```

```javascript
// upload.js에서 사용
const batchName = document.getElementById("batchName").value;
formData.append(
  "batch_name",
  batchName || `업로드 ${new Date().toLocaleString("ko-KR")}`
);
```

### 2. 진행률 표시 개선

```javascript
// 각 파일별 업로드 진행률 표시
formData.append("files", file1);
formData.append("files", file2);
formData.append("files", file3);

// 진행률: 33% → 66% → 100%
```

### 3. 에러 처리 강화

```javascript
if (data.data.errors && data.data.errors.length > 0) {
  console.warn("일부 파일 업로드 실패:", data.data.errors);
  // 실패한 파일 목록 표시
}
```

---

## 📚 관련 문서

1. [배치 업로드 가이드](./batch_upload_guide.md)
2. [마지막 파일만 처리되는 문제 해결](./BATCH_FIX_SUMMARY.md)
3. [구현 완료 보고서](./IMPLEMENTATION_SUMMARY.md)

---

**작성일:** 2025-10-20  
**버전:** 1.0
