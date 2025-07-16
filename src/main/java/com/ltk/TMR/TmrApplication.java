package com.ltk.TMR;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync           // ← @Async 활성화
public class TmrApplication {

	public static void main(String[] args) {
		SpringApplication.run(TmrApplication.class, args);
	}
}
