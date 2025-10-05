# 분류 엔진 전환 가이드

ClaraCS는 두 가지 분류 엔진을 지원합니다:

1. **규칙 기반** (Rule-based) - 빠르고 간단
2. **AI 기반** (Hugging Face) - 정확하지만 느림

---

## 📁 파일 구조 설명

### **1. `utils/classifiers/base_classifier.py`**

**역할:** 모든 분류 엔진의 인터페이스 정의

```python
class BaseClassifier(ABC):
    @abstractmethod
    def classify_ticket(ticket) -> dict:
        """티켓 분류 (필수 구현)"""
        pass

    @abstractmethod
    def get_engine_name() -> str:
        """엔진 이름 반환 (필수 구현)"""
        pass
```

**특징:**

- 추상 클래스로 모든 분류기가 따라야 하는 규칙 정의
- 새로운 분류 엔진 추가 시 이 인터페이스만 구현하면 됨

---

### **2. `utils/classifiers/rule_based_classifier.py`**

**역할:** inquiry_type 필드 기반 규칙 분류

**동작 방식:**

```
1. inquiry_type 필드 확인
   '배송' → '배송 문의' (신뢰도 0.9)
   '환불' → '환불/교환' (신뢰도 0.9)

2. inquiry_type 매칭 실패 시 본문/제목 키워드 분석
   본문에 '배송', '택배' 포함 → '배송 문의' (신뢰도 0.5~0.8)

3. 모두 실패 시 '기타' (신뢰도 0.5)
```

**장점:**

- ✅ 빠른 속도 (수천 건 처리 가능)
- ✅ 외부 의존성 없음
- ✅ 예측 가능한 결과

**단점:**

- ❌ 정확도가 떨어질 수 있음
- ❌ 새로운 패턴 학습 불가
- ❌ 복잡한 문맥 이해 불가

---

### **3. `utils/classifiers/ai_classifier.py`**

**역할:** Hugging Face Transformers 기반 AI 분류

**동작 방식:**

```
1. 사전 학습된 한국어 BERT 모델 로딩
   - beomi/kcbert-base (추천)
   - klue/bert-base

2. Zero-shot classification
   본문 텍스트 → 모델 추론 → 카테고리 확률 계산

3. 가장 높은 확률의 카테고리 선택
```

**장점:**

- ✅ 높은 정확도
- ✅ 문맥 이해 가능
- ✅ 새로운 표현 처리 가능

**단점:**

- ❌ 느린 속도 (GPU 권장)
- ❌ 외부 라이브러리 필요 (transformers, torch)
- ❌ 메모리 사용량 많음 (~2GB)

---

### **4. `services/auto_classify.py`**

**역할:** 분류 비즈니스 로직 + 엔진 선택

**분기 처리 위치:**

```python
# 파일 상단 (17~26줄)
USE_RULE_BASED = True  # ← 여기서 엔진 선택!

# 분류기 초기화 (49~73줄)
if self.use_rule_based:
    self.classifier = RuleBasedClassifier(...)  # 규칙 기반
else:
    self.classifier = AIClassifier(...)         # AI 기반
```

---

## 🔄 엔진 전환 방법

### **방법 1: 규칙 기반 → AI 기반으로 전환**

#### Step 1: 필수 라이브러리 설치

```bash
pip install transformers torch
```

#### Step 2: `services/auto_classify.py` 파일 수정

**Before (규칙 기반 - 현재):**

```python
# 17~26줄
# ============================================================
# 분류 엔진 선택 (주석 처리로 분기)
# ============================================================
# 규칙 기반 (현재 활성화) - 빠르고 간단
USE_RULE_BASED = True

# AI 기반 (주석 해제 시 활성화) - 정확하지만 느림
# Hugging Face Transformers 필요: pip install transformers torch
# USE_RULE_BASED = False
# ============================================================
```

**After (AI 기반):**

```python
# 17~26줄
# ============================================================
# 분류 엔진 선택 (주석 처리로 분기)
# ============================================================
# 규칙 기반 (현재 활성화) - 빠르고 간단
# USE_RULE_BASED = True

# AI 기반 (주석 해제 시 활성화) - 정확하지만 느림
# Hugging Face Transformers 필요: pip install transformers torch
USE_RULE_BASED = False
# ============================================================
```

#### Step 3: import 문 수정

**Before:**

```python
# 2줄
from utils.classifiers import RuleBasedClassifier  # , AIClassifier
```

**After:**

```python
# 2줄
from utils.classifiers import RuleBasedClassifier, AIClassifier
```

#### Step 4: 초기화 코드 주석 해제

**Before (49~73줄):**

```python
if self.use_rule_based:
    logger.info("규칙 기반 분류 엔진 사용")
    self.classifier = RuleBasedClassifier(category_mapping)
else:
    # from utils.classifiers import AIClassifier
    # logger.info("AI 기반 분류 엔진 사용 (Hugging Face)")
    # self.classifier = AIClassifier(
    #     model_name='beomi/kcbert-base',
    #     category_mapping=category_mapping
    # )
    raise NotImplementedError(...)
```

**After:**

