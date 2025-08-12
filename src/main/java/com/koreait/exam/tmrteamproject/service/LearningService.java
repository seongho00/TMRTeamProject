package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.LearningRepository;
import com.koreait.exam.tmrteamproject.vo.Learning;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class LearningService {

    @Autowired
    private LearningRepository learningRepository;

    public int setSaved(List<Learning> data) {
        List<Learning> entities = data.stream().map(d -> Learning.builder()
                .hjdCo(d.getHjdCo())
                .hjdCn(d.getHjdCn())
                .serviceTypeCode(d.getServiceTypeCode())
                .serviceTypeName(d.getServiceTypeName())
                .riskScore(d.getRiskScore())
                .riskLabel(d.getRiskLabel())
                .predictedRiskLabel(d.getPredictedRiskLabel())
                .riskLabel7(d.getRiskLabel7())
                .build()
        ).collect(Collectors.toList());
        learningRepository.saveAll(entities);
        return entities.size();
    }
}
