package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.AdminDongRepository;
import com.koreait.exam.tmrteamproject.repository.MemberRepository;
import com.koreait.exam.tmrteamproject.repository.PopulationStatRepository;
import com.koreait.exam.tmrteamproject.vo.*;
import lombok.RequiredArgsConstructor;
import org.json.JSONObject;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import javax.xml.transform.Result;
import java.util.Collections;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ChatBotService {

    private final RestTemplate restTemplate = new RestTemplate();
    private final PopulationStatRepository populationStatRepository;
    private final AdminDongRepository adminDongRepository;


    public ResultData analyzeMessage(String message) {
        String flaskUrl = "http://localhost:5000/predict?text=" + message;

        try {
            String response = restTemplate.getForObject(flaskUrl, String.class);
            JSONObject json = new JSONObject(response);

            // ✅ 전체 파싱해서 원하는 항목 꺼내기
            int intent = json.getInt("intent");
            double confidence = json.getDouble("confidence");
            String sido = json.optString("sido");
            String sigungu = json.optString("sigungu");
            String emd = json.optString("emd_nm");
            String gender = json.optString("gender");
            String ageGroup = json.optString("age_group");
            String messageText = json.optString("message");


            FlaskResult flaskResult = FlaskResult.builder()
                    .intent(intent)
                    .confidence(confidence)
                    .sido(sido)
                    .sigungu(sigungu)
                    .emd(emd)
                    .gender(gender)
                    .ageGroup(ageGroup)
                    .message(messageText)
                    .build();

            // ✅ 디버깅용 로그
            System.out.println("intent: " + intent + ", confidence: " + confidence);
            System.out.println("sido: " + sido + ", sigungu: " + sigungu + ", emd: " + emd);
            System.out.println("성별: " + gender + ", 연령대: " + ageGroup);

            return ResultData.from("S-1", "Flask 서버 연결 성공", "flaskResult", flaskResult);  // 또는 가공해서 리턴해도 OK
        } catch (Exception e) {
            e.printStackTrace();
            return ResultData.from("F-1", "❌ Flask 서버 연결 실패");
        }
    }

    public PopulationSummary getPopulationSummary(FlaskResult flaskResult) {

        String sido = flaskResult.getSido();
        String sigungu = flaskResult.getSigungu();
        String emd = flaskResult.getEmd();

        if (sido.equals("서울")) {
            sido = "서울특별시";
        }

        System.out.println("sido: " + sido);
        System.out.println("sigungu: " + sigungu);
        System.out.println("emd: " + emd);


        // 지역 관련
        if (!sido.equals("None") && !sigungu.equals("None") && !emd.equals("None")) {
            // "대전 동구 효동"
            return populationStatRepository.findBySidoAndSigunguAndEmd(sido, sigungu, emd);
        } else if (!sido.equals("None") && !sigungu.equals("None")) {
            // "대전 동구"
            return populationStatRepository.findBySidoAndSigungu(sido, sigungu);
        } else if (!sido.equals("None") && !emd.equals("None")) {
            // "대전 효동"
            return populationStatRepository.findBySidoAndEmd(sido, emd).get(0);
        } else if (!sigungu.equals("None") && !emd.equals("None")) {
            // "동구 효동"
            return populationStatRepository.findBySigunguAndEmd(sigungu, emd);
        } else if (!sido.equals("None")) {
            // "대전"
            return populationStatRepository.findBySido(sido);
        } else if (!sigungu.equals("None")) {
            // "동구"
            return populationStatRepository.findBySigungu(sigungu);
        } else if (!emd.equals("None")) {
            // "효동"
            return populationStatRepository.findByEmd(emd).get(0);
        }

        return null;
    }


    public FlaskResult setFlaskResult(FlaskResult flaskResult) {
        String sigungu = flaskResult.getSigungu();
        String emd = flaskResult.getEmd();

        if (!sigungu.equals("None")) {
            flaskResult.setSido("대전광역시");
        }

        if (!emd.equals("None")) {
            AdminDong adminDong = adminDongRepository.findRegionByEmdNm(emd);
            flaskResult.setSido(adminDong.getSidoNm());
            flaskResult.setSigungu(adminDong.getSggNm());
            flaskResult.setEmd(adminDong.getEmdNm());
        }

        return flaskResult;
    }
}
