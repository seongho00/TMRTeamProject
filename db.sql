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


