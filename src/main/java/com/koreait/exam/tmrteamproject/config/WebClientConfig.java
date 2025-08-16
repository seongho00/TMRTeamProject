package com.koreait.exam.tmrteamproject.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

@Configuration
public class WebClientConfig {
    @Bean
    public WebClient pythonClient(WebClient.Builder builder) {
        return builder.baseUrl("http://localhost:5000").build(); // FastAPI 주소
    }
}