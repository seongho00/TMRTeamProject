package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.*;
import com.koreait.exam.tmrteamproject.vo.*;
import com.koreait.exam.tmrteamproject.vo.FlaskResult;
import com.koreait.exam.tmrteamproject.vo.PopulationSummary;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.List;

@Controller
@RequestMapping("usr/chatbot")
@Slf4j
@RequiredArgsConstructor
public class ChatbotController {

    @Autowired
    private ChatBotService chatBotService;
    @Autowired
    private AdminDongService adminDongService;
    @Autowired
    private RiskScoreService riskScoreService;
    @Autowired
    private UpjongCodeService upjongCodeService;

    @GetMapping("/chat")
    public String chat() {
        return "chatbot/chat";
    }

    @PostMapping("/sendMessage")
    @ResponseBody
    public ResultData sendMessage(String message) {
        // 메세지 분석 로직
        System.out.println(message);
        ResultData result = chatBotService.analyzeMessage(message);

        if (result.isFail()) {
            return ResultData.from("F-1", result.getMsg());  // "Flask 서버 연결 실패"
        }

        FlaskResult flaskResult = (FlaskResult) result.getData1();

        int intent = flaskResult.getIntent();

        if (flaskResult.getSido() == null && flaskResult.getSigungu() == null && flaskResult.getEmd() == null) {
            return ResultData.from("F-2", "지역을 입력하지 않으셨어요. 예: '서울 종로구 사직동' 처럼 말해 주세요.");
        }
        // 행정동만 입력 시 여러 개인지 검색
        if (flaskResult.getSigungu().isEmpty() && flaskResult.getEmd() != null) {
            List<AdminDong> adminDongs = adminDongService.getAdminDongsByEmdNm(flaskResult.getEmd());
            if (adminDongs.size() >= 2) {
                return ResultData.from("F-3", "동 이름이 여러 구에 있어요. 정확한 위치를 선택하세요.", "adminDong 데이터", adminDongs);
            }
        }

        // 서울만 하니까 서울로 고정
        flaskResult.setSido("서울특별시");
        // 행정동 적었으면 행정동 코드 가져오기
        String emdCd = "";
        if (flaskResult.getEmd() != null) {
            AdminDong adminDong = adminDongService.findAdminDongBySggNmAndEmdNm(flaskResult.getSigungu(), flaskResult.getEmd());
            emdCd = adminDong.getEmdCd();
        }

        switch (intent) {
            case 0:
                // 매출 관련 조회 로직

                System.out.println("매출 분석 요청");

                if (flaskResult.getUpjong_nm() == null) {
                    return ResultData.from("F-4", "어떤 업종의 매출을 알고 싶으신가요?");
                }
                // DB에 넣어놔야하긴 해 + 과거 데이터도 넣을건가?
                if (!emdCd.isEmpty()) {
                    chatBotService.getSalesData(emdCd, flaskResult.getUpjong_nm());
                }

                return ResultData.from("S-1", "매출액 데이터 출력", "flaskResult", flaskResult);


            case 1:
                // 지역 분류
                System.out.println(flaskResult);
                PopulationSummary populationSummary = chatBotService.getPopulationSummary(flaskResult);

                // 지역 검색

                System.out.println("유동인구 조회 요청");

                return ResultData.from("S-2", "유동인구 데이터 출력", "flaskResult", flaskResult, "유동인구", populationSummary);

            case 2:
                // 상권 위험도 예측 로직
                RiskScore riskScore = riskScoreService.findAllByEmdCd(emdCd);

                System.out.println("위험도 예측 요청");
                break;

            case 3:
                // 청약 관련 로직
                System.out.println("청약 조회 요청");

                chatBotService.getLhSupplySchedule();


                return ResultData.from("S-4", "청약 데이터 출력", "flaskResult", flaskResult);

        }

        return ResultData.from("F-A", "데이터 요청 실패");
    }


}