```python
if self.use_rule_based:
    logger.info("규칙 기반 분류 엔진 사용")
    self.classifier = RuleBasedClassifier(category_mapping)
else:
    from utils.classifiers import AIClassifier
    logger.info("AI 기반 분류 엔진 사용 (Hugging Face)")
    self.classifier = AIClassifier(
        model_name='beomi/kcbert-base',
        category_mapping=category_mapping
    )
```

#### Step 5: 애플리케이션 재시작

```bash
python app.py
```

---

### **방법 2: AI 기반 → 규칙 기반으로 전환**

위 과정을 역순으로 수행:

1. `USE_RULE_BASED = False` → `USE_RULE_BASED = True`
2. AI 초기화 코드 주석 처리
3. 앱 재시작

---

## 🧪 테스트 방법

### 규칙 기반 테스트

```bash
# 1. 애플리케이션 실행
python app.py

# 2. 데이터 업로드
# http://localhost:5000/upload

# 3. 자동 분류 실행
# http://localhost:5000/classify → "분류 실행" 버튼

# 4. 로그 확인
# 콘솔에서 "규칙 기반 분류 엔진 사용" 메시지 확인
```

### AI 기반 테스트

```bash
# 1. 라이브러리 설치
pip install transformers torch

# 2. services/auto_classify.py 수정 (위 참조)

# 3. 애플리케이션 실행 (최초 실행 시 모델 다운로드 ~500MB)
python app.py

# 4. 자동 분류 실행
# 로그에서 "AI 기반 분류 엔진 사용" 확인
# "Hugging Face 모델 로딩 중" 메시지 확인
```

---

## 📊 성능 비교

| 항목          | 규칙 기반      | AI 기반 (Hugging Face)                 |
| ------------- | -------------- | -------------------------------------- |
| **처리 속도** | 1000건/초      | 10~50건/초 (CPU)<br>100~200건/초 (GPU) |
| **정확도**    | 70~85%         | 85~95%                                 |
| **메모리**    | ~100MB         | ~2GB                                   |
| **초기 설정** | 즉시 사용 가능 | 모델 다운로드 필요 (~500MB)            |
| **의존성**    | 없음           | transformers, torch                    |
| **GPU 필요**  | 아니오         | 선택 (권장)                            |

---

## 🛠️ AI 모델 옵션

### 한국어 추천 모델

#### 1. `beomi/kcbert-base` (기본값)

```python
AIClassifier(model_name='beomi/kcbert-base')
```

- 한국어 BERT 베이스
- 범용 용도
- 크기: ~500MB

#### 2. `klue/bert-base`

```python
AIClassifier(model_name='klue/bert-base')
```

- KLUE 벤치마크 학습
- 한국어 이해 우수
- 크기: ~500MB

#### 3. `BM-K/KoSimCSE-roberta-multitask`

```python
AIClassifier(model_name='BM-K/KoSimCSE-roberta-multitask')
```

- 의미 유사도 특화
- 문맥 이해 우수
- 크기: ~500MB

---

## 🚀 성능 최적화 팁

### GPU 사용 (권장)

```bash
# CUDA 설치 확인
python -c "import torch; print(torch.cuda.is_available())"

# GPU 사용 시 20~30배 빠름
```

### 배치 처리

```python
# utils/classifiers/ai_classifier.py 수정
def classify_batch(self, tickets: List[Dict]) -> List[Dict]:
    texts = [f"{t.get('title', '')} {t.get('body', '')}" for t in tickets]

    # 배치로 한번에 처리
    results = self.pipeline(
        texts,
        candidate_labels=self.category_labels,
        batch_size=16  # 배치 크기 조정
    )
    return results
```

### 모델 캐싱

```python
# 모델을 한번만 로딩하고 재사용
# AIClassifier가 이미 구현되어 있음 (지연 로딩)
```

---

## ❓ 문제 해결

### Q1. "transformers 라이브러리가 설치되지 않았습니다" 오류

```bash
pip install transformers torch
```

### Q2. AI 분류가 너무 느림

- GPU 사용 권장
- 또는 규칙 기반으로 전환

### Q3. 메모리 부족 오류

```python
# 작은 모델 사용
AIClassifier(model_name='beomi/kcbert-base')  # ~500MB
# 대신
AIClassifier(model_name='klue/roberta-small')  # ~200MB
```

### Q4. 모델 다운로드 실패

```bash
# 프록시 환경에서
export HF_ENDPOINT=https://huggingface.co

# 또는 수동 다운로드
# https://huggingface.co/beomi/kcbert-base
```

---

## 📚 참고 자료

- Hugging Face 모델 허브: https://huggingface.co/models
- Transformers 문서: https://huggingface.co/docs/transformers
- 한국어 NLP 가이드: https://github.com/younggyoseo/Awesome-Korean-NLP

---

## 🔮 향후 개선 방향

1. **Fine-tuning**: 실제 CS 데이터로 모델 재학습
2. **앙상블**: 규칙 기반 + AI 기반 결합
3. **A/B 테스트**: 두 엔진 성능 비교
4. **비용 최적화**: 간단한 케이스는 규칙, 복잡한 케이스만 AI

---

이제 엔진 전환이 주석 처리만으로 가능합니다! 🚀
