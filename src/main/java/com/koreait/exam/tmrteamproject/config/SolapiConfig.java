package com.koreait.exam.tmrteamproject.config;

import net.nurigo.sdk.NurigoApp;
import net.nurigo.sdk.message.service.DefaultMessageService;
import net.nurigo.sdk.message.service.MessageService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;


@Configuration
public class SolapiConfig {

    @Value("${solapi.apiKey}")
    private String apiKey;

    @Value("${solapi.apiSecret}")
    private String apiSecret;

    @Bean
    public DefaultMessageService messageService() {
        return NurigoApp.INSTANCE.initialize(apiKey, apiSecret, "https://api.solapi.com");
    }
}