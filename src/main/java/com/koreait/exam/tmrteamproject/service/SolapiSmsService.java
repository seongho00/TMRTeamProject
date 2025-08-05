package com.koreait.exam.tmrteamproject.service;

import net.nurigo.sdk.message.model.Message;
import net.nurigo.sdk.message.request.SingleMessageSendingRequest;
import net.nurigo.sdk.message.response.SingleMessageSentResponse;
import net.nurigo.sdk.message.service.DefaultMessageService;
import org.springframework.stereotype.Service;

@Service
public class SolapiSmsService {

    private final DefaultMessageService messageService;

    public SolapiSmsService(DefaultMessageService messageService) {
        this.messageService = messageService;
    }

    public SingleMessageSentResponse sendSms(String to, String text) {
        Message message = new Message();
        message.setFrom("01030417745"); // 발신번호
        message.setTo(to);
        message.setText(text);

        return messageService.sendOne(new SingleMessageSendingRequest(message));
    }
}
