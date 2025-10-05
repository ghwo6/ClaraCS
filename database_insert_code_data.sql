-- ClaraCS 코드성 데이터 INSERT 쿼리
-- 작성일: 2025-10-05

USE clara_cs;

-- 1. tb_uploaded_file_extension_code (파일 확장자 코드)
INSERT INTO `tb_uploaded_file_extension_code` (`extension_name`, `description`) VALUES
('csv', 'CSV 파일 형식'),
('xlsx', 'Excel 파일 형식 (xlsx)'),
('xls', 'Excel 파일 형식 (xls)');

-- 2. tb_column_mapping_code (컬럼 매핑 코드)
-- 8개 필수 컬럼
INSERT INTO `tb_column_mapping_code` (`code_name`, `description`) VALUES
('접수일', '티켓 접수 날짜/시간'),
('고객ID', '고객 고유 식별자'),
('채널', 'CS 문의 채널 (전화, 이메일, 게시판 등)'),
('상품코드', '제품/상품 고유 코드'),
('문의 유형', '문의 카테고리/유형'),
('본문', '문의 내용 본문'),
('담당자', '처리 담당자'),
('처리 상태', '티켓 처리 상태');

-- 추가 컬럼 (필요시 사용)
INSERT INTO `tb_column_mapping_code` (`code_name`, `description`) VALUES
('제목', '문의 제목'),
('고객이메일', '고객 이메일 주소'),
('고객전화번호', '고객 전화번호'),
('우선순위', '티켓 처리 우선순위'),
('해결일시', '티켓 해결 완료 일시');

-- 3. tb_category (기본 카테고리 데이터)
-- 대분류 카테고리
INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) VALUES
('배송 문의', NULL, '배송/배달 관련 문의'),
('환불/교환', NULL, '환불 및 교환 요청'),
('상품 문의', NULL, '상품 관련 질문'),
('기술 지원', NULL, '제품 사용 및 기술 지원'),
('불만/클레임', NULL, '불만 사항 및 클레임'),
('기타', NULL, '기타 문의사항');

-- 하위 카테고리 예시 (배송 문의)
INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT '배송 지연', category_id, '배송이 지연되는 경우' 
FROM `tb_category` WHERE category_name = '배송 문의' AND parent_category_id IS NULL;

INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT '배송 추적', category_id, '배송 추적 요청' 
FROM `tb_category` WHERE category_name = '배송 문의' AND parent_category_id IS NULL;

INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT '파손/분실', category_id, '배송 중 파손 또는 분실' 
FROM `tb_category` WHERE category_name = '배송 문의' AND parent_category_id IS NULL;

-- 하위 카테고리 예시 (환불/교환)
INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT '환불 요청', category_id, '제품 환불 요청' 
FROM `tb_category` WHERE category_name = '환불/교환' AND parent_category_id IS NULL;

INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT '교환 요청', category_id, '제품 교환 요청' 
FROM `tb_category` WHERE category_name = '환불/교환' AND parent_category_id IS NULL;

INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT '반품 절차', category_id, '반품 절차 문의' 
FROM `tb_category` WHERE category_name = '환불/교환' AND parent_category_id IS NULL;

-- 하위 카테고리 예시 (상품 문의)
INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT '상품 정보', category_id, '상품 스펙 및 정보 문의' 
FROM `tb_category` WHERE category_name = '상품 문의' AND parent_category_id IS NULL;

INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT '재고 확인', category_id, '상품 재고 확인' 
FROM `tb_category` WHERE category_name = '상품 문의' AND parent_category_id IS NULL;

INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT '가격 문의', category_id, '가격 및 할인 정보' 
FROM `tb_category` WHERE category_name = '상품 문의' AND parent_category_id IS NULL;

-- 하위 카테고리 예시 (기술 지원)
INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT '사용법', category_id, '제품 사용 방법 문의' 
FROM `tb_category` WHERE category_name = '기술 지원' AND parent_category_id IS NULL;

INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT '고장/오작동', category_id, '제품 고장 또는 오작동' 
FROM `tb_category` WHERE category_name = '기술 지원' AND parent_category_id IS NULL;

INSERT INTO `tb_category` (`category_name`, `parent_category_id`, `description`) 
SELECT 'AS 요청', category_id, 'A/S 및 수리 요청' 
FROM `tb_category` WHERE category_name = '기술 지원' AND parent_category_id IS NULL;

-- 4. tb_user (테스트 사용자 데이터)
INSERT INTO `tb_user` (`username`, `email`, `password_hash`, `role`) VALUES
('admin', 'admin@claraCS.com', 'hashed_password_here', 'admin'),
('cs_manager', 'manager@claraCS.com', 'hashed_password_here', 'manager'),
('cs_agent1', 'agent1@claraCS.com', 'hashed_password_here', 'user'),
('cs_agent2', 'agent2@claraCS.com', 'hashed_password_here', 'user');

-- 조회 쿼리 예시
-- SELECT * FROM tb_uploaded_file_extension_code;
-- SELECT * FROM tb_column_mapping_code;
-- SELECT * FROM tb_category WHERE parent_category_id IS NULL;  -- 대분류만
-- SELECT * FROM tb_category ORDER BY parent_category_id, category_id;  -- 전체
-- SELECT * FROM tb_user;

