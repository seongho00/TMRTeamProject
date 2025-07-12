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



CREATE TABLE areaCode (
                          id INT(10) AUTO_INCREMENT PRIMARY KEY,
                          regDate DATETIME NOT NULL,
                          updateDate DATETIME NOT NULL,
                          sidoCode CHAR(10) NOT NULL,
                          sidoName CHAR(20) NOT NULL,
                          sigunguCode CHAR(10) NOT NULL,
                          sigunguName CHAR(20) NOT NULL,
                          admDongCode CHAR(10) NOT NULL,
                          admDongName CHAR(20) NOT NULL,
                          fullCode CHAR(100) NOT NULL,
                          fullName CHAR(100) NOT NULL
);


SELECT * FROM `member`

