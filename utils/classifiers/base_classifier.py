"""
분류 엔진 베이스 클래스
모든 분류 엔진은 이 인터페이스를 구현해야 함
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseClassifier(ABC):
    """분류 엔진 인터페이스"""
    
    @abstractmethod
    def classify_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        개별 티켓 분류
        
        Args:
            ticket: 티켓 데이터 딕셔너리
                - ticket_id: int
                - body: str (본문)
                - title: str (제목)
                - inquiry_type: str (원본 문의 유형)
                - channel: str (채널)
                
        Returns:
            분류 결과 딕셔너리
            {
                'category_id': int,           # 분류된 카테고리 ID
                'category_name': str,         # 카테고리명
                'confidence': float,          # 신뢰도 (0.0 ~ 1.0)
                'keywords': List[str],        # 추출된 키워드
                'method': str                 # 분류 방법 (rule_based, ai, etc.)
            }
        """
        pass
    
    @abstractmethod
    def get_engine_name(self) -> str:
        """
        분류 엔진 이름 반환
        
        Returns:
            엔진 이름 (예: 'rule_based', 'gpt-4', 'claude-3')
        """
        pass
    
    def classify_batch(self, tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        여러 티켓 일괄 분류 (기본 구현: 순차 처리)
        하위 클래스에서 오버라이드하여 병렬 처리 등으로 최적화 가능
        
        Args:
            tickets: 티켓 리스트
            
        Returns:
            분류 결과 리스트
        """
        results = []
        for ticket in tickets:
            result = self.classify_ticket(ticket)
            results.append(result)
        return results

