package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.vo.FlaskResult;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import org.json.JSONObject;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import javax.xml.transform.Result;


@Service
public class ChatBotService {

    private final RestTemplate restTemplate = new RestTemplate();

    public ResultData analyzeMessage(String message) {
        String flaskUrl = "http://localhost:5000/predict?text=" + message;

        try {
            String response = restTemplate.getForObject(flaskUrl, String.class);
            JSONObject json = new JSONObject(response);

            // ✅ 전체 파싱해서 원하는 항목 꺼내기
            String intent = json.getString("intent");
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
}
