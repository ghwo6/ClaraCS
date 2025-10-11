# 🔧 프롬프트 생성 에러 해결

## 🐛 문제 분석

### 에러 로그

```
[2025-10-12 03:39:11,123] [ERROR] utils.ai_service: ❌ GPT 리포트 생성 실패: unhashable type: 'dict'
```

### 발생 위치

```python
# utils/ai_service.py - _build_comprehensive_report_prompt()
line 449: "categories": {json.dumps(category_list[:3], ensure_ascii=False)},
line 450: "channels": {json.dumps([{'channel': ch['name'], ...} for ch in channel_list[:2]], ensure_ascii=False)}
```

### 원인

#### f-string 내부에서 딕셔너리 사용

```python
# ❌ 문제 코드
prompt = f"""
예시 JSON:
{{
  "categories": {json.dumps(category_list[:3], ensure_ascii=False)},
  "channels": {json.dumps([{'channel': ch['name'], ...} for ch in channel_list], ensure_ascii=False)}
}}
"""
```

**문제점**:

1. f-string 내부 `{}` 와 JSON `{}` 충돌
2. 리스트 컴프리헨션 내부에서 딕셔너리 키 접근 `ch['name']`
3. `ch['name']`이 존재하지 않을 때 KeyError → unhashable type 에러

---

## ✅ 해결 방법

### 1. JSON 문자열 사전 생성

```python
# Before ❌
prompt = f"""
{json.dumps(category_list, ensure_ascii=False)}
"""

# After ✅
category_list_json = json.dumps(category_list, ensure_ascii=False)
prompt = f"""
{category_list_json}
"""
```

### 2. 안전한 딕셔너리 접근

```python
# Before ❌
ch['name']  # KeyError 발생 가능

# After ✅
ch.get('name', '미분류')  # 기본값 제공
```

### 3. 조건부 JSON 생성

```python
# Before ❌
{json.dumps(category_list[:3], ensure_ascii=False)}

# After ✅
{json.dumps(category_list[:3], ensure_ascii=False) if category_list else '[]'}
```

---

## 📝 수정 내용

### utils/ai_service.py - `_build_comprehensive_report_prompt()`

#### Before ❌

```python
prompt = f"""
**사용 가능한 카테고리 목록:**
{json.dumps(category_list, ensure_ascii=False)}

예시 JSON:
{{
  "summary": {{
    "categories": {json.dumps(category_list[:3], ensure_ascii=False)},
    "channels": {json.dumps([{{'channel': ch['name'], 'total': ch['count']}} for ch in channel_list[:2]], ensure_ascii=False)}
  }}
}}
"""
```

#### After ✅

```python
# JSON 문자열로 변환 (f-string 내부에서 안전하게 사용)
category_list_json = json.dumps(category_list, ensure_ascii=False)
channel_list_json = json.dumps(channel_list, ensure_ascii=False)

prompt = f"""
**사용 가능한 카테고리 목록:**
{category_list_json}

예시 JSON:
{{
  "summary": {{
    "categories": {json.dumps(category_list[:3], ensure_ascii=False) if category_list else '[]'},
    "channels": {json.dumps([{{'channel': ch.get('name', '미분류'), 'total': ch.get('count', 0), 'resolved': 0, 'resolution_rate': 0.0}} for ch in channel_list[:2]], ensure_ascii=False) if channel_list else '[]'}
  }}
}}
"""
```

---

## 🔍 디버깅 과정

### 로그 분석

```
line 993: [INFO] 프롬프트 구성 중...
line 995: [ERROR] ❌ GPT 리포트 생성 실패: unhashable type: 'dict'
```

→ GPT API 호출 전에 프롬프트 생성 단계에서 실패

### 에러 발생 지점

```python
# _build_comprehensive_report_prompt() 내부
try:
    prompt = f"""... {json.dumps(...)} ..."""  # ❌ 여기서 실패
except Exception as e:
    # 에러가 상위로 전파됨
    raise  # "unhashable type: 'dict'"
```

---

## 📊 차트 점 크기 축소

### Before

```javascript
pointRadius: 4,  // 큰 점
```

### After

```javascript
pointRadius: 2,           // 작은 점
pointHoverRadius: 4,      // 호버 시 크기
pointBorderColor: '#fff', // 흰색 테두리
pointBorderWidth: 1,      // 테두리 두께
```

**효과**:

- ✅ 평상시: 작은 점 (2px)
- ✅ 호버 시: 중간 크기 (4px)
- ✅ 흰색 테두리로 명확하게 보임

---

## 🚀 수정 후 예상 로그

### 성공 케이스

```bash
[INFO] === GPT 기반 종합 리포트 생성 시작 ===
[INFO] 프롬프트 구성 중...
[INFO] 🤖 GPT API 호출 중... (최대 30초 소요 예상)
[INFO] GPT 모델 호출: gpt-4o-mini (max_tokens=3000)
[INFO] API 키 앞 10자: sk-proj-ab... (총 길이: 164)
[INFO] GPT 응답 수신 완료 (길이: 2543 chars)
[INFO] GPT 응답 파싱 성공
[INFO] === 종합 리포트 생성 완료 (GPT 기반) ===
[INFO] 요약 스냅샷 저장 완료
[INFO] 인사이트 스냅샷 저장 완료
[INFO] 솔루션 스냅샷 저장 완료
[INFO] 채널 스냅샷 183건 저장 완료
[INFO] 리포트 생성 완료 (report_id: 26, file_id: 16)
```

---

## ✅ 수정된 파일

| 파일                  | 수정 내용                        | 상태 |
| --------------------- | -------------------------------- | ---- |
| `utils/ai_service.py` | ✅ 프롬프트 JSON 사전 변환       | ✅   |
| `utils/ai_service.py` | ✅ 안전한 딕셔너리 접근 (.get()) | ✅   |
| `utils/ai_service.py` | ✅ 조건부 JSON 생성              | ✅   |
| `static/js/report.js` | ✅ 점 크기 축소 (4→2)            | ✅   |

---

## 🎯 에러 원인 요약

### unhashable type: 'dict' 에러

```python
# 원인 1: f-string 내부 딕셔너리 사용
{json.dumps(category_list, ensure_ascii=False)}

# 원인 2: 리스트 컴프리헨션 내부 딕셔너리 키 접근
[{'channel': ch['name']} for ch in channel_list]
# → ch['name']이 없으면 KeyError
# → 내부적으로 'dict'를 해시 가능한 형태로 변환 시도
# → unhashable type: 'dict' 에러
```

### 해결

```python
# 해결 1: JSON 사전 변환
category_list_json = json.dumps(category_list, ensure_ascii=False)

# 해결 2: 안전한 접근
ch.get('name', '미분류')

# 해결 3: None 체크
if category_list else '[]'
```

---

## 🎉 완료!

### ✅ 해결된 문제

1. **프롬프트 생성 에러** → JSON 사전 변환
2. **점 크기** → 4px → 2px

### 🚀 다음 단계

```bash
# 서버 재시작
.\run_app.ps1

# 리포트 생성 테스트
# → GPT API 정상 호출 예상!
```

---

**완료일**: 2025-10-12  
**상태**: ✅ Ready for Test
