"""
데이터베이스 연결 및 기능 테스트 스크립트
로컬 DB 연동이 제대로 되었는지 확인합니다.
"""

from utils.database import db_manager
from services.db.report_db import ReportDB
from services.report import ReportService

def test_db_connection():
    """DB 연결 테스트"""
    print("=" * 50)
    print("1. DB 연결 테스트")
    print("=" * 50)
    
    if db_manager.test_connection():
        print("✅ DB 연결 성공!")
        return True
    else:
        print("❌ DB 연결 실패")
        print("\n해결 방법:")
        print("1. MySQL 서비스가 실행 중인지 확인")
        print("2. .env 파일의 DB 정보가 올바른지 확인")
        print("3. database_schema.sql을 실행하여 DB를 생성했는지 확인")
        return False

def test_basic_queries():
    """기본 쿼리 테스트"""
    print("\n" + "=" * 50)
    print("2. 기본 쿼리 테스트")
    print("=" * 50)
    
    report_db = ReportDB()
    
    try:
        # 티켓 조회
        print("\n[티켓 데이터 조회]")
        tickets = report_db.get_cs_tickets_by_user('user_001')
        print(f"✅ 티켓 데이터 {len(tickets)}건 조회 성공")
        if len(tickets) > 0:
            print(f"   첫 번째 티켓: {tickets.iloc[0]['ticket_id']} - {tickets.iloc[0]['title']}")
        
        # 분류 데이터 조회
        print("\n[자동 분류 데이터 조회]")
        classified = report_db.get_classified_data_by_user('user_001')
        print(f"✅ 자동 분류 데이터 {len(classified)}건 조회 성공")
        if len(classified) > 0:
            print(f"   첫 번째 분류: {classified.iloc[0]['predicted_category']} (신뢰도: {classified.iloc[0]['confidence_score']:.2f})")
        
        return True
    except Exception as e:
        print(f"❌ 쿼리 실행 실패: {e}")
        return False

def test_report_queries():
    """리포트 관련 쿼리 테스트"""
    print("\n" + "=" * 50)
    print("3. 리포트 쿼리 테스트")
    print("=" * 50)
    
    report_db = ReportDB()
    
    try:
        # 요약 데이터
        print("\n[요약 데이터 조회]")
        summary = report_db.get_summary_data('user_001')
        print(f"✅ 요약 데이터 조회 성공")
        print(f"   - 총 티켓 수: {summary['total_tickets']}건")
        print(f"   - 분류 정확도: {summary['classification_accuracy']:.1%}")
        print(f"   - 평균 해결 시간: {summary['avg_resolution_time']:.1f}시간" if summary['avg_resolution_time'] else "   - 평균 해결 시간: N/A")
        print(f"   - 채널별 분포: {summary['channels']}")
        
        # 채널별 추이
        print("\n[채널별 추이 데이터 조회]")
        channel_trends = report_db.get_channel_trend_data('user_001')
        print(f"✅ 채널별 추이 데이터 조회 성공: {len(channel_trends)}개 채널")
        for channel, data in channel_trends.items():
            print(f"   - {channel}: {len(data['dates'])}일간 데이터, {len(data['categories'])}개 카테고리")
        
        # AI 분석 데이터
        print("\n[AI 분석 데이터 조회]")
        ai_data = report_db.get_ai_analysis_data('user_001')
        print(f"✅ AI 분석 데이터 조회 성공")
        print(f"   - 카테고리 분포: {len(ai_data['category_distribution'])}개")
        print(f"   - 채널 분포: {len(ai_data['channel_distribution'])}개")
        print(f"   - 상위 키워드: {len(ai_data['top_keywords'])}개")
        print(f"   - 감정 분포: {len(ai_data['sentiment_distribution'])}개")
        
        return True
    except Exception as e:
        print(f"❌ 리포트 쿼리 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_report_service():
    """리포트 서비스 통합 테스트"""
    print("\n" + "=" * 50)
    print("4. 리포트 서비스 통합 테스트")
    print("=" * 50)
    
    try:
        report_service = ReportService()
        
        print("\n[리포트 생성 테스트]")
        print("Note: AI 인사이트 생성은 실제 OpenAI API 호출이 필요합니다.")
        print("      .env 파일에 OPENAI_API_KEY가 없으면 더미 데이터를 반환합니다.")
        
        # 리포트 생성 (AI 부분은 API 키가 없으면 스킵)
        report_data = report_service.generate_report('user_001')
        
        print(f"✅ 리포트 생성 성공")
        print(f"   - 채널 추이: {len(report_data['channel_trends'])}개 채널")
        print(f"   - 요약 데이터: 총 {report_data['summary']['total_tickets']}건")
        print(f"   - 생성 시각: {report_data['generated_at']}")
        
        return True
    except Exception as e:
        print(f"❌ 리포트 서비스 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 실행"""
    print("\n" + "🔧 " * 20)
    print("ClaraCS 데이터베이스 연결 테스트")
    print("🔧 " * 20 + "\n")
    
    results = []
    
    # 1. DB 연결 테스트
    results.append(("DB 연결", test_db_connection()))
    
    if not results[0][1]:
        print("\n⚠️  DB 연결에 실패하여 다른 테스트를 건너뜁니다.")
        print("DB_SETUP_GUIDE.md를 참고하여 DB 설정을 확인하세요.")
        return
    
    # 2. 기본 쿼리 테스트
    results.append(("기본 쿼리", test_basic_queries()))
    
    # 3. 리포트 쿼리 테스트
    results.append(("리포트 쿼리", test_report_queries()))
    
    # 4. 리포트 서비스 테스트
    results.append(("리포트 서비스", test_report_service()))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    print(f"\n총 {total_count}개 테스트 중 {success_count}개 성공")
    
    if success_count == total_count:
        print("\n🎉 모든 테스트 통과! 로컬 DB 연동이 완료되었습니다.")
        print("\n다음 단계:")
        print("1. python app.py 로 Flask 서버 실행")
        print("2. http://localhost:5000/report 접속")
        print("3. '리포트 생성' 버튼 클릭하여 실제 동작 확인")
    else:
        print("\n⚠️  일부 테스트가 실패했습니다.")
        print("DB_SETUP_GUIDE.md를 참고하여 문제를 해결하세요.")

if __name__ == "__main__":
    main()

