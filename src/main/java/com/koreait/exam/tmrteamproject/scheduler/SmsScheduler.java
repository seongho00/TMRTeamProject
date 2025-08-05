package com.koreait.exam.tmrteamproject.scheduler;

import com.koreait.exam.tmrteamproject.service.SolapiSmsService;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDate;

@Component
@RequiredArgsConstructor
public class SmsScheduler {

    private final SolapiSmsService smsService;

    @Scheduled(cron = "0 0 9 * * *") // 매일 오전 9시
    public void checkAndSendSms() {
        LocalDate today = LocalDate.now();

        // 예: 2025-07-15이면 발송
        if (today.equals(LocalDate.of(2025, 7, 15))) {
            smsService.sendSms("01022087215", "오늘은 문자 보낼 날입니다!");
        }

        // 또는 DB에서 조건 조회 후 문자 발송도 가능
    }
}
