from services.db.mapping_db import MappingDB
from utils.logger import get_logger

logger = get_logger(__name__)

class MappingService:
    """컬럼 매핑 서비스 클래스"""
    
    def __init__(self):
        self.mapping_db = MappingDB()
    
    def get_all_mapping_codes(self):
        """모든 매핑 코드 조회"""
        try:
            codes = self.mapping_db.get_all_mapping_codes()
            logger.info(f"매핑 코드 {len(codes)}개 조회 완료")
            return codes
        except Exception as e:
            logger.error(f"매핑 코드 조회 실패: {e}")
            raise
    
    def save_mappings(self, mappings, file_id=None):
        """컬럼 매핑 저장"""
        try:
            # 매핑 데이터 검증
            for mapping in mappings:
                if not mapping.get('original_column'):
                    raise ValueError("original_column은 필수입니다.")
                
                # mapping_code_id가 문자열(code_name)인 경우 ID로 변환
                if isinstance(mapping.get('mapping_code_id'), str):
                    code_name = mapping['mapping_code_id']
                    code_id = self.mapping_db.get_mapping_code_id_by_name(code_name)
                    if code_id:
                        mapping['mapping_code_id'] = code_id
                    else:
                        logger.warning(f"매핑 코드명 '{code_name}'을 찾을 수 없습니다.")
                        mapping['mapping_code_id'] = None
                
                # file_id 설정
                if file_id:
                    mapping['file_id'] = file_id
            
            # 저장
            result = self.mapping_db.insert_mappings(mappings)
            logger.info(f"컬럼 매핑 {len(mappings)}건 저장 완료")
            return result
            
        except Exception as e:
            logger.error(f"컬럼 매핑 저장 실패: {e}")
            raise
    
    def get_last_mappings(self, file_id=None):
        """마지막 컬럼 매핑 조회"""
        try:
            mappings = self.mapping_db.get_last_mappings(file_id)
            logger.info(f"마지막 컬럼 매핑 {len(mappings)}건 조회 완료")
            return mappings
        except Exception as e:
            logger.error(f"마지막 매핑 조회 실패: {e}")
            raise
    
    def get_mappings_by_file(self, file_id):
        """특정 파일의 컬럼 매핑 조회"""
        try:
            mappings = self.mapping_db.get_mappings_by_file(file_id)
            logger.info(f"파일 ID {file_id}의 컬럼 매핑 {len(mappings)}건 조회 완료")
            return mappings
        except Exception as e:
            logger.error(f"파일별 매핑 조회 실패: {e}")
            raise
    
    def get_active_mappings_dict(self, file_id=None):
        """활성화된 매핑을 딕셔너리로 반환 (original_column: code_name)"""
        try:
            mappings = self.get_last_mappings(file_id) if not file_id else self.get_mappings_by_file(file_id)
            
            # 활성화된 매핑만 필터링하여 딕셔너리로 변환
            mapping_dict = {}
            for mapping in mappings:
                if mapping.get('is_activate', True):
                    original = mapping.get('original_column')
                    code_name = mapping.get('code_name')
                    if original and code_name:
                        mapping_dict[original] = code_name
            
            return mapping_dict
        except Exception as e:
            logger.error(f"활성 매핑 딕셔너리 생성 실패: {e}")
            raise

