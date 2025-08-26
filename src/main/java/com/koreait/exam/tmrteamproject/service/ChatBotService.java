package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.AdminDongRepository;
import com.koreait.exam.tmrteamproject.repository.DataSaveRepository;
import com.koreait.exam.tmrteamproject.repository.PopulationStatRepository;
import com.koreait.exam.tmrteamproject.vo.*;
import lombok.RequiredArgsConstructor;
import org.json.JSONObject;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ChatBotService {

    private final RestTemplate restTemplate = new RestTemplate();
    private final PopulationStatRepository populationStatRepository;
    private final AdminDongRepository adminDongRepository;
    private final DataSaveRepository dataSaveRepository;


    public ResultData analyzeMessage(String message) {
        String flaskUrl = "http://localhost:5000/predict?text=" + message;

        try {
            String response = restTemplate.getForObject(flaskUrl, String.class);
            JSONObject json = new JSONObject(response);
            // ✅ 전체 파싱해서 원하는 항목 꺼내기
            int intent = json.getInt("intent");
            double confidence = json.getDouble("confidence");
            JSONObject entities = json.getJSONObject("entities");


            String sido = entities.optString("sido");
            String sigungu = entities.optString("sigungu");
            String emd = entities.optString("emd_nm");
            String gender = entities.optString("gender");
            String ageGroup = entities.optString("age_group");
            String messageText = entities.optString("message");


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
        return null;
    }


    public FlaskResult analyzeRegion(FlaskResult flaskResult) {
        return null;
    }

    public void getLhSupplySchedule() {
    }

    public void getSalesData(String emdCd, String upjongCd) {
        List<DataSet> dataSet = dataSaveRepository.findAllByAdminDongCodeAndServiceIndustryCode(emdCd, upjongCd);
        dataSet.get(0).getMonthlySalesAmount();
    }
}
