from utils.database import db_manager
from utils.logger import get_logger
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = get_logger(__name__)

class ReportDB:
    """리포트 관련 데이터베이스 작업 클래스 (실제 스키마 기반)"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    # ========================================
    # 티켓 관련 조회
    # ========================================
    
    def get_tickets_by_file(self, file_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """파일 ID로 티켓 데이터 조회"""
        logger.info(f"파일 {file_id}의 티켓 데이터 조회 시작")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT 
                    t.ticket_id, t.file_id, t.user_id, t.received_at, t.channel,
                    t.customer_id, t.product_code, t.inquiry_type, t.title, t.body,
                    t.status, t.created_at, t.updated_at
                FROM tb_ticket t
                WHERE t.file_id = %s
            """
            params = [file_id]
            
            if start_date:
                query += " AND t.received_at >= %s"
                params.append(start_date)
            
            if end_date:
                query += " AND t.received_at <= %s"
                params.append(end_date)
            
            query += " ORDER BY t.received_at DESC"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            df = pd.DataFrame(results)
            logger.info(f"티켓 데이터 {len(df)}건 조회 완료")
            return df
            
        except Exception as e:
            logger.error(f"티켓 데이터 조회 실패: {e}")
            return pd.DataFrame()
        finally:
            cursor.close()
    
    def get_tickets_by_user(self, user_id: int) -> pd.DataFrame:
        """사용자 ID로 모든 티켓 조회"""
        logger.info(f"사용자 {user_id}의 티켓 데이터 조회")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT 
                    t.ticket_id, t.file_id, t.user_id, t.received_at, t.channel,
                    t.customer_id, t.product_code, t.inquiry_type, t.title, t.body,
                    t.status
                FROM tb_ticket t
                WHERE t.user_id = %s
                ORDER BY t.received_at DESC
            """
            
            cursor.execute(query, [user_id])
            results = cursor.fetchall()
            
            df = pd.DataFrame(results)
            logger.info(f"티켓 데이터 {len(df)}건 조회 완료")
            return df
            
        except Exception as e:
            logger.error(f"티켓 데이터 조회 실패: {e}")
            return pd.DataFrame()
        finally:
            cursor.close()
    
    # ========================================
    # 분류 결과 조회
    # ========================================
    
    def get_latest_classification_result(self, file_id: int) -> Optional[int]:
        """파일의 최신 분류 결과 ID 조회"""
        logger.info(f"파일 {file_id}의 최신 분류 결과 조회")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT cr.class_result_id
                FROM tb_classification_result cr
                JOIN tb_ticket t ON cr.ticket_id = t.ticket_id
                WHERE t.file_id = %s
                ORDER BY cr.classified_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, [file_id])
            result = cursor.fetchone()
            
            if result:
                logger.info(f"분류 결과 ID {result['class_result_id']} 조회 완료")
                return result['class_result_id']
            else:
                logger.warning(f"파일 {file_id}의 분류 결과가 없습니다")
                return None
                
        except Exception as e:
            logger.error(f"분류 결과 조회 실패: {e}")
            return None
        finally:
            cursor.close()
    
    def get_category_results(self, class_result_id: int) -> List[Dict]:
        """카테고리별 분류 결과 조회"""
        logger.info(f"분류 결과 {class_result_id}의 카테고리별 데이터 조회")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT 
                    ccr.cat_result_id,
                    ccr.category_id,
                    c.category_name,
                    ccr.count,
                    ccr.ratio,
                    ccr.example_keywords
                FROM tb_classification_category_result ccr
                JOIN tb_category c ON ccr.category_id = c.category_id
                WHERE ccr.class_result_id = %s
                ORDER BY ccr.count DESC
            """
            
            cursor.execute(query, [class_result_id])
            results = cursor.fetchall()
            
            # JSON 필드 파싱
            for row in results:
                if row['example_keywords'] and isinstance(row['example_keywords'], str):
                    row['example_keywords'] = json.loads(row['example_keywords'])
            
            logger.info(f"카테고리별 결과 {len(results)}건 조회 완료")
            return results
            
        except Exception as e:
            logger.error(f"카테고리별 결과 조회 실패: {e}")
            return []
        finally:
            cursor.close()
    
    def get_channel_results(self, class_result_id: int) -> List[Dict]:
        """채널별 분류 결과 조회"""
        logger.info(f"분류 결과 {class_result_id}의 채널별 데이터 조회")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT 
                    chr.ch_result_id,
                    chr.channel,
                    chr.category_id,
                    c.category_name,
                    chr.count,
                    chr.ratio
                FROM tb_classification_channel_result chr
                JOIN tb_category c ON chr.category_id = c.category_id
                WHERE chr.class_result_id = %s
                ORDER BY chr.channel, chr.count DESC
            """
            
            cursor.execute(query, [class_result_id])
            results = cursor.fetchall()
            
            logger.info(f"채널별 결과 {len(results)}건 조회 완료")
            return results
            
        except Exception as e:
            logger.error(f"채널별 결과 조회 실패: {e}")
            return []
        finally:
            cursor.close()
    
    # ========================================
    # 리포트 데이터 조회 (프론트엔드용)
    # ========================================
    
    def get_channel_trend_data(self, file_id: int) -> dict:
        """채널별 추이 데이터 조회 (최근 30일)"""
        logger.info(f"파일 {file_id}의 채널별 추이 데이터 조회")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # 최신 분류 결과 ID 조회
            class_result_id = self.get_latest_classification_result(file_id)
            if not class_result_id:
                return {}
            
            # 채널별, 카테고리별, 날짜별 집계
            query = """
                SELECT 
                    t.channel,
                    c.category_name,
                    DATE(t.received_at) as date,
                    COUNT(*) as count
                FROM tb_ticket t
                LEFT JOIN tb_classification_result cr ON t.ticket_id = cr.ticket_id
                LEFT JOIN tb_classification_category_result ccr ON cr.class_result_id = ccr.class_result_id
                LEFT JOIN tb_category c ON ccr.category_id = c.category_id
                WHERE t.file_id = %s
                AND t.received_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY t.channel, c.category_name, DATE(t.received_at)
                ORDER BY DATE(t.received_at), t.channel, c.category_name
            """
            
            cursor.execute(query, [file_id])
            results = cursor.fetchall()
            
            # 데이터 구조 변환
            channel_trends = {}
            for row in results:
                channel = row['channel'] or '미분류'
                category = row['category_name'] or '미분류'
                date = row['date'].strftime('%m-%d') if row['date'] else ''
                count = row['count']
                
                if channel not in channel_trends:
                    channel_trends[channel] = {
                        'categories': [],
                        'dates': [],
                        'data': []
                    }
                
                if category not in channel_trends[channel]['categories']:
                    channel_trends[channel]['categories'].append(category)
                
                if date not in channel_trends[channel]['dates']:
                    channel_trends[channel]['dates'].append(date)
                
                date_idx = channel_trends[channel]['dates'].index(date)
                cat_idx = channel_trends[channel]['categories'].index(category)
                
                # data 배열 초기화
                while len(channel_trends[channel]['data']) <= date_idx:
                    channel_trends[channel]['data'].append([0] * len(channel_trends[channel]['categories']))
                
                # 카테고리 개수 증가 시 배열 확장
                for data_row in channel_trends[channel]['data']:
                    while len(data_row) < len(channel_trends[channel]['categories']):
                        data_row.append(0)
                
                channel_trends[channel]['data'][date_idx][cat_idx] = count
            
            logger.info(f"채널별 추이 데이터 조회 완료: {len(channel_trends)}개 채널")
            return channel_trends
            
        except Exception as e:
            logger.error(f"채널별 추이 데이터 조회 실패: {e}")
            return {}
        finally:
            cursor.close()
    
    def get_summary_data(self, file_id: int) -> dict:
        """데이터 요약 정보 조회"""
        logger.info(f"파일 {file_id}의 요약 데이터 조회")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # 1. 총 티켓 수
            cursor.execute("""
                SELECT COUNT(*) as total_tickets
                FROM tb_ticket
                WHERE file_id = %s
            """, [file_id])
            total_tickets = cursor.fetchone()['total_tickets']
            
            # 2. 최신 분류 결과의 평균 신뢰도
            class_result_id = self.get_latest_classification_result(file_id)
            classification_accuracy = 0.0
            
            if class_result_id:
                cursor.execute("""
                    SELECT AVG(metric_value) as avg_reliability
                    FROM tb_classification_reliability_result
                    WHERE class_result_id = %s
                    AND metric_name IN ('accuracy', 'f1_score')
                """, [class_result_id])
                result = cursor.fetchone()
                classification_accuracy = result['avg_reliability'] if result['avg_reliability'] else 0.0
            
            # 3. 채널별 티켓 수
            cursor.execute("""
                SELECT channel, COUNT(*) as count
                FROM tb_ticket
                WHERE file_id = %s
                GROUP BY channel
                ORDER BY count DESC
            """, [file_id])
            channels = {}
            for row in cursor.fetchall():
                channels[row['channel'] or '미분류'] = row['count']
            
            # 4. 상태별 티켓 수
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM tb_ticket
                WHERE file_id = %s
                GROUP BY status
            """, [file_id])
            status_distribution = {}
            for row in cursor.fetchall():
                status_distribution[row['status']] = row['count']
            
            summary = {
                'total_tickets': total_tickets,
                'classification_accuracy': float(classification_accuracy),
                'avg_resolution_time': None,  # 해결 시간 필드가 없음
                'channels': channels,
                'status_distribution': status_distribution
            }
            
            logger.info(f"요약 데이터 조회 완료")
            return summary
            
        except Exception as e:
            logger.error(f"요약 데이터 조회 실패: {e}")
            return {
                'total_tickets': 0,
                'classification_accuracy': 0.0,
                'avg_resolution_time': None,
                'channels': {},
                'status_distribution': {}
            }
        finally:
            cursor.close()
    
    def get_ai_analysis_data(self, file_id: int) -> dict:
        """AI 분석용 데이터 조회"""
        logger.info(f"파일 {file_id}의 AI 분석 데이터 조회")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            class_result_id = self.get_latest_classification_result(file_id)
            
            # 1. 카테고리별 티켓 분포
            category_distribution = []
            if class_result_id:
                category_distribution = self.get_category_results(class_result_id)
            
            # 2. 채널별 티켓 분포
            cursor.execute("""
                SELECT channel, COUNT(*) as count
                FROM tb_ticket
                WHERE file_id = %s
                GROUP BY channel
                ORDER BY count DESC
            """, [file_id])
            channel_distribution = cursor.fetchall()
            
            # 3. 문의 유형별 분포
            cursor.execute("""
                SELECT inquiry_type, COUNT(*) as count
                FROM tb_ticket
                WHERE file_id = %s AND inquiry_type IS NOT NULL
                GROUP BY inquiry_type
                ORDER BY count DESC
            """, [file_id])
            inquiry_type_distribution = cursor.fetchall()
            
            # 4. 최근 7일간 추세
            cursor.execute("""
                SELECT 
                    DATE(received_at) as date,
                    COUNT(*) as count
                FROM tb_ticket
                WHERE file_id = %s
                AND received_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(received_at)
                ORDER BY date
            """, [file_id])
            recent_trend = cursor.fetchall()
            
            # 5. 키워드 추출 (카테고리별 예시 키워드에서)
            top_keywords = []
            if class_result_id:
                for cat_result in category_distribution:
                    if cat_result.get('example_keywords'):
                        keywords = cat_result['example_keywords']
                        if isinstance(keywords, list):
                            top_keywords.extend(keywords)
            
            ai_analysis_data = {
                'category_distribution': category_distribution,
                'channel_distribution': channel_distribution,
                'inquiry_type_distribution': inquiry_type_distribution,
                'top_keywords': list(set(top_keywords))[:20],  # 중복 제거 후 상위 20개
                'recent_trend': recent_trend,
                'class_result_id': class_result_id
            }
            
            logger.info(f"AI 분석 데이터 조회 완료")
            return ai_analysis_data
            
        except Exception as e:
            logger.error(f"AI 분석 데이터 조회 실패: {e}")
            return {
                'category_distribution': [],
                'channel_distribution': [],
                'inquiry_type_distribution': [],
                'top_keywords': [],
                'recent_trend': [],
                'class_result_id': None
            }
        finally:
            cursor.close()
    
    # ========================================
    # 리포트 저장 (스냅샷)
    # ========================================
    
    def create_report(self, file_id: int, user_id: int, report_type: str, title: str) -> Optional[int]:
        """리포트 생성 (tb_analysis_report)"""
        logger.info(f"리포트 생성: 파일 {file_id}, 유저 {user_id}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_analysis_report 
                (file_id, created_by, report_type, title, status, created_at)
                VALUES (%s, %s, %s, %s, 'processing', NOW())
            """
            
            cursor.execute(query, (file_id, user_id, report_type, title))
            connection.commit()
            
            report_id = cursor.lastrowid
            logger.info(f"리포트 생성 완료: report_id={report_id}")
            return report_id
            
        except Exception as e:
            logger.error(f"리포트 생성 실패: {e}")
            connection.rollback()
            return None
        finally:
            cursor.close()
    
    def save_channel_snapshot(self, report_id: int, channel_data: List[Dict]) -> bool:
        """채널 스냅샷 저장"""
        logger.info(f"채널 스냅샷 저장: report_id={report_id}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_analysis_channel_snapshot
                (report_id, channel, time_period, category_id, count)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            for data in channel_data:
                cursor.execute(query, (
                    report_id,
                    data['channel'],
                    data.get('time_period'),
                    data.get('category_id'),
                    data['count']
                ))
            
            connection.commit()
            logger.info(f"채널 스냅샷 {len(channel_data)}건 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"채널 스냅샷 저장 실패: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
    
    def save_summary_snapshot(self, report_id: int, summary_data: Dict) -> bool:
        """요약 스냅샷 저장"""
        logger.info(f"요약 스냅샷 저장: report_id={report_id}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_analysis_summary_snapshot
                (report_id, total_tickets, resolved_count, category_ratios, repeat_rate, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            
            cursor.execute(query, (
                report_id,
                summary_data.get('total_tickets', 0),
                json.dumps(summary_data.get('resolved_count', {})),
                json.dumps(summary_data.get('category_ratios', {})),
                summary_data.get('repeat_rate', 0.0)
            ))
            
            connection.commit()
            logger.info(f"요약 스냅샷 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"요약 스냅샷 저장 실패: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
    
    def save_insight_snapshot(self, report_id: int, insights: Dict) -> bool:
        """인사이트 스냅샷 저장"""
        logger.info(f"인사이트 스냅샷 저장: report_id={report_id}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_analysis_insight_snapshot
                (report_id, insight_payload, created_at)
                VALUES (%s, %s, NOW())
            """
            
            cursor.execute(query, (report_id, json.dumps(insights, ensure_ascii=False)))
            connection.commit()
            
            logger.info(f"인사이트 스냅샷 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"인사이트 스냅샷 저장 실패: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
    
    def save_solution_snapshot(self, report_id: int, solutions: Dict) -> bool:
        """솔루션 스냅샷 저장"""
        logger.info(f"솔루션 스냅샷 저장: report_id={report_id}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                INSERT INTO tb_analysis_solution_snapshot
                (report_id, solution_payload, created_at)
                VALUES (%s, %s, NOW())
            """
            
            cursor.execute(query, (report_id, json.dumps(solutions, ensure_ascii=False)))
            connection.commit()
            
            logger.info(f"솔루션 스냅샷 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"솔루션 스냅샷 저장 실패: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
    
    def complete_report(self, report_id: int, file_path: str = None) -> bool:
        """리포트 완료 처리"""
        logger.info(f"리포트 완료 처리: report_id={report_id}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            query = """
                UPDATE tb_analysis_report
                SET status = 'completed', completed_at = NOW()
            """
            
            if file_path:
                query += ", file_path = %s"
                cursor.execute(query + " WHERE report_id = %s", (file_path, report_id))
            else:
                cursor.execute(query + " WHERE report_id = %s", (report_id,))
            
            connection.commit()
            logger.info(f"리포트 완료 처리 성공")
            return True
            
        except Exception as e:
            logger.error(f"리포트 완료 처리 실패: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
    
    def _get_current_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
