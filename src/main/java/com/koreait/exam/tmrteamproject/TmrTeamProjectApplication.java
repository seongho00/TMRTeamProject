package com.koreait.exam.tmrteamproject;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.web.bind.annotation.CrossOrigin;

@EnableScheduling
@SpringBootApplication
@EnableJpaAuditing
public class TmrTeamProjectApplication {

    public static void main(String[] args) {
        SpringApplication.run(TmrTeamProjectApplication.class, args);
    }

}
