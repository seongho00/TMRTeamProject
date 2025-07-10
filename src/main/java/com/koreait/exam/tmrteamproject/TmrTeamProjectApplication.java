package com.koreait.exam.tmrteamproject;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@MapperScan("com.koreait.exam.tmrteamproject.repository")
@SpringBootApplication
public class TmrTeamProjectApplication {

    public static void main(String[] args) {
        SpringApplication.run(TmrTeamProjectApplication.class, args);
    }

}
