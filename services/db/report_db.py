from utils.database import db_manager
from utils.logger import get_logger
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import decimal

logger = get_logger(__name__)

class ReportDB:
    """리포트 관련 데이터베이스 작업 클래스 (실제 스키마 기반)"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    # ========================================
    # 파일 관련 조회
    # ========================================
    
    def get_latest_file_id(self, user_id: int) -> Optional[int]:
        """사용자의 최신 업로드 파일 ID 조회"""
        logger.info(f"사용자 {user_id}의 최신 파일 조회")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            query = """
                SELECT file_id
                FROM tb_uploaded_file
                WHERE user_id = %s
                  AND status = 'processed'
                  AND (is_deleted IS NULL OR is_deleted = FALSE)
                ORDER BY created_at DESC
                LIMIT 1
            """
            
            cursor.execute(query, [user_id])
            result = cursor.fetchone()
            
            if result:
                file_id = result['file_id']
                logger.info(f"최신 파일 조회 완료: file_id={file_id}")
                return file_id
            else:
                logger.warning(f"사용자 {user_id}의 업로드 파일이 없습니다")
                return None
                
        except Exception as e:
            logger.error(f"최신 파일 조회 실패: {e}")
            return None
        finally:
            cursor.close()
            if connection and connection.is_connected():
                connection.close()
    
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
            if connection and connection.is_connected():
                connection.close()
    
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
            if connection and connection.is_connected():
                connection.close()
    
    # ========================================
    # 분류 결과 조회
    # ========================================
    
    def get_latest_classification_result(self, file_id: int) -> Optional[int]:
        """파일의 최신 분류 결과 ID 조회"""
        logger.info(f"파일 {file_id}의 최신 분류 결과 조회")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # tb_classification_result 테이블에 file_id가 직접 있음 (JOIN 불필요)
            query = """
                SELECT class_result_id
                FROM tb_classification_result
                WHERE file_id = %s
                ORDER BY classified_at DESC
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
            if connection and connection.is_connected():
                connection.close()
    
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
            if connection and connection.is_connected():
                connection.close()
    
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
            if connection and connection.is_connected():
                connection.close()
    
    # ========================================
    # 리포트 데이터 조회 (프론트엔드용)
    # ========================================
    
    def get_channel_trend_data(self, file_id: int, days: int = 365) -> dict:
        """채널별 추이 데이터 조회 (기본 365일, 전체 기간 포함)"""
        logger.info(f"파일 {file_id}의 채널별 추이 데이터 조회 (최근 {days}일)")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # 최신 분류 결과 ID 조회
            class_result_id = self.get_latest_classification_result(file_id)
            if not class_result_id:
                logger.warning(f"파일 {file_id}의 분류 결과가 없습니다")
                return {}
            
            # 채널별, 카테고리별, 날짜별 집계
            # tb_ticket.classified_category_id를 직접 사용
            query = """
                SELECT 
                    t.channel,
                    c.category_name,
                    DATE(t.received_at) as date,
                    COUNT(*) as count
                FROM tb_ticket t
                LEFT JOIN tb_category c ON t.classified_category_id = c.category_id
                WHERE t.file_id = %s
                  AND t.classified_category_id IS NOT NULL
                GROUP BY t.channel, c.category_name, DATE(t.received_at)
                ORDER BY DATE(t.received_at), t.channel, c.category_name
            """
            
            cursor.execute(query, [file_id])
            results = cursor.fetchall()
            
            if not results:
                logger.warning(f"파일 {file_id}의 채널별 추이 데이터가 없습니다. 분류 실행 여부를 확인하세요.")
                return {}
            
            logger.debug(f"채널별 추이 원본 데이터 {len(results)}건 조회")
            
            # 데이터 구조 변환
            channel_trends = {}
            for row in results:
                channel = row['channel'] or '미분류'
                category = row['category_name'] or '미분류'
                
                # 날짜 형식: YYYY-MM-DD (DB 저장용 전체 날짜)
                date_full = row['date'].strftime('%Y-%m-%d') if row['date'] else ''
                # 표시용 날짜: MM-DD (프론트엔드용)
                date_display = row['date'].strftime('%m-%d') if row['date'] else ''
                
                count = row['count']
                
                if channel not in channel_trends:
                    channel_trends[channel] = {
                        'categories': [],
                        'dates': [],  # 표시용 (MM-DD)
                        'dates_full': [],  # DB 저장용 (YYYY-MM-DD)
                        'data': []
                    }
                
                if category not in channel_trends[channel]['categories']:
                    channel_trends[channel]['categories'].append(category)
                
                if date_display not in channel_trends[channel]['dates']:
                    channel_trends[channel]['dates'].append(date_display)
                    channel_trends[channel]['dates_full'].append(date_full)
                
                date_idx = channel_trends[channel]['dates'].index(date_display)
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
            if connection and connection.is_connected():
                connection.close()
    
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
            if connection and connection.is_connected():
                connection.close()
    
    def get_cs_analysis_data(self, file_id: int) -> dict:
        """CS 분석용 데이터 조회 - GPT 프롬프트에 사용할 데이터"""
        logger.info(f"파일 {file_id}의 CS 분석 데이터 조회")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        try:
            class_result_id = self.get_latest_classification_result(file_id)
            
            if not class_result_id:
                logger.warning(f"파일 {file_id}의 분류 결과가 없습니다")
                return {
                    'total_tickets': 0,
                    'category_distribution': [],
                    'channel_distribution': [],
                    'status_distribution': {}
                }
            
            # 1. 총 티켓 수
            cursor.execute("""
                SELECT COUNT(*) as total_tickets
                FROM tb_ticket
                WHERE file_id = %s
            """, [file_id])
            total_tickets = cursor.fetchone()['total_tickets']
            
            # 2. 카테고리별 분포 (분류 결과 기반)
            category_distribution = []
            category_results = self.get_category_results(class_result_id)
            
            for cat_result in category_results:
                category_distribution.append({
                    'category_id': cat_result['category_id'],  # ✅ category_id 추가
                    'category_name': cat_result['category_name'],
                    'count': cat_result['count'],
                    'ratio': cat_result['ratio'],
                    'percentage': round(cat_result['ratio'] * 100, 1),  # % 변환
                    'keywords': cat_result.get('example_keywords', [])[:5]  # 상위 5개 키워드
                })
            
            # 3. 채널별 분포
            cursor.execute("""
                SELECT channel, COUNT(*) as count
                FROM tb_ticket
                WHERE file_id = %s
                GROUP BY channel
                ORDER BY count DESC
            """, [file_id])
            channel_rows = cursor.fetchall()
            
            channel_distribution = []
            for row in channel_rows:
                channel_distribution.append({
                    'channel': row['channel'] or '미분류',
                    'count': row['count'],
                    'percentage': round((row['count'] / total_tickets * 100), 1) if total_tickets > 0 else 0
                })
            
            # 4. 상태별 분포 (해결률 계산용)
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM tb_ticket
                WHERE file_id = %s
                GROUP BY status
            """, [file_id])
            status_rows = cursor.fetchall()
            
            status_distribution = {}
            for row in status_rows:
                status_distribution[row['status']] = {
                    'count': row['count'],
                    'percentage': round((row['count'] / total_tickets * 100), 1) if total_tickets > 0 else 0
                }
            
            # 5. 채널별 해결률 계산 (status='closed' 기준)
            cursor.execute("""
                SELECT 
                    channel,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as resolved
                FROM tb_ticket
                WHERE file_id = %s
                GROUP BY channel
            """, [file_id])
            channel_resolution = cursor.fetchall()
            
            channel_resolution_rates = []
            for row in channel_resolution:
                resolution_rate = round((row['resolved'] / row['total'] * 100), 1) if row['total'] > 0 else 0
                channel_resolution_rates.append({
                    'channel': row['channel'] or '미분류',
                    'total': row['total'],
                    'resolved': row['resolved'],
                    'resolution_rate': resolution_rate
                })
            
            cs_analysis_data = {
                'total_tickets': total_tickets,
                'category_distribution': category_distribution,
                'channel_distribution': channel_distribution,
                'status_distribution': status_distribution,
                'channel_resolution_rates': channel_resolution_rates,
                'class_result_id': class_result_id
            }
            
            logger.info(f"CS 분석 데이터 조회 완료: 총 {total_tickets}건")
            return cs_analysis_data
            
        except Exception as e:
            logger.error(f"CS 분석 데이터 조회 실패: {e}")
            return {
                'total_tickets': 0,
                'category_distribution': [],
                'channel_distribution': [],
                'status_distribution': {},
                'channel_resolution_rates': [],
                'class_result_id': None
            }
        finally:
            cursor.close()
            if connection and connection.is_connected():
                connection.close()
    
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
            if connection and connection.is_connected():
                connection.close()
    
    def save_channel_snapshot(self, report_id: int, channel_trends: Dict) -> bool:
        """채널 스냅샷 저장 - 채널별 추이 데이터를 평면화하여 저장"""
        logger.info(f"채널 스냅샷 저장: report_id={report_id}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            # 카테고리명 -> category_id 매핑 조회
            cursor.execute("SELECT category_id, category_name FROM tb_category")
            category_map = {row[1]: row[0] for row in cursor.fetchall()}
            
            query = """
                INSERT INTO tb_analysis_channel_snapshot
                (report_id, channel, time_period, category_id, count)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            snapshot_count = 0
            current_year = datetime.now().year
            
            # channel_trends 구조: {channel: {categories: [...], dates: [...], dates_full: [...], data: [[...]]}}
            for channel, trend_data in channel_trends.items():
                categories = trend_data.get('categories', [])
                dates = trend_data.get('dates', [])  # 표시용 (MM-DD)
                dates_full = trend_data.get('dates_full', [])  # DB 저장용 (YYYY-MM-DD)
                data_matrix = trend_data.get('data', [])
                
                # 날짜별, 카테고리별 데이터 저장
                for date_idx, date_display in enumerate(dates):
                    if date_idx < len(data_matrix):
                        # DB 저장용 전체 날짜 가져오기
                        full_date = dates_full[date_idx] if date_idx < len(dates_full) else None
                        
                        if not full_date:
                            # 혹시 dates_full이 없으면 현재 연도로 변환
                            if date_display and '-' in date_display and len(date_display.split('-')) == 2:
                                month, day = date_display.split('-')
                                full_date = f"{current_year}-{month}-{day}"
                            else:
                                logger.warning(f"날짜 형식 오류: {date_display}, 건너뜀")
                                continue
                        
                        for cat_idx, category in enumerate(categories):
                            count = data_matrix[date_idx][cat_idx] if cat_idx < len(data_matrix[date_idx]) else 0
                            
                            # 카테고리 ID 조회
                            category_id = category_map.get(category)
                            
                            if not category_id:
                                logger.warning(f"카테고리 '{category}' ID를 찾을 수 없습니다. 건너뜀")
                                continue
                            
                            cursor.execute(query, (
                                report_id,
                                channel,
                                full_date,  # YYYY-MM-DD 형식
                                category_id,
                                int(count) if count else 0
                            ))
                            snapshot_count += 1
            
            connection.commit()
            logger.info(f"채널 스냅샷 {snapshot_count}건 저장 완료")
            return True
            
        except Exception as e:
            logger.error(f"채널 스냅샷 저장 실패: {e}")
            logger.error(f"상세 오류: {str(e)}", exc_info=True)
            connection.rollback()
            return False
        finally:
            cursor.close()
            if connection and connection.is_connected():
                connection.close()
    
    def save_summary_snapshot(self, report_id: int, summary_data: Dict) -> bool:
        """요약 스냅샷 저장"""
        logger.info(f"요약 스냅샷 저장: report_id={report_id}")
        
        connection = self.db_manager.get_connection()
        cursor = connection.cursor()
        
        try:
            # Decimal을 float로 변환하는 헬퍼 함수
            def convert_decimals(obj):
                """Decimal 타입을 float로 변환"""
                if isinstance(obj, dict):
                    return {k: convert_decimals(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_decimals(item) for item in obj]
                elif isinstance(obj, decimal.Decimal):
                    return float(obj)
                return obj
            
            query = """
                INSERT INTO tb_analysis_summary_snapshot
                (report_id, total_tickets, resolved_count, category_ratios, repeat_rate, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """
            
            # Decimal 변환 적용
            resolved_count = convert_decimals(summary_data.get('resolved_count', {}))
            category_ratios = convert_decimals(summary_data.get('category_ratios', {}))
            
            cursor.execute(query, (
                report_id,
                int(summary_data.get('total_tickets', 0)),
                json.dumps(resolved_count, ensure_ascii=False),
                json.dumps(category_ratios, ensure_ascii=False),
                float(summary_data.get('repeat_rate', 0.0))
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
            if connection and connection.is_connected():
                connection.close()
    
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
            if connection and connection.is_connected():
                connection.close()
    
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
            if connection and connection.is_connected():
                connection.close()
    
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
            if connection and connection.is_connected():
                connection.close()
    
    def _get_current_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
