package com.koreait.exam.tmrteamproject.controller;


import com.koreait.exam.tmrteamproject.service.KakaoOAuthService;
import com.koreait.exam.tmrteamproject.service.NaverOAuthService;
import com.koreait.exam.tmrteamproject.service.SolapiSmsService;
import com.koreait.exam.tmrteamproject.vo.Rq;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.nurigo.sdk.NurigoApp;
import net.nurigo.sdk.message.model.Message;
import net.nurigo.sdk.message.request.SingleMessageSendingRequest;
import net.nurigo.sdk.message.response.SingleMessageSentResponse;
import net.nurigo.sdk.message.service.DefaultMessageService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

        import java.io.UnsupportedEncodingException;
import java.math.BigInteger;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;

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


