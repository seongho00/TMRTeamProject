package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.SolapiSmsService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.nurigo.sdk.message.response.SingleMessageSentResponse;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("usr/sms")
@Slf4j
@RequiredArgsConstructor
public class SmsController {

    private final SolapiSmsService smsService;

    @GetMapping("/send-one")
    public SingleMessageSentResponse sendOne() {
        return smsService.sendSms("01030417745", "테스트 메시지입니다.123");
    }
}
