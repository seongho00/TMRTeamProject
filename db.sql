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
