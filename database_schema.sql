-- ClaraCS 데이터베이스 스키마
-- MySQL 8.0+

-- 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS clara_cs 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE clara_cs;

-- 1. CS 티켓 테이블
CREATE TABLE IF NOT EXISTS cs_tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    channel VARCHAR(50) NOT NULL COMMENT '접수 채널 (전화, 이메일, 게시판, 카카오톡, 네이버톡톡 등)',
    customer_id VARCHAR(100) NOT NULL COMMENT '고객 ID 또는 이메일',
    title VARCHAR(255) DEFAULT NULL COMMENT '문의 제목',
    content TEXT NOT NULL COMMENT '문의 내용',
    status VARCHAR(20) NOT NULL DEFAULT '신규' COMMENT '처리 상태 (신규, 진행중, 완료, 보류)',
    priority VARCHAR(20) DEFAULT NULL COMMENT '우선순위 (높음, 보통, 낮음)',
    assigned_to VARCHAR(100) DEFAULT NULL COMMENT '담당자',
    category VARCHAR(100) DEFAULT NULL COMMENT '수동 분류 카테고리',
    resolution_time FLOAT DEFAULT NULL COMMENT '해결 소요 시간 (시간 단위)',
    
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_channel (channel),
    INDEX idx_status (status),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CS 티켓 테이블';

