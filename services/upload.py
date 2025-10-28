from services.db.upload_db import UploadDB
from services.mapping import MappingService
from utils.logger import get_logger
from datetime import datetime
import pandas as pd
import os
import re
from werkzeug.utils import secure_filename
from io import BytesIO

logger = get_logger(__name__)

class UploadService:
    """파일 업로드 서비스 클래스"""
    
    def __init__(self):
        self.upload_db = UploadDB()
        self.mapping_service = MappingService()
        self.allowed_extensions = {'csv', 'xlsx', 'xls'}
        self.upload_folder = 'uploads'
        
        # 업로드 폴더가 없으면 생성
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
    
    def upload_batch(self, files, user_id=1, batch_name=None):
        """
        여러 파일을 배치로 업로드 및 처리
        
        Args:
            files: 파일 리스트
            user_id: 사용자 ID
            batch_name: 배치 이름 (선택)
            
        Returns:
            dict: 배치 업로드 결과
        """
        try:
            if not files or len(files) == 0:
                raise ValueError('업로드할 파일이 없습니다.')
            
            logger.info(f"배치 업로드 시작: {len(files)}개 파일")
            
            # 1. 배치 생성
            batch_id = self.upload_db.create_batch(user_id, batch_name)
            logger.info(f"파일 배치 생성: batch_id={batch_id}")
            
            # 2. 각 파일 업로드 처리
            uploaded_files = []
            total_row_count = 0
            errors = []
            
            for file in files:
                try:
                    # 파일 업로드 (batch_id 포함)
                    result = self._upload_single_file(file, user_id, batch_id)
                    uploaded_files.append(result)
                    total_row_count += result['row_count']
                    
                except Exception as e:
                    logger.error(f"파일 업로드 실패 ({file.filename}): {e}")
                    errors.append({
                        'filename': file.filename,
                        'error': str(e)
                    })
            
            # 3. 배치 정보 업데이트
            self.upload_db.update_batch_file_count(
                batch_id, 
                len(uploaded_files), 
                total_row_count
            )
            
            # 4. 배치 완료 처리
            if len(uploaded_files) > 0:
                self.upload_db.complete_batch(batch_id)
            
            logger.info(f"배치 업로드 완료: batch_id={batch_id}, {len(uploaded_files)}/{len(files)} 성공")
            
            return {
                'batch_id': batch_id,
                'batch_name': batch_name,
                'total_files': len(files),
                'successful_files': len(uploaded_files),
                'failed_files': len(errors),
                'total_rows': total_row_count,
                'uploaded_files': uploaded_files,
                'errors': errors,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"배치 업로드 실패: {e}")
            raise
    
    def _upload_single_file(self, file, user_id, batch_id=None):
        """
        단일 파일 업로드 (내부용 - 배치 지원)
        
        Args:
            file: 업로드 파일
            user_id: 사용자 ID
            batch_id: 배치 ID (선택)
            
        Returns:
            dict: 업로드 결과
        """
        # 1. 파일 검증
        if not file or file.filename == '':
            raise ValueError('파일이 선택되지 않았습니다.')
        
        if not self.allowed_file(file.filename):
            raise ValueError('허용되지 않은 파일 형식입니다. (csv, xlsx, xls만 허용)')
        
        # 2. 파일 저장
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')  # 마이크로초 추가
        storage_filename = f"{timestamp}_{original_filename}"
        storage_path = os.path.join(self.upload_folder, storage_filename)
        
        file.save(storage_path)
        logger.info(f"파일 저장 완료: {storage_path}")
        
        # 3. 파일 데이터 읽기
        df = self._read_file(storage_path, file_extension)
        row_count = len(df)
        
        # 4. 파일 정보 DB 저장 (batch_id 포함)
        extension_code_id = self.upload_db.get_extension_code_id(file_extension)
        file_data = {
            'user_id': user_id,
            'original_filename': original_filename,
            'storage_path': storage_path,
            'extension_code_id': extension_code_id,
            'row_count': row_count,
            'status': 'uploaded',
            'batch_id': batch_id  # 배치 ID 추가
        }
        
        file_id = self.upload_db.insert_file(file_data)
        logger.info(f"파일 정보 DB 저장 완료: file_id={file_id}, batch_id={batch_id}")
        
        # 5. 컬럼 매핑 조회
        mapping_dict = self.mapping_service.get_active_mappings_dict()
        
        # 6. 티켓 데이터 파싱 및 저장
        tickets_inserted = self._parse_and_save_tickets(df, file_id, user_id, mapping_dict)
        
        # 7. 파일 상태 업데이트
        self.upload_db.update_file_status(file_id, 'processed')
        
        return {
            'file_id': file_id,
            'original_filename': original_filename,
            'row_count': row_count,
            'tickets_inserted': tickets_inserted,
            'created_at': datetime.now().isoformat()
        }
    
    def allowed_file(self, filename):
        """허용된 파일 확장자 체크"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def upload(self, file, user_id=1):
        """
        단일 파일 업로드 및 처리 (기존 API 호환성 유지)
        배치 없이 개별 파일로 업로드
        """
        try:
            return self._upload_single_file(file, user_id, batch_id=None)
        except Exception as e:
            logger.error(f"파일 업로드 실패: {e}")
            raise
    
    def _read_file(self, file_path, file_extension):
        """파일 읽기 (CSV 또는 Excel)"""
        try:
            if file_extension == 'csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f'지원되지 않는 파일 형식: {file_extension}')
            
            logger.info(f"파일 읽기 완료: {len(df)}행, {len(df.columns)}컬럼")
            return df
            
        except Exception as e:
            logger.error(f"파일 읽기 실패: {e}")
            raise
    
    def _parse_and_save_tickets(self, df, file_id, user_id, mapping_dict):
        """
        데이터프레임을 파싱하여 티켓 데이터로 변환 및 저장
        mapping_dict: {원본컬럼명: 매핑코드명}
        """
        try:
            tickets = []
            
            # 역매핑 딕셔너리 생성 (매핑코드명: 원본컬럼명)
            reverse_mapping = {v: k for k, v in mapping_dict.items()}
            
            # 대소문자 무시 매핑 생성
            file_columns_lower = {col.lower(): col for col in df.columns}
            case_insensitive_reverse = {}
            for code_name, mapped_column in reverse_mapping.items():
                mapped_lower = mapped_column.lower()
                if mapped_lower in file_columns_lower:
                    # 실제 파일의 컬럼명 사용
                    case_insensitive_reverse[code_name] = file_columns_lower[mapped_lower]
            
            for index, row in df.iterrows():
                ticket = {
                    'file_id': file_id,
                    'user_id': user_id,
                    'received_at': self._get_mapped_value(row, case_insensitive_reverse, '접수일'),
                    'channel': self._get_mapped_value(row, case_insensitive_reverse, '채널'),
                    'customer_id': self._get_mapped_value(row, case_insensitive_reverse, '고객ID'),
                    'product_code': self._get_mapped_value(row, case_insensitive_reverse, '상품코드'),
                    'inquiry_type': self._get_mapped_value(row, case_insensitive_reverse, '문의 유형'),
                    'title': self._get_mapped_value(row, case_insensitive_reverse, '제목'),  # 제목 매핑 추가
                    'body': self._get_mapped_value(row, case_insensitive_reverse, '본문'),
                    'assignee': self._get_mapped_value(row, case_insensitive_reverse, '담당자'),  # 담당자 추가
                    'status': self._get_mapped_value(row, case_insensitive_reverse, '처리 상태', default='new'),
                    'raw_data': row.to_json()
                }
                
                tickets.append(ticket)
            
            # 티켓 DB 저장
            inserted_count = self.upload_db.insert_tickets(tickets)
            logger.info(f"티켓 데이터 {inserted_count}건 저장 완료")
            
            return inserted_count
            
        except Exception as e:
            logger.error(f"티켓 파싱 및 저장 실패: {e}")
            raise
    
    def _get_mapped_value(self, row, reverse_mapping, code_name, default=None):
        """
        매핑된 컬럼에서 값 가져오기 (대소문자 무시)
        reverse_mapping: {매핑코드명: 실제파일컬럼명}
        """
        actual_column = reverse_mapping.get(code_name)
        if actual_column and actual_column in row.index:
            value = row[actual_column]
            # NaN 체크
            if pd.isna(value):
                return default
            return str(value) if value is not None else default
        return default
    
    def validate_file(self, file, mapping_dict):
        """
        파일 유효성 검사
        1. 매핑된 컬럼이 실제 파일에 존재하는지 확인 (대소문자 무시)
        2. 필수 컬럼 누락 체크 (본문에 공란이 있는지)
        3. 날짜 형식 체크 (접수일이 올바른 형식인지)
        """
        try:
            # 파일 읽기 (임시로 메모리에서 처리)
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            
            # 파일을 BytesIO로 읽어서 원본 파일을 보존
            file_content = file.read()
            file.seek(0)  # 파일 포인터를 다시 처음으로
            
            # DataFrame으로 변환
            if file_extension == 'csv':
                df = pd.read_csv(BytesIO(file_content), encoding='utf-8')
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(BytesIO(file_content))
            else:
                raise ValueError(f'지원되지 않는 파일 형식: {file_extension}')
            
            # 파일의 실제 컬럼명 (대소문자 구분 없이 매핑하기 위해 소문자로 변환)
            file_columns_lower = {col.lower(): col for col in df.columns}
            
            # 역매핑 딕셔너리 생성 (매핑코드명: 원본컬럼명)
            reverse_mapping = {v: k for k, v in mapping_dict.items()}
            
            # 대소문자 무시 매핑 딕셔너리 생성
            # {매핑코드명: 실제파일컬럼명}
            case_insensitive_mapping = {}
            for code_name, mapped_column in reverse_mapping.items():
                mapped_lower = mapped_column.lower()
                if mapped_lower in file_columns_lower:
                    case_insensitive_mapping[code_name] = file_columns_lower[mapped_lower]
            
            errors = []
            
            # 0. 매핑된 컬럼이 실제 파일에 존재하는지 확인
            missing_columns = []
            for code_name, mapped_column in reverse_mapping.items():
                mapped_lower = mapped_column.lower()
                if mapped_lower not in file_columns_lower:
                    missing_columns.append({
                        'code_name': code_name,
                        'expected': mapped_column,
                        'available': list(df.columns)
                    })
            
            if missing_columns:
                for missing in missing_columns:
                    errors.append({
                        'type': 'column_not_found',
                        'column': missing['code_name'],
                        'expected_column': missing['expected'],
                        'message': f"매핑 오류: '{missing['code_name']}'에 매핑된 컬럼 '{missing['expected']}'을(를) 파일에서 찾을 수 없습니다."
                    })
            
            # 1. 필수 컬럼 누락 체크 (본문)
            if '본문' in case_insensitive_mapping:
                body_column = case_insensitive_mapping['본문']
                missing_count = df[body_column].isna().sum()
                if missing_count > 0:
                    errors.append({
                        'type': 'missing_values',
                        'column': '본문',
                        'count': int(missing_count),
                        'message': f'필수 컬럼 누락: 본문 {missing_count}건'
                    })
            
            # 2. 날짜 형식 체크 (접수일)
            if '접수일' in case_insensitive_mapping:
                date_column = case_insensitive_mapping['접수일']
                invalid_dates = self._check_date_format(df[date_column])
                if invalid_dates > 0:
                    errors.append({
                        'type': 'date_format',
                        'column': '접수일',
                        'count': int(invalid_dates),
                        'message': f'날짜 형식 불일치: 접수일 {invalid_dates}건 (YYYY-MM-DD 권장)'
                    })
            
            # 유효성 검사 결과 반환
            is_valid = len(errors) == 0
            
            return {
                'is_valid': is_valid,
                'errors': errors,
                'row_count': len(df),
                'column_count': len(df.columns),
                'file_columns': list(df.columns),  # 디버깅용
                'mapped_columns': list(reverse_mapping.values())  # 디버깅용
            }
            
        except Exception as e:
            logger.error(f"파일 유효성 검사 실패: {e}")
            raise
    
    def _check_date_format(self, date_series):
        """
        날짜 형식 체크
        YYYY-MM-DD 또는 YYYY-MM-DD HH:MM:SS 형식인지 확인
        """
        invalid_count = 0
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$',  # YYYY-MM-DD HH:MM:SS
            r'^\d{4}/\d{2}/\d{2}$',  # YYYY/MM/DD
            r'^\d{4}\.\d{2}\.\d{2}$'  # YYYY.MM.DD
        ]
        
        for value in date_series:
            if pd.isna(value):
                continue
            
            value_str = str(value).strip()
            is_valid = False
            
            for pattern in date_patterns:
                if re.match(pattern, value_str):
                    is_valid = True
                    break
            
            # pandas datetime 형식도 허용
            try:
                pd.to_datetime(value)
                is_valid = True
            except:
                pass
            
            if not is_valid:
                invalid_count += 1
        
        return invalid_count