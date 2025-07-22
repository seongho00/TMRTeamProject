DROP DATABASE IF EXISTS `TMRTeamProject`;
CREATE DATABASE `TMRTeamProject`;
USE `TMRTeamProject`;

CREATE TABLE MEMBER (
                        id INT(10) AUTO_INCREMENT PRIMARY KEY,
                        regDate DATETIME NOT NULL,
                        updateDate DATETIME NOT NULL,
                        `name` VARCHAR(50) NOT NULL,
                        loginPw VARCHAR(100) NOT NULL,
                        email VARCHAR(100) NOT NULL,
                        phoneNum VARCHAR(20)
);

CREATE TABLE admin_dong (
                            admi_nm VARCHAR(100),                -- 전체 이름
                            sido_cd CHAR(2),
                            sido_nm VARCHAR(20),
                            sgg_cd CHAR(5),
                            sgg_nm VARCHAR(20),
                            emd_cd CHAR(10) PRIMARY KEY,         -- 읍면동 코드 (PK)
                            emd_nm VARCHAR(20)
);

CREATE TABLE population_stat (
                                 id INT AUTO_INCREMENT PRIMARY KEY,
                                 emd_cd CHAR(10),             -- 읍면동 코드
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
                             major_cd VARCHAR(10),        -- 대분류 코드
                             major_nm VARCHAR(50),        -- 대분류명
                             middle_cd VARCHAR(10),       -- 중분류 코드
                             middle_nm VARCHAR(100),      -- 중분류명
                             minor_cd VARCHAR(10),        -- 소분류 코드
                             minor_nm VARCHAR(100)        -- 소분류명
);


CREATE TABLE resident_stats(
                               emd_cd CHAR(10) PRIMARY KEY,
                               total_households INT(10) NOT NULL COMMENT '전체세대수',
                               total_population INT(10) NOT NULL COMMENT '전체인구수',
                               main_facility_count INT(10) NOT NULL COMMENT '주요시설수',
                               misc_facility_count INT(10) NOT NULL COMMENT '잡객시설수'

);

