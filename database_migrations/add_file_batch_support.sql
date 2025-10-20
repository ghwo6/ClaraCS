-- ============================================================
-- 파일 배치(그룹) 기능 추가 마이그레이션
-- 목적: 여러 파일을 하나의 배치로 묶어서 통합 분류 및 리포트 생성
-- 작성일: 2025-10-20
-- ============================================================

USE clara_cs;

-- ============================================================
-- 1. 파일 배치 테이블 생성
-- ============================================================

CREATE TABLE IF NOT EXISTS `tb_file_batch` (
  `batch_id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '배치 ID',
  `user_id` INT NOT NULL COMMENT '업로드한 사용자 ID',
  `batch_name` VARCHAR(255) COMMENT '배치 이름 (선택, 예: "2024년 1분기 데이터")',
  `file_count` INT DEFAULT 0 COMMENT '배치에 포함된 파일 수',
  `total_row_count` INT DEFAULT 0 COMMENT '전체 행 수',
  `status` VARCHAR(20) DEFAULT 'uploading' COMMENT '배치 상태: uploading, completed, processing, failed',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시각',
  `completed_at` DATETIME COMMENT '완료 시각',
  
  INDEX idx_batch_user_id (user_id),
  INDEX idx_batch_status (status),
  INDEX idx_batch_created_at (created_at),
  
  FOREIGN KEY (user_id) REFERENCES tb_user(user_id) ON DELETE CASCADE
) COMMENT '파일 배치 테이블 - 여러 파일을 하나의 그룹으로 관리';


-- ============================================================
-- 2. tb_uploaded_file에 batch_id 컬럼 추가
-- ============================================================

-- batch_id 컬럼 추가 (컬럼이 이미 있으면 오류 무시)
ALTER TABLE `tb_uploaded_file`
ADD COLUMN `batch_id` INT COMMENT '파일이 속한 배치 ID';

-- 인덱스 추가
ALTER TABLE `tb_uploaded_file`
ADD INDEX idx_uploaded_file_batch_id (batch_id);

-- batch_id에 외래키 제약조건 추가 (선택사항)
-- ALTER TABLE `tb_uploaded_file`
-- ADD CONSTRAINT fk_uploaded_file_batch
-- FOREIGN KEY (batch_id) REFERENCES tb_file_batch(batch_id) ON DELETE SET NULL;


-- ============================================================
-- 3. tb_classification_result에 batch_id 컬럼 추가
-- ============================================================

-- batch_id 컬럼 추가
ALTER TABLE `tb_classification_result`
ADD COLUMN `batch_id` INT COMMENT '분류 대상 배치 ID (file_id와 배타적)';

-- 인덱스 추가
ALTER TABLE `tb_classification_result`
ADD INDEX idx_classification_batch_id (batch_id);

-- file_id와 batch_id 중 하나는 반드시 있어야 함
-- (체크 제약조건은 MySQL 8.0.16+ 지원)
-- ALTER TABLE `tb_classification_result`
-- ADD CONSTRAINT chk_file_or_batch
-- CHECK (file_id IS NOT NULL OR batch_id IS NOT NULL);


-- ============================================================
-- 4. tb_analysis_report에 batch_id 컬럼 추가
-- ============================================================

-- batch_id 컬럼 추가
ALTER TABLE `tb_analysis_report`
ADD COLUMN `batch_id` INT COMMENT '리포트 대상 배치 ID (file_id와 배타적)';

-- 인덱스 추가
ALTER TABLE `tb_analysis_report`
ADD INDEX idx_report_batch_id (batch_id);


-- ============================================================
-- 5. 기존 데이터 마이그레이션 (선택사항 - 필요시 주석 해제)
-- ============================================================

-- 기존 업로드된 파일들을 각각 개별 배치로 생성하고 싶은 경우 아래 주석을 해제하세요
-- 주의: 기존 파일이 많으면 시간이 오래 걸릴 수 있습니다

/*
-- 1) 기존 파일들에 대해 batch 생성
INSERT INTO tb_file_batch (user_id, batch_name, file_count, total_row_count, status, created_at, completed_at)
SELECT 
    f.user_id,
    CONCAT('레거시 배치 - ', f.original_filename) as batch_name,
    1 as file_count,
    f.row_count as total_row_count,
    'completed' as status,
    f.created_at,
    f.processed_at
FROM tb_uploaded_file f
WHERE f.batch_id IS NULL
ORDER BY f.file_id;

-- 2) 생성된 batch_id를 파일에 할당
UPDATE tb_uploaded_file f
INNER JOIN (
    SELECT 
        f2.file_id,
        b.batch_id
    FROM tb_uploaded_file f2
    INNER JOIN tb_file_batch b 
        ON b.batch_name = CONCAT('레거시 배치 - ', f2.original_filename)
        AND b.user_id = f2.user_id
    WHERE f2.batch_id IS NULL
) mapping ON mapping.file_id = f.file_id
SET f.batch_id = mapping.batch_id;
*/


-- ============================================================
-- 6. 배치 상태 확인 뷰 생성 (편의 기능)
-- ============================================================

CREATE OR REPLACE VIEW v_batch_summary AS
SELECT 
    b.batch_id,
    b.user_id,
    b.batch_name,
    b.file_count,
    b.total_row_count,
    b.status,
    b.created_at,
    b.completed_at,
    COUNT(DISTINCT f.file_id) as actual_file_count,
    SUM(f.row_count) as actual_row_count,
    COUNT(DISTINCT t.ticket_id) as total_tickets,
    COUNT(DISTINCT cr.class_result_id) as classification_count,
    COUNT(DISTINCT ar.report_id) as report_count
FROM tb_file_batch b
LEFT JOIN tb_uploaded_file f ON f.batch_id = b.batch_id
LEFT JOIN tb_ticket t ON t.file_id = f.file_id
LEFT JOIN tb_classification_result cr ON cr.batch_id = b.batch_id
LEFT JOIN tb_analysis_report ar ON ar.batch_id = b.batch_id
GROUP BY b.batch_id
ORDER BY b.created_at DESC;


-- ============================================================
-- 7. 테스트 쿼리
-- ============================================================

-- 배치 목록 조회
-- SELECT * FROM v_batch_summary;

-- 특정 사용자의 배치 목록
-- SELECT * FROM v_batch_summary WHERE user_id = 1;

-- 특정 배치의 파일 목록
-- SELECT * FROM tb_uploaded_file WHERE batch_id = 1;

-- 특정 배치의 티켓 수
-- SELECT COUNT(*) FROM tb_ticket t
-- INNER JOIN tb_uploaded_file f ON f.file_id = t.file_id
-- WHERE f.batch_id = 1;


-- ============================================================
-- 마이그레이션 완료
-- ============================================================

SELECT '파일 배치 기능 추가 완료!' as message;

