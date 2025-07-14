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

# 행정동 코드 저장
CREATE TABLE admin_dong (
                            admi_nm VARCHAR(100),                -- 전체 이름
                            sido_cd CHAR(2),
                            sido_nm VARCHAR(20),
                            sgg_cd CHAR(5),
                            sgg_nm VARCHAR(20),
                            emd_cd CHAR(10) PRIMARY KEY,         -- 읍면동 코드 (PK)
                            emd_nm VARCHAR(20)
);

SELECT * FROM admin_dong;

# 업종별 코드 저장
CREATE TABLE upjong_code (
                             major_cd VARCHAR(10),        -- 대분류 코드
                             major_nm VARCHAR(50),        -- 대분류명
                             middle_cd VARCHAR(10),       -- 중분류 코드
                             middle_nm VARCHAR(100),      -- 중분류명
                             minor_cd VARCHAR(10),        -- 소분류 코드
                             minor_nm VARCHAR(100)        -- 소분류명
);

SELECT * FROM upjong_code;