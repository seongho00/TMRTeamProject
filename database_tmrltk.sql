DROP DATABASE IF EXISTS `tmrltk`;
CREATE DATABASE `tmrltk` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `tmrltk`;

CREATE TABLE `member`
(
    `id`          INT(10)      NOT NULL,
    `reg_date`    DATETIME     NOT NULL,
    `update_date` DATETIME     NOT NULL,
    `login_id`    VARCHAR(30)  NOT NULL,
    `login_pw`    VARCHAR(100) NOT NULL,
    `del_state`   TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '0: 미삭제, 1: 삭제',
    `del_date`    DATETIME     NULL COMMENT '삭제 날짜',
    `name`        VARCHAR(10)  NOT NULL,
    `email`       VARCHAR(30)  NOT NULL,
    PRIMARY KEY (`id`)
);

CREATE TABLE `question_type`
(
    `id`          INT(10)      NOT NULL,
    `reg_date`    DATETIME     NOT NULL,
    `update_date` DATETIME     NOT NULL,
    `code`        VARCHAR(10)  NOT NULL,
    `name`        VARCHAR(50)  NOT NULL,
    `description` VARCHAR(255) NOT NULL COMMENT '예: 사용자 상권 조회 요청',
    `field`       VARCHAR(255) NULL,
    PRIMARY KEY (`id`)
);

CREATE TABLE `gender_ratio`
(
    `id`                  INT(10)     NOT NULL,
    `gender`              VARCHAR(10) NOT NULL,
    `ratio`               FLOAT       NOT NULL,
    `commercial_stats_id` INT(10)     NOT NULL,
    PRIMARY KEY (`id`)
);

CREATE TABLE `item`
(
    `id`        INT(10)      NOT NULL,
    `item_code` VARCHAR(14)  NOT NULL,
    `item_type` VARCHAR(5)   NOT NULL,
    `field3`    VARCHAR(100) NOT NULL,
    `field4`    VARCHAR(20)  NOT NULL,
    `field5`    DATETIME     NOT NULL,
    `field6`    VARCHAR(20)  NOT NULL,
    `field2`    VARCHAR(20)  NOT NULL,
    PRIMARY KEY (`id`, `item_code`)
);

CREATE TABLE `store`
(
    `id`               INT(10)       NOT NULL,
    `store_num`        VARCHAR(50)   NOT NULL,
    `store_name`       VARCHAR(100)  NOT NULL,
    `road_address`     VARCHAR(200)  NOT NULL,
    `number_address`   VARCHAR(200)  NOT NULL,
    `old_zip_code`     VARCHAR(255)  NULL,
    `new_zip_code`     VARCHAR(255)  NULL,
    `floor_number`     VARCHAR(255)  NULL,
    `mapx`             DOUBLE(10, 7) NOT NULL,
    `mapy`             DOUBLE(10, 7) NOT NULL,
    `room_number`      VARCHAR(255)  NULL,
    `area_code_id`     INT(10)       NOT NULL,
    `industry_code_id` INT(10)       NOT NULL,
    PRIMARY KEY (`id`)
);

CREATE TABLE `commercial_data`
(
    `id`                  INT(10) NOT NULL,
    `sales`               INT     NOT NULL,
    `store_count`         INT     NOT NULL,
    `foot_traffic`        INT     NOT NULL,
    `commercial_stats_id` INT(10) NOT NULL,
    `area_code_id`        INT(10) NOT NULL,
    PRIMARY KEY (`id`)
);

CREATE TABLE `area_code`
(
    `id`            INT(10)     NOT NULL,
    `reg_date`      DATETIME    NOT NULL,
    `update_date`   DATETIME    NOT NULL,
    `sido_code`     VARCHAR(10) NOT NULL,
    `sido_name`     VARCHAR(20) NOT NULL,
    `sigungu_code`  VARCHAR(10) NOT NULL,
    `sigungu_name`  VARCHAR(20) NOT NULL,
    `adm_dong_code` VARCHAR(10) NOT NULL,
    `adm_dong_name` VARCHAR(20) NOT NULL,
    `full_code`     VARCHAR(20) NOT NULL,
    PRIMARY KEY (`id`)
);


/*
 LH청약플러스 상가
 */
