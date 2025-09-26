package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.vo.CommercialData;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@Slf4j
public class CommercialDataService {
    private List<CommercialData> csvData;

    public CommercialData getFirstRow() {
        return csvData.get(0); // 예제용: 첫 행 반환
    }

    public CommercialData findByEmdCode(String emdCode) {
        return csvData.stream()
                .filter(row -> row.getEmdCode().equals(emdCode))
                .findFirst()
                .orElse(null);
    }
}
