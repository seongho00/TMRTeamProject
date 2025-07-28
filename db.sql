DROP
DATABASE IF EXISTS `TMRTeamProject`;
CREATE
DATABASE `TMRTeamProject`;
USE
`TMRTeamProject`;


CREATE TABLE `member`
(
    id          INT(10) AUTO_INCREMENT PRIMARY KEY,
    reg_date    DATETIME     NOT NULL,
    update_date DATETIME     NOT NULL,
    `name`      VARCHAR(50)  NOT NULL,
    login_pw    VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL,
    phone_num   VARCHAR(20)
);

CREATE TABLE floating_population
(
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    region_name      VARCHAR(100),            -- 예: 강남구 역삼동
    gender           ENUM('M', 'F') NOT NULL, -- 남(M), 여(F)
    age_group        VARCHAR(10) NOT NULL,    -- 예: '10대', '20대'
    population_count INT         NOT NULL,    -- 유동인구 수
    collected_date   DATE        NOT NULL,    -- 데이터 수집 기준일
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admin_dong
(
    admi_nm VARCHAR(100),         -- 전체 이름
    sido_cd CHAR(2),
    sido_nm VARCHAR(20),
    sgg_cd  CHAR(5),
    sgg_nm  VARCHAR(20),
    emd_cd  CHAR(10) PRIMARY KEY, -- 읍면동 코드 (PK)
    emd_nm  VARCHAR(20)
);

CREATE TABLE population_stat
(
    id     INT AUTO_INCREMENT PRIMARY KEY,
    emd_cd CHAR(10), -- 읍면동 코드
    total  INT,
    male   INT,
    female INT,
    age_10 INT,
    age_20 INT,
    age_30 INT,
    age_40 INT,
    age_50 INT,
    age_60 INT

);

# 업종별 코드 저장
CREATE TABLE upjong_code
(
    major_cd  VARCHAR(10),  -- 대분류 코드
    major_nm  VARCHAR(50),  -- 대분류명
    middle_cd VARCHAR(10),  -- 중분류 코드
    middle_nm VARCHAR(100), -- 중분류명
    minor_cd  VARCHAR(10),  -- 소분류 코드
    minor_nm  VARCHAR(100)  -- 소분류명
);

CREATE TABLE resident_stats
(
    emd_cd              CHAR(10) PRIMARY KEY,
    total_households    INT(10) NOT NULL COMMENT '전체세대수',
    total_population    INT(10) NOT NULL COMMENT '전체인구수',
    main_facility_count INT(10) NOT NULL COMMENT '주요시설수',
    misc_facility_count INT(10) NOT NULL COMMENT '잡객시설수'

);

# pdf 파일 저장
CREATE TABLE pdf_files
(
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    region_name VARCHAR(100),
    upjong_type VARCHAR(100),
    file_name   VARCHAR(255),
    file_data   LONGBLOB
);

SELECT *
FROM pdf_files;

# pdf파일 추출된 내용 저장
CREATE TABLE trade_area
(
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    regionName   VARCHAR(100),
    industry     VARCHAR(100),
    storeCount   INT,
    storeCountYoyChange DOUBLE,
    footTraffic  INT,
    monthlySales INT,
    salesYoyChange DOUBLE,
    salesMomChange DOUBLE,
    peakDay      VARCHAR(100),
    peakTime     VARCHAR(100)
);

SELECT *
FROM trade_area;