CREATE TABLE `lh_apply_info`
(
    `id`                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `site_no`             INT             NOT NULL COMMENT 'LH 원본 번호',
    `reg_date`            DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_date`         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `title`               VARCHAR(255)    NOT NULL,
    `address`             VARCHAR(255)    NOT NULL,
    `post_date`           DATE            NULL,
    `deadline_date`       DATE            NULL,
    `ann_date`            DATE            NULL     COMMENT '게시일',
    `status`              VARCHAR(30)     NULL,
    `views`               INT UNSIGNED    NULL,
    `call_number`         VARCHAR(50)     NULL,
    `attachments`         TEXT            NULL     COMMENT '첨부파일',
    `extracted_text`      LONGTEXT        NULL     COMMENT 'pdf 전체 텍스트',
    `markdown_text`       LONGTEXT        NULL     COMMENT '추출된 PDF 전체 내용 마크다운',
    `markdown_status`     VARCHAR(30)     NOT NULL DEFAULT 'PENDING' COMMENT '마크다운 변환 상태',
    `processing_status`   VARCHAR(30)     NOT NULL DEFAULT 'PENDING' COMMENT 'LLM 처리 상태',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_site_no` (`site_no`),
    KEY `idx_title_post` (`title`, `post_date`)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;

/*
 상가 상세정보
 */
CREATE TABLE `lh_shop_detail`
(
    `id`                     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '고유 ID',
    `lh_apply_info_id`       BIGINT UNSIGNED NOT NULL COMMENT '원본 공고 ID',
    `supply_type_detail`     VARCHAR(100)    NULL     COMMENT '상세 공급유형',
    `complex_type`           VARCHAR(100)    NULL     COMMENT '단지 유형',
    `shop_usage`             VARCHAR(100)    NULL     COMMENT '용도',
    `dong`                   VARCHAR(50)     NULL     COMMENT '동',
    `floor`                  VARCHAR(50)     NULL     COMMENT '층',
    `ho`                     VARCHAR(50)     NULL     COMMENT '호수',
    `area_exclusive`         DOUBLE          NULL     COMMENT '전용 면적',
    `area_common`            DOUBLE          NULL     COMMENT '공용 면적',
    `area_common_etc`        DOUBLE          NULL     COMMENT '기타 공용 면적',
    `area_total`             DOUBLE          NULL     COMMENT '분양/임대 면적 (계)',
    `land_stake`             DOUBLE          NULL     COMMENT '공유대지 지분',
    `deposit`                BIGINT          NULL     COMMENT '임대 보증금 (계)',
    `deposit_down_payment`   BIGINT          NULL     COMMENT '임대보증금 (계약금)',
    `deposit_balance`        BIGINT          NULL     COMMENT '임대보증금 (잔금)',
    `rent_monthly`           BIGINT          NULL     COMMENT '월 임대료 (VAT 별도)',
    `price_estimated`        BIGINT          NULL     COMMENT '분양 예정가격',
    `rent_total_period`      BIGINT          NULL     COMMENT '기간 총 임대료',
    `rent_period_months`     INT             NULL     COMMENT '임대료 기간 (개월)',
    `housing_units`          INT             NULL     COMMENT '주택 세대수',
    `capacity_personnel`     INT             NULL     COMMENT '추정 정원 (명)',
    `move_in_date`           VARCHAR(100)    NULL     COMMENT '입주(입점) 가능 시기',
    `remarks`                VARCHAR(255)    NULL     COMMENT '비고',
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_detail_to_info` FOREIGN KEY (`lh_apply_info_id`)
        REFERENCES `lh_apply_info` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT = 'LH 상가 공고별 상세 정보';

CREATE TABLE `commercial_stats`
(
    `id`               INT(10) NOT NULL,
    `area_code_id`     INT(10) NOT NULL,
    `industry_code_id` INT(10) NOT NULL,
    `sales`            INT     NOT NULL,
    `delivery_count`   INT     NOT NULL,
    `store_count`      INT     NOT NULL,
    `foot_traffic`     INT     NOT NULL,
    PRIMARY KEY (`id`)
);

CREATE TABLE `industry_code`
(
    `id`          INT(10)     NOT NULL,
    `reg_date`    DATETIME    NOT NULL,
    `update_date` DATETIME    NOT NULL,
    `major_code`  VARCHAR(10) NOT NULL,
    `major_name`  VARCHAR(50) NOT NULL,
    `mid_code`    VARCHAR(10) NOT NULL,
    `mid_name`    VARCHAR(50) NOT NULL,
    `minor_code`  VARCHAR(10) NOT NULL,
    `minor_name`  VARCHAR(50) NOT NULL,
    PRIMARY KEY (`id`)
);

CREATE TABLE `qa`
(
    `id`               INT(10)     NOT NULL,
    `reg_time`         DATETIME    NOT NULL,
    `question_text`    TEXT        NOT NULL,
    `response_text`    TEXT        NOT NULL,
    `question_type_id` VARCHAR(50) NOT NULL,
    `member_id`        INT(10)     NOT NULL,
    PRIMARY KEY (`id`)
);

CREATE TABLE `office`
(
    `id`         INT(10)     NOT NULL,
    `open_regno` VARCHAR(20) NOT NULL,
    `o_name`     VARCHAR(20) NOT NULL,
    `b_name`     VARCHAR(15) NOT NULL,
    `o_num`      VARCHAR(20) NOT NULL,
    `b_num`      VARCHAR(20) NOT NULL,
    `item_id`    INT(10)     NOT NULL,
    PRIMARY KEY (`id`, `open_regno`)
);

CREATE TABLE `age_ratio`
(
    `id`                  INT(10)     NOT NULL,
    `age_group`           VARCHAR(10) NOT NULL,
    `ratio`               FLOAT       NOT NULL,
    `commercial_stats_id` INT(10)     NOT NULL,
    PRIMARY KEY (`id`)
);