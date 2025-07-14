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
