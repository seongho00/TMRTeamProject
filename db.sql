DROP DATABASE IF EXISTS `TMRTeamProject`;
CREATE DATABASE `TMRTeamProject`;
USE `TMRTeamProject`;

CREATE TABLE `member` (
                          id INT(10) AUTO_INCREMENT PRIMARY KEY,
                          reg_date DATETIME NOT NULL,
                          update_date DATETIME NOT NULL,
                          `name` VARCHAR(50) NOT NULL,
                          login_pw VARCHAR(100) NOT NULL,
                          email VARCHAR(100) NOT NULL,
                          phone_num VARCHAR(20)
);

CREATE TABLE floating_population (
                                     id BIGINT AUTO_INCREMENT PRIMARY KEY,
                                     region_name VARCHAR(100),             -- 예: 강남구 역삼동
                                     gender ENUM('M', 'F') NOT NULL,       -- 남(M), 여(F)
                                     age_group VARCHAR(10) NOT NULL,       -- 예: '10대', '20대'
                                     population_count INT NOT NULL,        -- 유동인구 수
                                     collected_date DATE NOT NULL,         -- 데이터 수집 기준일
                                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admin_dong (
                            admi_nm VARCHAR(100),
                            sido_cd CHAR(2),
                            sido_nm VARCHAR(20),
                            sgg_cd CHAR(5),
                            sgg_nm VARCHAR(20),
                            emd_cd CHAR(10) PRIMARY KEY,
                            emd_nm VARCHAR(20)
);

CREATE TABLE population_stat (
                                 id INT AUTO_INCREMENT PRIMARY KEY,
                                 emd_cd CHAR(10),
                                 total INT,
                                 male INT,
                                 female INT,
                                 age_10 INT,
                                 age_20 INT,
                                 age_30 INT,
                                 age_40 INT,
                                 age_50 INT,
                                 age_60 INT
);

CREATE TABLE upjong_code (
                             major_cd VARCHAR(10),
                             major_nm VARCHAR(50),
                             middle_cd VARCHAR(10),
                             middle_nm VARCHAR(100),
                             minor_cd VARCHAR(10),
                             minor_nm VARCHAR(100)
);

/* LH청약플러스 상가 공고 정보 */
CREATE TABLE `lh_apply_info` (
                                 `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                                 `site_no` INT NOT NULL COMMENT 'LH 원본 번호',
                                 `reg_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                 `update_date` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                 `title` VARCHAR(255) NOT NULL,
                                 `address` VARCHAR(255) NOT NULL,
                                 `post_date` DATE NULL,
                                 `deadline_date` DATE NULL,
                                 `ann_date` DATE NULL COMMENT '게시일',
                                 `status` VARCHAR(30) NULL,
                                 `views` INT UNSIGNED NULL,
                                 `call_number` VARCHAR(50) NULL,
                                 `attachments` TEXT NULL COMMENT '첨부파일',
                                 `extracted_text` LONGTEXT NULL COMMENT 'pdf 전체 텍스트',
                                 `markdown_text` LONGTEXT NULL COMMENT '추출된 PDF 전체 내용 마크다운',
                                 `markdown_status` VARCHAR(30) NOT NULL DEFAULT 'PENDING' COMMENT '마크다운 변환 상태',
                                 `processing_status` VARCHAR(30) NOT NULL DEFAULT 'PENDING' COMMENT 'LLM 처리 상태',
                                 PRIMARY KEY (`id`),
                                 UNIQUE KEY `uk_site_no` (`site_no`),
                                 KEY `idx_title_post` (`title`, `post_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

/* LH 상가 상세정보 */
CREATE TABLE `lh_shop_detail` (
                                  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '고유 ID',
                                  `lh_apply_info_id` BIGINT UNSIGNED NOT NULL COMMENT '원본 공고 ID',
                                  `supply_type_detail` VARCHAR(100) NULL COMMENT '상세 공급유형',
                                  `complex_type` VARCHAR(100) NULL COMMENT '단지 유형',
                                  `shop_usage` VARCHAR(100) NULL COMMENT '용도',
                                  `dong` VARCHAR(50) NULL COMMENT '동',
                                  `floor` VARCHAR(50) NULL COMMENT '층',
                                  `ho` VARCHAR(50) NULL COMMENT '호수',
                                  `area_exclusive` DOUBLE NULL COMMENT '전용 면적',
                                  `area_common` DOUBLE NULL COMMENT '공용 면적',
                                  `area_common_etc` DOUBLE NULL COMMENT '기타 공용 면적',
                                  `area_total` DOUBLE NULL COMMENT '분양/임대 면적 (계)',
                                  `land_stake` DOUBLE NULL COMMENT '공유대지 지분',
                                  `deposit` BIGINT NULL COMMENT '임대 보증금 (계)',
                                  `deposit_down_payment` BIGINT NULL COMMENT '임대보증금 (계약금)',
                                  `deposit_balance` BIGINT NULL COMMENT '임대보증금 (잔금)',
                                  `rent_monthly` BIGINT NULL COMMENT '월 임대료 (VAT 별도)',
                                  `price_estimated` BIGINT NULL COMMENT '분양 예정가격',
                                  `rent_total_period` BIGINT NULL COMMENT '기간 총 임대료',
                                  `rent_period_months` INT NULL COMMENT '임대료 기간 (개월)',
                                  `housing_units` INT NULL COMMENT '주택 세대수',
                                  `capacity_personnel` INT NULL COMMENT '추정 정원 (명)',
                                  `move_in_date` VARCHAR(100) NULL COMMENT '입주(입점) 가능 시기',
                                  `remarks` VARCHAR(255) NULL COMMENT '비고',
                                  PRIMARY KEY (`id`),
                                  CONSTRAINT `fk_detail_to_info` FOREIGN KEY (`lh_apply_info_id`)
                                      REFERENCES `lh_apply_info` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT = 'LH 상가 공고별 상세 정보';