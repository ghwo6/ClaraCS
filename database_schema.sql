-- ClaraCS 데이터베이스 스키마
-- MySQL 8.0+

-- 데이터베이스 생성
CREATE DATABASE clara_cs;

USE clara_cs;

-- 테이블 생성
CREATE TABLE `tb_user` (
  `user_id` INT PRIMARY KEY AUTO_INCREMENT,
  `username` VARCHAR(150) NOT NULL,
  `email` VARCHAR(255) UNIQUE NOT NULL,
  `password_hash` VARCHAR(255),
  `role` VARCHAR(20) DEFAULT 'user',
  `created_at` DATETIME DEFAULT (NOW()),
  `updated_at` DATETIME
);

CREATE TABLE `tb_uploaded_file_extension_code` (
  `extension_code_id` INT PRIMARY KEY AUTO_INCREMENT,
  `extension_name` VARCHAR(16) NOT NULL,
  `description` VARCHAR(255)
);

CREATE TABLE `tb_uploaded_file` (
  `file_id` INT PRIMARY KEY AUTO_INCREMENT,
  `user_id` INT,
  `original_filename` VARCHAR(512) NOT NULL,
  `storage_path` VARCHAR(1024),
  `extension_code_id` INT,
  `row_count` INT,
  `status` VARCHAR(20) DEFAULT 'uploaded',
  `is_deleted` BOOLEAN,
  `deleted_at` DATETIME,
  `created_at` DATETIME DEFAULT (NOW()),
  `processed_at` DATETIME
);

CREATE TABLE `tb_column_mapping_code` (
  `mapping_code_id` INT PRIMARY KEY AUTO_INCREMENT,
  `code_name` VARCHAR(100) NOT NULL,
  `description` VARCHAR(255)
);

CREATE TABLE `tb_column_mapping` (
  `mapping_id` INT PRIMARY KEY AUTO_INCREMENT,
  `file_id` INT,
  `original_column` VARCHAR(255) NOT NULL,
  `mapping_code_id` INT,
  `is_activate` BOOLEAN,
  `created_at` DATETIME DEFAULT (NOW())
);

CREATE TABLE `tb_category` (
  `category_id` INT PRIMARY KEY AUTO_INCREMENT,
  `category_name` VARCHAR(150) NOT NULL,
  `parent_category_id` INT,
  `description` VARCHAR(255),
  `created_at` DATETIME DEFAULT (NOW())
);

CREATE TABLE `tb_ticket` (
  `ticket_id` INT PRIMARY KEY AUTO_INCREMENT,
  `file_id` INT,
  `user_id` INT,
  `received_at` DATETIME,
  `channel` VARCHAR(64),
  `customer_id` VARCHAR(128),
  `product_code` VARCHAR(128),
  `inquiry_type` VARCHAR(128),
  `title` VARCHAR(1000),
  `body` TEXT,
  `status` VARCHAR(20) DEFAULT 'new',
  `created_at` DATETIME DEFAULT (NOW()),
  `updated_at` DATETIME,
  `raw_data` JSON
);

CREATE TABLE `tb_classification_result` (
  `class_result_id` INT PRIMARY KEY AUTO_INCREMENT,
  `ticket_id` INT,
  `engine_name` VARCHAR(100),
  `classified_at` DATETIME DEFAULT (NOW()),
  `needs_review` BOOLEAN DEFAULT FALSE
);

CREATE TABLE `tb_classification_category_result` (
  `cat_result_id` INT PRIMARY KEY AUTO_INCREMENT,
  `class_result_id` INT,
  `category_id` INT,
  `count` INT DEFAULT 0,
  `ratio` FLOAT,
  `example_keywords` JSON
);

CREATE TABLE `tb_classification_channel_result` (
  `ch_result_id` INT AUTO_INCREMENT,
  `channel` VARCHAR(64),
  `class_result_id` INT,
  `category_id` INT,
  `count` INT DEFAULT 0,
  `ratio` FLOAT,
  PRIMARY KEY (`ch_result_id`, `channel`)
);

CREATE TABLE `tb_classification_reliability_result` (
  `reliability_id` INT PRIMARY KEY AUTO_INCREMENT,
  `class_result_id` INT,
  `metric_name` VARCHAR(128),
  `metric_value` FLOAT,
  `details` JSON,
  `created_at` DATETIME DEFAULT (NOW())
);

CREATE TABLE `tb_analysis_report` (
  `report_id` INT PRIMARY KEY AUTO_INCREMENT,
  `file_id` INT,
  `created_by` INT,
  `report_type` VARCHAR(50),
  `title` VARCHAR(255),
  `status` VARCHAR(20) DEFAULT 'queued',
  `file_path` VARCHAR(1024),
  `created_at` DATETIME DEFAULT (NOW()),
  `completed_at` DATETIME
);

CREATE TABLE `tb_analysis_channel_snapshot` (
  `channel_snapshot_id` INT PRIMARY KEY AUTO_INCREMENT,
  `report_id` INT,
  `channel` VARCHAR(64),
  `time_period` DATE,
  `category_id` INT,
  `count` INT
);

CREATE TABLE `tb_analysis_summary_snapshot` (
  `summary_snapshot_id` INT PRIMARY KEY AUTO_INCREMENT,
  `report_id` INT,
  `total_tickets` INT,
  `resolved_count` JSON,
  `category_ratios` JSON,
  `repeat_rate` FLOAT,
  `created_at` DATETIME DEFAULT (NOW())
);

CREATE TABLE `tb_analysis_solution_snapshot` (
  `solution_id` INT PRIMARY KEY AUTO_INCREMENT,
  `report_id` INT,
  `solution_payload` JSON,
  `created_at` DATETIME DEFAULT (NOW())
);

CREATE TABLE `tb_analysis_insight_snapshot` (
  `insight_id` INT PRIMARY KEY AUTO_INCREMENT,
  `report_id` INT,
  `insight_payload` JSON,
  `created_at` DATETIME DEFAULT (NOW())
);