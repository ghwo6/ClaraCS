-- ============================================================
-- 파일 배치 기능 롤백 스크립트
-- 목적: add_file_batch_support.sql 적용 내용을 되돌리기
-- 작성일: 2025-10-20
-- ============================================================

USE clara_cs;

-- ============================================================
-- 1. 뷰 삭제
-- ============================================================

DROP VIEW IF EXISTS v_batch_summary;


-- ============================================================
-- 2. 인덱스 삭제
-- ============================================================

-- tb_analysis_report
ALTER TABLE `tb_analysis_report`
DROP INDEX IF EXISTS idx_report_batch_id;

-- tb_classification_result
ALTER TABLE `tb_classification_result`
DROP INDEX IF EXISTS idx_classification_batch_id;

-- tb_uploaded_file
ALTER TABLE `tb_uploaded_file`
DROP INDEX IF EXISTS idx_uploaded_file_batch_id;


-- ============================================================
-- 3. 컬럼 삭제
-- ============================================================

-- tb_analysis_report
ALTER TABLE `tb_analysis_report`
DROP COLUMN IF EXISTS `batch_id`;

-- tb_classification_result
ALTER TABLE `tb_classification_result`
DROP COLUMN IF EXISTS `batch_id`;

-- tb_uploaded_file
ALTER TABLE `tb_uploaded_file`
DROP COLUMN IF EXISTS `batch_id`;


-- ============================================================
-- 4. 배치 테이블 삭제
-- ============================================================

DROP TABLE IF EXISTS `tb_file_batch`;


-- ============================================================
-- 롤백 완료
-- ============================================================

SELECT '파일 배치 기능 롤백 완료!' as message;

