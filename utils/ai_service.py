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
    
    def generate_comprehensive_report(self, cs_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CS 데이터 기반 종합 리포트 생성 (데이터 요약, 인사이트, 솔루션 통합)
        
        Args:
            cs_data: CS 분석 데이터 (카테고리, 채널, 해결률 등)
            
        Returns:
            종합 리포트 (summary, insight, overall_insight, solution)
        """
        logger.info("종합 리포트 생성 시작")
        
        try:
            # 프롬프트 구성
            prompt = self._build_comprehensive_report_prompt(cs_data)
            
            # OpenAI API 호출
            response = self._call_openai_api(prompt, max_tokens=3000)
            
            # 응답 파싱
            report = self._parse_comprehensive_report_response(response)
            
            logger.info("종합 리포트 생성 완료")
            return report
            
        except Exception as e:
            logger.error(f"종합 리포트 생성 실패: {e}")
            return self._get_fallback_comprehensive_report(cs_data)
    
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
    
    def _call_openai_api(self, prompt: str, max_tokens: int = 2000) -> str:
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
                max_tokens=max_tokens,
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
    
    def _build_comprehensive_report_prompt(self, cs_data: Dict[str, Any]) -> str:
        """종합 리포트 생성용 프롬프트 구성"""
        
        # CS 데이터를 읽기 쉬운 형식으로 변환
        total_tickets = cs_data.get('total_tickets', 0)
        
        # 카테고리별 분포
        category_info = ""
        for cat in cs_data.get('category_distribution', []):
            category_info += f"- {cat['category_name']}: {cat['count']}건 ({cat['percentage']}%)\n"
        
        # 채널별 분포
        channel_info = ""
        for ch in cs_data.get('channel_distribution', []):
            channel_info += f"- {ch['channel']}: {ch['count']}건 ({ch['percentage']}%)\n"
        
        # 채널별 해결률
        resolution_info = ""
        for res in cs_data.get('channel_resolution_rates', []):
            resolution_info += f"- {res['channel']}: {res['resolution_rate']}% (해결 {res['resolved']}건 / 전체 {res['total']}건)\n"
        
        prompt = f"""당신은 고객 CS 데이터를 분석하여 자동 분류 및 솔루션을 제안하는 AI 서비스의 분석 전문가입니다.

다음 데이터를 기반으로 아래 4가지 항목에 대해 JSON 형식으로 응답해 주세요. 각 항목은 key-value 구조로 구성해 주세요.

**CS 데이터:**
- 전체 CS 건수: {total_tickets}건

**카테고리별 분포:**
{category_info}

**채널별 분포:**
{channel_info}

**채널별 해결률:**
{resolution_info}

---

**응답 형식:**

다음 4가지 항목을 포함한 JSON 형식으로 응답해주세요:

1. **summary**: 전체 CS 건수, 카테고리별 비율, 채널별 해결률
   - total_cs_count (전체 건수)
   - category_ratio (카테고리별 비율, 상위 3~5개만)
   - resolution_rate (채널별 해결률)

2. **insight**: 카테고리별 문제점과 단기/장기 개선 방안
   - 각 주요 카테고리에 대해:
     - issue: 문제점
     - short_term: 단기 개선 방안
     - long_term: 장기 개선 방안

3. **overall_insight**: 단기/장기/특이사항 관점에서 종합 인사이트
   - short_term: 단기적 종합 전략
   - long_term: 장기적 종합 전략
   - notable: 특이사항 (반복 문의, 긴급 이슈 등)

4. **solution**: 단기(1~6개월)/장기(6개월~2년) 전략 제안
   - short_term: 배열 형태로 여러 제안
     - suggestion: 제안 내용
     - expected_effect: 기대 효과
   - long_term: 배열 형태로 여러 제안
     - suggestion: 제안 내용
     - expected_effect: 기대 효과

**중요**: 반드시 순수한 JSON 형식으로만 응답하세요. 추가 설명이나 마크다운 코드 블록(```)은 포함하지 마세요.

예시 JSON 구조:
{{
  "summary": {{
    "total_cs_count": {total_tickets},
    "category_ratio": {{
      "카테고리1": "40%",
      "카테고리2": "35%"
    }},
    "resolution_rate": {{
      "채널1": "70%",
      "채널2": "85%"
    }}
  }},
  "insight": {{
    "카테고리1": {{
      "issue": "문제점 설명",
      "short_term": "단기 해결 방안",
      "long_term": "장기 해결 방안"
    }}
  }},
  "overall_insight": {{
    "short_term": "단기 종합 전략",
    "long_term": "장기 종합 전략",
    "notable": "특이사항"
  }},
  "solution": {{
    "short_term": [
      {{"suggestion": "제안1", "expected_effect": "효과1"}},
      {{"suggestion": "제안2", "expected_effect": "효과2"}}
    ],
    "long_term": [
      {{"suggestion": "제안1", "expected_effect": "효과1"}}
    ]
  }}
}}
"""
        return prompt
    
    def _parse_comprehensive_report_response(self, response: str) -> Dict[str, Any]:
        """종합 리포트 응답 파싱"""
        try:
            # JSON 코드 블록 제거 (```json ... ``` 형식)
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            # JSON 파싱
            report = json.loads(response)
            
            # 필수 키 검증
            required_keys = ['summary', 'insight', 'overall_insight', 'solution']
            for key in required_keys:
                if key not in report:
                    logger.warning(f"필수 키 '{key}'가 응답에 없습니다.")
                    report[key] = {}
            
            return report
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}")
            logger.error(f"원본 응답: {response[:500]}")
            return self._get_fallback_comprehensive_report({})
        except Exception as e:
            logger.error(f"응답 파싱 중 오류: {e}")
            return self._get_fallback_comprehensive_report({})
    
    def _get_fallback_comprehensive_report(self, cs_data: Dict[str, Any]) -> Dict[str, Any]:
        """API 실패 시 대체 리포트"""
        total_tickets = cs_data.get('total_tickets', 0)
        
        # 카테고리별 비율 추출
        category_ratio = {}
        for cat in cs_data.get('category_distribution', [])[:3]:
            category_ratio[cat['category_name']] = f"{cat['percentage']}%"
        
        # 채널별 해결률 추출
        resolution_rate = {}
        for res in cs_data.get('channel_resolution_rates', []):
            resolution_rate[res['channel']] = f"{res['resolution_rate']}%"
        
        return {
            "summary": {
                "total_cs_count": total_tickets,
                "category_ratio": category_ratio if category_ratio else {"분석 중": "0%"},
                "resolution_rate": resolution_rate if resolution_rate else {"분석 중": "0%"}
            },
            "insight": {
                "일반": {
                    "issue": "AI 분석 서비스가 일시적으로 사용할 수 없습니다",
                    "short_term": "수동 분석 또는 재시도",
                    "long_term": "시스템 안정성 개선"
                }
            },
            "overall_insight": {
                "short_term": "AI 분석 서비스 복구 후 재실행 권장",
                "long_term": "안정적인 분석 시스템 구축",
                "notable": "일시적 서비스 장애"
            },
            "solution": {
                "short_term": [
                    {"suggestion": "AI 서비스 재시도", "expected_effect": "정상 분석 결과 획득"}
                ],
                "long_term": [
                    {"suggestion": "백업 분석 시스템 구축", "expected_effect": "서비스 안정성 향상"}
                ]
            }
        }

# 싱글톤 인스턴스
ai_service = AIService()
