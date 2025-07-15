package com.koreait.exam.tmrteamproject.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.client.RestTemplate;
import org.json.JSONObject;

@Controller
@RequestMapping("usr/chatbot")
@Slf4j
@RequiredArgsConstructor
public class ChatbotController {

    private final RestTemplate restTemplate = new RestTemplate();

    @GetMapping("/chat")
    public String chat() {
        return "chatbot/chat";
    }

    @PostMapping("/sendMessage")
    @ResponseBody
    public String sendMessage(String message) {
        System.out.println(message);
        String flaskUrl = "http://localhost:5000/predict?text=" + message;

        try {
            String response = restTemplate.getForObject(flaskUrl, String.class);
            JSONObject json = new JSONObject(response);
            return json.getString("message"); // ✅ 응답 메시지만 꺼내서 리턴
        } catch (Exception e) {
            e.printStackTrace();
            return "❌ Flask 서버 연결 실패";
        }

    }
}
