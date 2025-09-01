package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.entity.LhApplyInfo;
import com.koreait.exam.tmrteamproject.service.*;
import com.koreait.exam.tmrteamproject.service.AdminDongService;
import com.koreait.exam.tmrteamproject.service.ChatBotService;
import com.koreait.exam.tmrteamproject.service.LearningService;
import com.koreait.exam.tmrteamproject.vo.*;
import com.koreait.exam.tmrteamproject.vo.FlaskResult;
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
    private LearningService learningService;
    @Autowired
    private UpjongCodeService upjongCodeService;
    @Autowired
    private DataSetService dataSaveService;
    @Autowired
    private LhApplyInfoService lhApplyInfoService;


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

        String emdCd = null;

        if (intent != 3) {
            if (flaskResult.getEmd().isEmpty()) {
                return ResultData.from("F-2", "행정동을 입력하지 않으셨어요 정확한 분석을 위해 행정동을 입력해주세요. 예: '서울 종로구 사직동' 처럼 말해 주세요.");
            }

            if (flaskResult.getSigungu().isEmpty()) {
                List<AdminDong> adminDongs = adminDongService.getAdminDongsByEmdNm(flaskResult.getEmd());
                if (adminDongs.size() >= 2) {
                    return ResultData.from("F-3", "동 이름이 여러 구에 있어요. 정확한 위치를 선택하세요.", "adminDong 데이터", adminDongs);
                } else if (flaskResult.getSigungu().isEmpty()) {
                    AdminDong adminDong = adminDongService.getAdminDongsByEmdNm(flaskResult.getEmd()).get(0);
                    flaskResult.setSigungu(adminDong.getSggNm());
                }
            }
            // 서울만 하니까 서울로 고정
            flaskResult.setSido("서울특별시");
            // 행정동 코드 가져오기
            AdminDong adminDong = adminDongService.findAdminDongBySggNmAndEmdNm(flaskResult.getSigungu(), flaskResult.getEmd());
            emdCd = adminDong.getEmdCd();
        }

        UpjongCode upjongCode;

        switch (intent) {
            case 0:
                // 매출 관련 조회 로직
                System.out.println("매출 분석 요청");
                System.out.println(flaskResult);
                // 업종 종류 보여주기
                if (flaskResult.getUpjong_nm().isEmpty()) {
                    List<UpjongCode> upjongCodes = upjongCodeService.findAll();
                    return ResultData.from("F-4", "업종 선택 필요", "업종 종류", upjongCodes, "메세지 원본", message);
                }


                // 업종 이름을 통해 업종 데이터 가져오기
                upjongCode = upjongCodeService.findAllByUpjongNm(flaskResult.getUpjong_nm()).get(0);

                // 지역 및 업종을 통해 dataSet 가져오기
                List<DataSet> upjongDataSet = dataSaveService.findAllByEmdCdAndUpjongCodeGroupByAdminDongCode(emdCd, upjongCode.getUpjongCd());
                return ResultData.from("S-1", "매출액 데이터 출력", "flaskResult", flaskResult, "업종 데이터", upjongCode, "매출액 데이터", upjongDataSet);


            case 1:

                System.out.println("유동인구 조회 요청");

                // 해당 지역 data 가져오기
                DataSet dataSet = dataSaveService.findAllByAdminDongCodeAndBaseYearQuarterCodeGroupByAdminDongCode(emdCd);

                // 모든 지역 data 가져오기
                List<DataSet> AllDataSets;
                // 나이, 연령대 입력 없을 시
                if (!flaskResult.getGender().isEmpty() && flaskResult.getAgeGroup().isEmpty()) {
                    // 성별만 입력 시
                    if (flaskResult.getGender().equals("female")) {
                        AllDataSets = dataSaveService.findGroupedByAdminDongOrderByFemale();
                    } else {
                        AllDataSets = dataSaveService.findGroupedByAdminDongOrderByMale();
                    }
                } else if (flaskResult.getGender().isEmpty() && !flaskResult.getAgeGroup().isEmpty()) {
                    // 연령대만 입력 시
                    AllDataSets = dataSaveService.findGroupedByAdminDongOrderByAge(flaskResult.getAgeGroup());

                } else {
                    // 그 외
                    AllDataSets = dataSaveService.findGroupedByAdminDong();

                }

                // 현재 지역 상위 몇 프로인지 계산하기
                int total = AllDataSets.size();

                // 랭킹 찾기 (내림차순 정렬된 상태라 index+1 = 순위)
                int rank = 0;
                for (int i = 0; i < total; i++) {
                    if (AllDataSets.get(i).getAdminDongCode().equals(emdCd)) {
                        rank = i + 1;
                        break;
                    }
                }

                double percentile = (double) rank / total * 100;
                long rounded = Math.round(percentile);


                return ResultData.from("S-2", "유동인구 데이터 출력", "flaskResult", flaskResult, "유동인구", dataSet, "상위 계산", rounded);

            case 2:
                // 상권 위험도 예측 로직
                if (flaskResult.getUpjong_nm().isEmpty()) {
                    List<UpjongCode> upjongCodes = upjongCodeService.findAll();
                    return ResultData.from("F-4", "업종 선택 필요", "업종 종류", upjongCodes, "메세지 원본", message);
                }

                // 업종 이름을 통해 업종 데이터 가져오기
                upjongCode = upjongCodeService.findAllByUpjongNm(flaskResult.getUpjong_nm()).get(0);

                // 업종 종류 보여주기
                if (flaskResult.getUpjong_nm().isEmpty()) {
                    List<UpjongCode> upjongCodes = upjongCodeService.findAll();
                    return ResultData.from("F-4", "업종 선택 필요", "업종 종류", upjongCodes, "메세지 원본", message);
                }

                // 업종 이름을 통해 업종 데이터 가져오기
                upjongCode = upjongCodeService.findAllByUpjongNm(flaskResult.getUpjong_nm()).get(0);

                // 지역, 업종코드를 통해 위험도 데이터 가져오기
                List<Learning> riskDataSet = learningService.findAllByEmdCdAndUpjongCodeGroupByAdminDongCode(emdCd, upjongCode.getUpjongCd());

                System.out.println(riskDataSet);

                return ResultData.from("S-3", "위험도 데이터 출력", "flaskResult", flaskResult, "위험도 데이터", riskDataSet);

            case 3:
                // 청약 관련 로직
                System.out.println("청약 조회 요청");
                // 현재 공급중인 청약 데이터 가져오기
                List<LhApplyInfo> lhApplyInfos = lhApplyInfoService.findAllByStatus();


                return ResultData.from("S-4", "청약 데이터 출력", "flaskResult", flaskResult, "청약 데이터", lhApplyInfos);

        }

        return ResultData.from("F-A", "데이터 요청 실패");
    }
}
