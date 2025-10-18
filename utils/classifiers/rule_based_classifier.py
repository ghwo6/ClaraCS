"""
규칙 기반 분류 엔진
inquiry_type 필드를 기반으로 카테고리 매핑
"""
from typing import Dict, List, Any
from .base_classifier import BaseClassifier
from utils.logger import get_logger
import re

logger = get_logger(__name__)


class RuleBasedClassifier(BaseClassifier):
    """inquiry_type 기반 규칙 분류 엔진"""
    
    def __init__(self, category_mapping: Dict[int, str] = None):
        """
        Args:
            category_mapping: {category_id: category_name} 딕셔너리
        """
        self.category_mapping = category_mapping or {}
        self.reverse_mapping = {v: k for k, v in self.category_mapping.items()}
        
        # inquiry_type -> category_name 매핑 규칙
        self.inquiry_rules = self._build_inquiry_rules()
        
        # 키워드 추출 패턴 (우선순위 기반 - 1순위부터 8순위까지)
        # 우선순위가 높은 카테고리가 먼저 검사됨
        self.keyword_patterns = {
            # 1순위: 품질/하자 (최우선 분류)
            '품질/하자': [
                '불량', '하자', '파손', '오작동', '작동안됨', '깨짐', '스크래치', '찢어짐', 
                '변색', '눌림', '결함', '이상', '고장', '문제있음', '기능이상', '동작불량', 
                '얼룩', '누수', '냄새남', '부품빠짐', '마감불량', '교환요청', '교체', 
                '새상품아님', '사용불가', '작동안함', '틀어짐', '불완전', '부식', '기스', 
                '품질문제', '소리남', '흔들림', '접착불량', '터짐', '불안정', '내부손상', '외관불량'
            ],
            
            # 2순위: 서비스
            '서비스': [
                '불친절', '친절', '응대', '태도', '무례', '성의없음', '느림', '처리늦음', 
                '답변없음', '전화안받음', '상담불만', '대응', '고객센터', '안내미흡', 
                '소통불가', '대화불편', '통화불가', '불만접수', '기분나쁨', '직원태도', 
                '안내잘못', '무시당함', '답변지연', '응대속도', '서비스불만', '불성실', 
                '고객응대', '응답없음', '소극적', '안내부족', '응대태도', '불쾌', '무성의'
            ],
            
            # 3순위: 배송
            '배송': [
                '배송', '지연', '늦음', '안옴', '언제와요', '출고', '발송', '물류', '택배', 
                '택배사', '배송조회', '운송장', '분실', '누락', '미도착', '주소', '수취인', 
                '배달', '도착', '배송중', '출발', '물건이없어요', '잘못배송', '다른사람에게감', 
                '반송', '재배송', '기사님', '연락안됨', '배송문자', '배송상태', '물류센터', 
                '배달사고', '배송오류', '택배지연', '송장오류', '배달지연', '배송누락', '배송불가', '배송문제'
            ],
            
            # 4순위: AS/수리
            'AS/수리': [
                'AS', '수리', '보증', '점검', '교체', '서비스센터', '수리요청', '부품', 
                '무상수리', '유상수리', '고장수리', '방문수리', '수리불가', '센터', 
                '수리신청', '보증기간', '점검요청', '수리상태', '수리완료', '수리비', 
                '수리기간', '수리지연', '기술자', '수리센터', '대리점', '교체요청', 
                '점검필요', '제품수리', '부품교체', '보증서', '고장수리요청', 'A/S요청', 
                'A/S접수', 'A/S센터'
            ],
            
            # 5순위: 결제
            '결제': [
                '결제', '입금', '환불', '취소', '승인', '카드', '이체', '결제실패', 
                '중복결제', '미결제', '자동결제', '환불요청', '결제취소', '금액틀림', 
                '금액오류', '포인트', '결제안됨', '결제오류', '입금확인', '환불지연', 
                '환불처리', '환불안됨', '부분취소', '결제내역', '카드승인', '결제취소요청', 
                '영수증', '결제완료', '결제취소불가', '환불계좌', '결제확인', '입금오류', '결제문제'
            ],
            
            # 6순위: 이벤트
            '이벤트': [
                '이벤트', '쿠폰', '할인', '프로모션', '사은품', '적립금', '경품', '행사', 
                '이벤트참여', '쿠폰사용', '쿠폰등록', '쿠폰오류', '쿠폰안됨', '이벤트신청', 
                '응모', '당첨', '미당첨', '혜택', '이벤트기간', '쿠폰발급', '이벤트코드', 
                '쿠폰만료', '쿠폰지급', '쿠폰문의', '사은품누락', '할인쿠폰', '쿠폰적용', '이벤트참여방법'
            ],
            
            # 7순위: 일반
            '일반': [
                '문의', '안내', '확인', '사용법', '방법', '어떻게', '알려주세요', '문의드립니다', 
                '공지', '단순변심', '변경요청', '확인요청', '사용문의', '제품문의', '정보요청', 
                '설명서', '매뉴얼', '연락처', '계정문의', '시간문의', '배송문의', '단순문의', 
                '제품확인', '등록방법', '계정변경', '사용설명', '고객정보', '접속안됨', 
                '로그인', '로그아웃', '비밀번호', '아이디', '등록안됨'
            ],
            
            # 8순위: 기타 (아무 키워드에도 매칭되지 않을 때)
            '기타': []
        }
        
        # 카테고리 우선순위 정의
        self.category_priority = [
            '품질/하자',    # 1순위
            '서비스',       # 2순위
            '배송',         # 3순위
            'AS/수리',      # 4순위
            '결제',         # 5순위
            '이벤트',       # 6순위
            '일반',         # 7순위
            '기타'          # 8순위
        ]
    
    def _build_inquiry_rules(self) -> Dict[str, str]:
        """inquiry_type 문자열 -> category_name 매핑 규칙 생성"""
        return {
            # 품질/하자 관련
            '품질': '품질/하자',
            '하자': '품질/하자',
            '불량': '품질/하자',
            '파손': '품질/하자',
            '오작동': '품질/하자',
            '고장': '품질/하자',
            '결함': '품질/하자',
            
            # 서비스 관련
            '서비스': '서비스',
            '응대': '서비스',
            '상담': '서비스',
            '고객센터': '서비스',
            '불친절': '서비스',
            
            # 배송 관련
            '배송': '배송',
            '배송문의': '배송',
            '배송지연': '배송',
            '배송추적': '배송',
            '택배': '배송',
            '운송': '배송',
            '물류': '배송',
            
            # AS/수리 관련
            'AS': 'AS/수리',
            '수리': 'AS/수리',
            '보증': 'AS/수리',
            '점검': 'AS/수리',
            '서비스센터': 'AS/수리',
            
            # 결제 관련
            '결제': '결제',
            '입금': '결제',
            '환불': '결제',
            '취소': '결제',
            '결제취소': '결제',
            
            # 이벤트 관련
            '이벤트': '이벤트',
            '쿠폰': '이벤트',
            '할인': '이벤트',
            '프로모션': '이벤트',
            
            # 일반 관련
            '일반문의': '일반',
            '단순문의': '일반',
            '확인요청': '일반',
        }
    
    def classify_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        티켓 분류 (inquiry_type 기반)
        
        Args:
            ticket: 티켓 데이터
            
        Returns:
            분류 결과
        """
        inquiry_type = (ticket.get('inquiry_type') or '').strip()
        body = ticket.get('body') or ''
        title = ticket.get('title') or ''
        
        # 1. inquiry_type으로 카테고리 매핑 시도
        category_name = None
        confidence = 0.0
        matched_keywords = []  # 실제로 매칭된 키워드 수집
        
        if inquiry_type:
            # 정확히 매칭
            category_name = self.inquiry_rules.get(inquiry_type)
            
            # 부분 매칭 시도
            if not category_name:
                inquiry_lower = inquiry_type.lower()
                for rule_key, rule_category in self.inquiry_rules.items():
                    if rule_key.lower() in inquiry_lower or inquiry_lower in rule_key.lower():
                        category_name = rule_category
                        matched_keywords.append(rule_key)  # 매칭된 규칙 저장
                        break
            
            if category_name:
                confidence = 0.9  # inquiry_type 매칭 시 높은 신뢰도
                if not matched_keywords:
                    matched_keywords.append(inquiry_type)  # inquiry_type 자체를 키워드로
        
        # 2. inquiry_type 매칭 실패 시 본문/제목 키워드 기반 추론
        if not category_name:
            category_name, confidence, matched_keywords = self._classify_by_keywords(body, title)
        
        # 3. 여전히 실패 시 '기타'로 분류
        if not category_name:
            category_name = '기타'
            confidence = 0.5
            matched_keywords = ['미분류']
        
        # 4. category_id 조회
        category_id = self.reverse_mapping.get(category_name)
        
        if not category_id:
            logger.warning(f"카테고리 '{category_name}'에 해당하는 ID를 찾을 수 없습니다. '기타'로 대체합니다.")
            category_name = '기타'
            category_id = self.reverse_mapping.get('기타', 6)  # 기타 기본값
            confidence = 0.3
            matched_keywords = ['오류']
        
        # 5. 키워드 정리 (중복 제거, 상위 5개)
        keywords = list(dict.fromkeys(matched_keywords))[:5]  # 중복 제거 + 순서 유지
        
        return {
            'category_id': category_id,
            'category_name': category_name,
            'confidence': confidence,
            'keywords': keywords,
            'method': 'rule_based',
            'original_inquiry_type': inquiry_type
        }
    
    def _classify_by_keywords(self, body: str, title: str) -> tuple:
        """
        본문/제목 키워드 기반 분류 (우선순위 기반 매칭)
        
        Returns:
            (category_name, confidence, matched_keywords)
        """
        text = (body + ' ' + title).lower()
        
        category_scores = {}
        category_matched_keywords = {}  # 카테고리별 매칭된 키워드 저장
        
        # 모든 카테고리에 대해 매칭 점수 계산
        for category, keywords in self.keyword_patterns.items():
            score = 0
            matched = []
            for keyword in keywords:
                if keyword in text:
                    score += 1
                    matched.append(keyword)  # 실제로 매칭된 키워드 저장
            if score > 0:
                category_scores[category] = score
                category_matched_keywords[category] = matched
        
        if category_scores:
            # 우선순위 기반 분류: 동점일 경우 우선순위가 높은 카테고리 선택
            # 1. 최고 점수 찾기
            max_score = max(category_scores.values())
            
            # 2. 최고 점수를 가진 카테고리들 중 우선순위가 가장 높은 것 선택
            candidates = [cat for cat, score in category_scores.items() if score == max_score]
            
            # 3. 우선순위 순서대로 확인
            best_category = None
            for priority_cat in self.category_priority:
                if priority_cat in candidates:
                    best_category = priority_cat
                    break
            
            # 4. 우선순위에 없는 경우 첫 번째 후보 선택 (fallback)
            if not best_category:
                best_category = candidates[0]
            
            confidence = min(0.9, 0.6 + (max_score * 0.05))  # 최대 0.9
            matched_keywords = category_matched_keywords[best_category]
            return best_category, confidence, matched_keywords
        
        return None, 0.0, []
    
    # _extract_keywords 메서드 제거 (더 이상 사용하지 않음)
    # 키워드는 분류 과정에서 실시간으로 수집됨
    
    def get_engine_name(self) -> str:
        """엔진 이름 반환"""
        return 'rule_based_v1'
    
    def set_category_mapping(self, category_mapping: Dict[int, str]):
        """카테고리 매핑 업데이트"""
        self.category_mapping = category_mapping
        self.reverse_mapping = {v: k for k, v in category_mapping.items()}
        logger.info(f"카테고리 매핑 업데이트: {len(category_mapping)}개")