-- 2. 자동 분류 결과 테이블
CREATE TABLE IF NOT EXISTS classified_data (
    classification_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    ticket_id VARCHAR(50) NOT NULL,
    classified_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    predicted_category VARCHAR(100) NOT NULL COMMENT 'AI가 예측한 카테고리',
    confidence_score FLOAT NOT NULL COMMENT '분류 신뢰도 (0.0 ~ 1.0)',
    keywords TEXT DEFAULT NULL COMMENT '추출된 키워드 (콤마로 구분)',
    sentiment VARCHAR(20) DEFAULT NULL COMMENT '감정 분석 결과 (긍정, 부정, 중립)',
    urgency_level INT DEFAULT NULL COMMENT '긴급도 (1~5)',
    
    INDEX idx_user_id (user_id),
    INDEX idx_ticket_id (ticket_id),
    INDEX idx_classified_at (classified_at),
    INDEX idx_predicted_category (predicted_category),
    
    FOREIGN KEY (ticket_id) REFERENCES cs_tickets(ticket_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='자동 분류 결과 테이블';

-- 3. 컬럼 매핑 테이블 (기존 테이블 유지)
CREATE TABLE IF NOT EXISTS tb_column_mapping (
    mapping_id INT AUTO_INCREMENT PRIMARY KEY,
    original_column VARCHAR(100) NOT NULL COMMENT '원본 파일의 컬럼명',
    file_id VARCHAR(50) NOT NULL COMMENT '파일 ID',
    mapping_code_id VARCHAR(50) NOT NULL COMMENT '매핑 코드 ID',
    is_activate BOOLEAN NOT NULL DEFAULT TRUE COMMENT '활성화 여부',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_file_id (file_id),
    INDEX idx_mapping_code_id (mapping_code_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='컬럼 매핑 테이블';

-- 4. 사용자 테이블 (선택사항 - 추후 확장용)
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME DEFAULT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자 테이블';

-- 5. 리포트 생성 이력 테이블 (선택사항)
CREATE TABLE IF NOT EXISTS report_history (
    report_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    report_type VARCHAR(50) NOT NULL COMMENT '리포트 유형',
    start_date DATE DEFAULT NULL,
    end_date DATE DEFAULT NULL,
    total_tickets INT NOT NULL DEFAULT 0,
    
    INDEX idx_user_id (user_id),
    INDEX idx_generated_at (generated_at),
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='리포트 생성 이력 테이블';

-- ============================================
-- 샘플 데이터 삽입
-- ============================================

-- 사용자 샘플 데이터
INSERT INTO users (user_id, username, email) VALUES 
('user_001', '김철수', 'kimcs@example.com'),
('user_002', '이영희', 'leeyh@example.com')
ON DUPLICATE KEY UPDATE username=VALUES(username);

-- CS 티켓 샘플 데이터
INSERT INTO cs_tickets (ticket_id, user_id, created_at, channel, customer_id, title, content, status, priority, category, resolution_time) VALUES 
('TICKET_001', 'user_001', '2025-10-01 10:30:00', '전화', 'cust_1001', '배송 지연 문의', '주문한 상품이 아직 도착하지 않았습니다.', '완료', '높음', '배송지연', 2.5),
('TICKET_002', 'user_001', '2025-10-01 14:20:00', '이메일', 'cust_1002', '환불 요청', '제품이 파손되어 환불을 요청합니다.', '완료', '높음', '환불문의', 1.5),
('TICKET_003', 'user_001', '2025-10-02 09:15:00', '게시판', 'cust_1003', '제품 사용 문의', '제품 사용법을 알고 싶습니다.', '완료', '보통', 'AS요청', 0.5),
('TICKET_004', 'user_001', '2025-10-02 11:45:00', '카카오톡', 'cust_1004', '색상 변경 가능한가요?', '주문한 제품의 색상을 변경하고 싶습니다.', '진행중', '보통', '기타문의', NULL),
('TICKET_005', 'user_001', '2025-10-03 08:30:00', '네이버톡톡', 'cust_1005', '배송 추적', '배송 상태를 확인하고 싶습니다.', '신규', '보통', '배송지연', NULL),
('TICKET_006', 'user_001', '2025-10-03 13:20:00', '전화', 'cust_1006', '제품 불량', '제품에 흠집이 있습니다.', '완료', '높음', '품질불만', 3.0),
('TICKET_007', 'user_001', '2025-10-04 10:10:00', '이메일', 'cust_1007', 'AS 센터 문의', 'AS 센터 위치를 알고 싶습니다.', '완료', '낮음', 'AS요청', 0.3),
('TICKET_008', 'user_001', '2025-10-04 15:30:00', '게시판', 'cust_1008', '교환 요청', '사이즈가 맞지 않아 교환하고 싶습니다.', '진행중', '보통', '환불문의', NULL)
ON DUPLICATE KEY UPDATE content=VALUES(content);

-- 자동 분류 결과 샘플 데이터
INSERT INTO classified_data (classification_id, user_id, ticket_id, classified_at, predicted_category, confidence_score, keywords, sentiment, urgency_level) VALUES 
('CLASS_001', 'user_001', 'TICKET_001', '2025-10-01 10:31:00', '배송지연', 0.95, '배송,지연,도착', '부정', 4),
('CLASS_002', 'user_001', 'TICKET_002', '2025-10-01 14:21:00', '환불문의', 0.92, '환불,파손,제품', '부정', 5),
('CLASS_003', 'user_001', 'TICKET_003', '2025-10-02 09:16:00', 'AS요청', 0.88, '사용법,제품,문의', '중립', 2),
('CLASS_004', 'user_001', 'TICKET_004', '2025-10-02 11:46:00', '기타문의', 0.85, '색상,변경,주문', '중립', 3),
('CLASS_005', 'user_001', 'TICKET_005', '2025-10-03 08:31:00', '배송지연', 0.90, '배송,추적,확인', '중립', 3),
('CLASS_006', 'user_001', 'TICKET_006', '2025-10-03 13:21:00', '품질불만', 0.93, '불량,흠집,제품', '부정', 4),
('CLASS_007', 'user_001', 'TICKET_007', '2025-10-04 10:11:00', 'AS요청', 0.87, 'AS,센터,위치', '중립', 2),
('CLASS_008', 'user_001', 'TICKET_008', '2025-10-04 15:31:00', '환불문의', 0.89, '교환,사이즈,제품', '중립', 3)
ON DUPLICATE KEY UPDATE confidence_score=VALUES(confidence_score);

-- ============================================
-- 유용한 조회 쿼리
-- ============================================

-- 1. 채널별 티켓 수 조회
-- SELECT channel, COUNT(*) as count FROM cs_tickets GROUP BY channel;

-- 2. 카테고리별 분류 결과 조회
-- SELECT predicted_category, COUNT(*) as count, AVG(confidence_score) as avg_confidence 
-- FROM classified_data GROUP BY predicted_category;

-- 3. 최근 7일간 티켓 추이
-- SELECT DATE(created_at) as date, COUNT(*) as count 
-- FROM cs_tickets 
-- WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
-- GROUP BY DATE(created_at);

-- 4. 평균 해결 시간 조회
-- SELECT AVG(resolution_time) as avg_resolution_time 
-- FROM cs_tickets 
-- WHERE resolution_time IS NOT NULL;

-- 5. 감정별 티켓 분포
-- SELECT sentiment, COUNT(*) as count 
-- FROM classified_data 
-- GROUP BY sentiment;

