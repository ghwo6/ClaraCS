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
        
        # 키워드 추출 패턴
        self.keyword_patterns = {
            '배송': ['배송', '택배', '운송', '배달', '지연', '추적', '도착'],
            '환불/교환': ['환불', '교환', '반품', '취소', '결제', '승인', '카드'],
            '상품 문의': ['상품', '제품', '스펙', '정보', '재고', '가격', '할인'],
            '기술 지원': ['사용법', '고장', '오작동', 'AS', '수리', '설치', '기사'],
            '불만/클레임': ['불만', '클레임', '화남', '불량', '파손', '품질', '하자'],
            '기타': ['문의', '확인', '안내', '질문']
        }
    
    def _build_inquiry_rules(self) -> Dict[str, str]:
        """inquiry_type 문자열 -> category_name 매핑 규칙 생성"""
        return {
            # 배송 관련
            '배송': '배송 문의',
            '배송문의': '배송 문의',
            '배송지연': '배송 문의',
            '배송추적': '배송 문의',
            '택배': '배송 문의',
            '운송': '배송 문의',
            
            # 환불/교환 관련
            '환불': '환불/교환',
            '교환': '환불/교환',
            '반품': '환불/교환',
            '취소': '환불/교환',
            '결제취소': '환불/교환',
            
            # 상품 문의
            '상품문의': '상품 문의',
            '제품문의': '상품 문의',
            '재고문의': '상품 문의',
            '가격문의': '상품 문의',
            
            # 기술 지원
            '기술지원': '기술 지원',
            'AS': '기술 지원',
            '설치': '기술 지원',
            '사용법': '기술 지원',
            '고장': '기술 지원',
            '수리': '기술 지원',
            
            # 불만/클레임
            '불만': '불만/클레임',
            '클레임': '불만/클레임',
            '불량': '불만/클레임',
            '파손': '불만/클레임',
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
        본문/제목 키워드 기반 분류 (매칭된 키워드도 함께 반환)
        
        Returns:
            (category_name, confidence, matched_keywords)
        """
        text = (body + ' ' + title).lower()
        
        category_scores = {}
        category_matched_keywords = {}  # 카테고리별 매칭된 키워드 저장
        
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
            # 가장 많이 매칭된 카테고리 선택
            best_category = max(category_scores, key=category_scores.get)
            max_score = category_scores[best_category]
            confidence = min(0.8, 0.5 + (max_score * 0.1))  # 최대 0.8
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

