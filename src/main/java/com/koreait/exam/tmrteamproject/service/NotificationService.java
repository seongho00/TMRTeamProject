package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.vo.DueAlert;
import lombok.RequiredArgsConstructor;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class NotificationService {

    private final SimpMessagingTemplate template;

    // memberId 기준으로 보냄
    public void notifyMember(Long memberId, DueAlert dueAlert) {
        String dest = "/topic/member/" + memberId;
        template.convertAndSend(dest, dueAlert);
    }
}
