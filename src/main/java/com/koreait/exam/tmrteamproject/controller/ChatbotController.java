package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.ChatBotService;
import com.koreait.exam.tmrteamproject.service.KakaoOAuthService;
import com.koreait.exam.tmrteamproject.vo.FlaskResult;
import com.koreait.exam.tmrteamproject.vo.PopulationSummary;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.util.ResourceUtils;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.client.RestTemplate;

@Controller
@RequestMapping("usr/chatbot")
@Slf4j
@RequiredArgsConstructor
public class ChatbotController {


    @Autowired
    private ChatBotService chatBotService;

    @GetMapping("/chat")
    public String chat() {
        return "chatbot/chat";
    }

    @PostMapping("/sendMessage")
    @ResponseBody
    public ResultData sendMessage(String message) {

        ResultData result = chatBotService.analyzeMessage(message);

        if (result.isFail()) {
            return ResultData.from("F-1", result.getMsg());  // "❌ Flask 서버 연결 실패"
        }
        FlaskResult flaskResult = (FlaskResult) result.getData1();

        String intent = flaskResult.getIntent();

        if (flaskResult.getSido() == null && flaskResult.getSigungu() == null && flaskResult.getEmd() == null) {
            return ResultData.from("F-2", "지역을 입력하지 않으셨어요. 예: '대전 유성구 궁동' 처럼 말해 주세요.");
        }


        switch (intent) {
            case "0":
                // 매출 관련 조회 로직
                System.out.println("매출 분석 요청");
                break;

            case "1":
                // 지역 분류
                PopulationSummary populationSummary = chatBotService.getPopulationSummary(flaskResult);

                // 지역 검색

                flaskResult = chatBotService.setFlaskResult(flaskResult);
                System.out.println("유동인구 조회 요청");

                return ResultData.from("S-2", "유동인구 데이터 출력", "유동인구", populationSummary, "flaskResult", flaskResult);

            case "2":
                // 상권 위험도 예측 로직
                System.out.println("위험도 예측 요청");
                break;

            case "3":
                // 청약 관련 로직
                System.out.println("청약 조회 요청");
                break;

            default:
                // 알 수 없는 intent
                System.out.println("알 수 없는 요청");
                break;
        }


        return ResultData.from("F-1", "데이터 요청 실패");
    }
}
