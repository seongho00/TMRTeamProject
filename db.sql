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


SELECT * FROM admin_dong;
SELECT * FROM population_stat;

SELECT * FROM admin_dong;

# 업종별 코드 저장
CREATE TABLE upjong_code (
                             reg_date DATETIME NOT NULL,
                             update_date DATETIME NOT NULL,
                             upjong_cd VARCHAR(10) PRIMARY KEY,        -- 업종코드
                             upjong_nm VARCHAR(50)      -- 업종명
);

CREATE TABLE risk_score (
                            emd_cd         VARCHAR(20)  NOT NULL,
                            upjong_cd      VARCHAR(20)  NOT NULL,
                            reg_date       DATETIME     NOT NULL,
                            update_date    DATETIME     NOT NULL,
                            risk_raw       DECIMAL(6,4) NOT NULL,   -- 소수 정밀도 확보(예: -0.4000 ~ 0.2000)
                            risk_label     INT          NULL,
                            risk7_label    VARCHAR(10)  NULL,
                            risk_pred      INT          NULL,
                            risk100_all    DECIMAL(5,1) NULL,
                            risk100_by_biz DECIMAL(5,1) NULL,
                            PRIMARY KEY (emd_cd, upjong_cd),
                            KEY idx_risk_score_upjong (upjong_cd)
)
SELECT * FROM upjong_code;
