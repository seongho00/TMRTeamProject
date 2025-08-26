package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.AdminDongRepository;
import com.koreait.exam.tmrteamproject.repository.PopulationStatRepository;
import com.koreait.exam.tmrteamproject.repository.RiskScoreRepository;
import com.koreait.exam.tmrteamproject.vo.FlaskResult;
import com.koreait.exam.tmrteamproject.vo.PopulationSummary;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import com.koreait.exam.tmrteamproject.vo.RiskScore;
import lombok.RequiredArgsConstructor;
import org.json.JSONObject;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class RiskScoreService {

    private final RestTemplate restTemplate = new RestTemplate();
    private final PopulationStatRepository populationStatRepository;
    private final AdminDongRepository adminDongRepository;
    private final RiskScoreRepository riskScoreRepository;



    public RiskScore findAllByEmdCd(String emdCd) {
        return riskScoreRepository.findAllByEmdCd(emdCd);
    }
}
