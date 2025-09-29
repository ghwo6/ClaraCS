import openai
import json
from typing import Dict, List, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class AIService:
    """OpenAI ChatGPT 연동 서비스 클래스"""
    
    def __init__(self, api_key: str = None):
        """
        AI 서비스 초기화
        
        Args:
            api_key: OpenAI API 키 (환경변수에서 자동 로드 가능)
        """
        self.api_key = api_key or self._get_api_key()
        if self.api_key:
            openai.api_key = self.api_key
        else:
            logger.warning("OpenAI API 키가 설정되지 않았습니다. 환경변수 OPENAI_API_KEY를 설정하세요.")
    
    def _get_api_key(self) -> Optional[str]:
        """환경변수에서 API 키 가져오기"""
        import os
        return os.getenv('OPENAI_API_KEY')
    
    def analyze_cs_insights(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CS 데이터 인사이트 분석
        
        Args:
            analysis_data: 분석할 데이터 (티켓 요약, 분류 데이터, 트렌드 등)
            
        Returns:
            분석 결과 (인사이트, 솔루션 제안 등)
        """
        logger.info("CS 데이터 인사이트 분석 시작")
        
        try:
            # 프롬프트 구성
            prompt = self._build_analysis_prompt(analysis_data)
            
            # OpenAI API 호출
            response = self._call_openai_api(prompt)
            
            # 응답 파싱
            insights = self._parse_analysis_response(response)
            
            logger.info("CS 데이터 인사이트 분석 완료")
            return insights
            
        except Exception as e:
            logger.error(f"CS 데이터 인사이트 분석 실패: {e}")
            return self._get_fallback_insights()
    
    def generate_solution_recommendations(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        솔루션 제안 생성
        
        Args:
            insights: 인사이트 분석 결과
            
        Returns:
            솔루션 제안 결과
        """
        logger.info("솔루션 제안 생성 시작")
        
        try:
            prompt = self._build_solution_prompt(insights)
            response = self._call_openai_api(prompt)
            solutions = self._parse_solution_response(response)
            
            logger.info("솔루션 제안 생성 완료")
            return solutions
            
        except Exception as e:
            logger.error(f"솔루션 제안 생성 실패: {e}")
            return self._get_fallback_solutions()
    
    def _build_analysis_prompt(self, analysis_data: Dict[str, Any]) -> str:
        """인사이트 분석용 프롬프트 구성"""
        prompt = f"""
다음 CS 데이터를 분석하여 인사이트를 도출해주세요.

데이터 요약:
- 총 티켓 수: {len(analysis_data.get('ticket_summaries', []))}
- 카테고리 분포: {analysis_data.get('trend_analysis', {}).get('category_trends', {})}
- 감정 분석: {analysis_data.get('issue_patterns', {}).get('sentiment_analysis', {})}

주요 키워드:
{analysis_data.get('issue_patterns', {}).get('top_keywords', {})}

문제가 많은 카테고리:
{analysis_data.get('issue_patterns', {}).get('problem_categories', {})}

다음 형식으로 분석 결과를 제공해주세요:
1. 주요 인사이트 (3-5개)
2. 문제점 식별
3. 개선 기회
4. 우선순위 제안

JSON 형식으로 응답해주세요:
{{
    "insights": [
        {{"title": "인사이트 제목", "description": "상세 설명", "priority": "high/medium/low"}}
    ],
    "problems": [
        {{"category": "문제 카테고리", "description": "문제 설명", "impact": "영향도"}}
    ],
    "opportunities": [
        {{"area": "개선 영역", "description": "개선 방안", "expected_impact": "예상 효과"}}
    ]
}}
"""
        return prompt
    
    def _build_solution_prompt(self, insights: Dict[str, Any]) -> str:
        """솔루션 제안용 프롬프트 구성"""
        prompt = f"""
다음 인사이트를 바탕으로 구체적인 솔루션을 제안해주세요.

인사이트:
{json.dumps(insights, ensure_ascii=False, indent=2)}

다음 영역별로 솔루션을 제안해주세요:
1. 매크로/자동화 솔루션
2. 프로세스 개선 솔루션  
3. 제품/서비스 개선 솔루션
4. 고객 경험 개선 솔루션

각 솔루션은 다음 정보를 포함해주세요:
- 솔루션명
- 구체적인 실행 방안
- 예상 효과
- 구현 난이도
- 우선순위

JSON 형식으로 응답해주세요:
{{
    "solutions": [
        {{
            "category": "솔루션 카테고리",
            "name": "솔루션명",
            "description": "상세 설명",
            "implementation": "구현 방안",
            "expected_impact": "예상 효과",
            "difficulty": "easy/medium/hard",
            "priority": "high/medium/low"
        }}
    ],
    "recommendations": [
        {{
            "title": "권고사항 제목",
            "description": "권고사항 설명",
            "timeline": "실행 일정",
            "resources": "필요 자원"
        }}
    ]
}}
"""
        return prompt
    
    def _call_openai_api(self, prompt: str) -> str:
        """OpenAI API 호출"""
        if not self.api_key:
            raise Exception("OpenAI API 키가 설정되지 않았습니다.")
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 CS 데이터 분석 전문가입니다. 정확하고 실용적인 인사이트와 솔루션을 제공해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {e}")
            raise
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """분석 응답 파싱"""
        try:
            # JSON 응답 파싱 시도
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                # JSON이 아닌 경우 기본 구조로 변환
                return self._parse_text_response(response, 'analysis')
        except json.JSONDecodeError:
            logger.warning("JSON 파싱 실패, 텍스트 응답으로 처리")
            return self._parse_text_response(response, 'analysis')
    
    def _parse_solution_response(self, response: str) -> Dict[str, Any]:
        """솔루션 응답 파싱"""
        try:
            if response.strip().startswith('{'):
                return json.loads(response)
            else:
                return self._parse_text_response(response, 'solution')
        except json.JSONDecodeError:
            logger.warning("JSON 파싱 실패, 텍스트 응답으로 처리")
            return self._parse_text_response(response, 'solution')
    
    def _parse_text_response(self, response: str, response_type: str) -> Dict[str, Any]:
        """텍스트 응답을 구조화된 데이터로 변환"""
        if response_type == 'analysis':
            return {
                "insights": [
                    {"title": "주요 인사이트", "description": response[:200] + "...", "priority": "medium"}
                ],
                "problems": [
                    {"category": "일반", "description": "데이터 분석 중", "impact": "중간"}
                ],
                "opportunities": [
                    {"area": "전반적", "description": "개선 기회 식별 중", "expected_impact": "긍정적"}
                ]
            }
        else:  # solution
            return {
                "solutions": [
                    {
                        "category": "일반",
                        "name": "솔루션 제안",
                        "description": response[:200] + "...",
                        "implementation": "단계별 실행",
                        "expected_impact": "개선 예상",
                        "difficulty": "medium",
                        "priority": "medium"
                    }
                ],
                "recommendations": [
                    {
                        "title": "권고사항",
                        "description": "추가 검토 필요",
                        "timeline": "1-2주",
                        "resources": "기본 자원"
                    }
                ]
            }
    
    def _get_fallback_insights(self) -> Dict[str, Any]:
        """API 실패 시 대체 인사이트"""
        return {
            "insights": [
                {
                    "title": "데이터 분석 중",
                    "description": "AI 분석 서비스가 일시적으로 사용할 수 없습니다. 기본 분석을 제공합니다.",
                    "priority": "medium"
                }
            ],
            "problems": [
                {
                    "category": "서비스",
                    "description": "AI 분석 서비스 연결 문제",
                    "impact": "낮음"
                }
            ],
            "opportunities": [
                {
                    "area": "시스템",
                    "description": "AI 서비스 안정성 개선",
                    "expected_impact": "높음"
                }
            ]
        }
    
    def _get_fallback_solutions(self) -> Dict[str, Any]:
        """API 실패 시 대체 솔루션"""
        return {
            "solutions": [
                {
                    "category": "시스템",
                    "name": "AI 서비스 복구",
                    "description": "AI 분석 서비스를 복구하여 정상적인 인사이트를 제공합니다.",
                    "implementation": "시스템 관리자 문의",
                    "expected_impact": "높음",
                    "difficulty": "easy",
                    "priority": "high"
                }
            ],
            "recommendations": [
                {
                    "title": "대안 분석",
                    "description": "기본 통계 분석을 활용한 인사이트 제공",
                    "timeline": "즉시",
                    "resources": "기본 자원"
                }
            ]
        }

# 싱글톤 인스턴스
ai_service = AIService()
