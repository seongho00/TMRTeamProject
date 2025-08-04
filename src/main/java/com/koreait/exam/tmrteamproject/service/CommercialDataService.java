package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.vo.CommercialData;
import com.opencsv.bean.CsvToBeanBuilder;
import org.springframework.stereotype.Service;

import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.util.List;

@Service
public class CommercialDataService {
    private List<CommercialData> csvData;

    public CommercialDataService() {
        try {
            csvData = new CsvToBeanBuilder<CommercialData>(
                    new InputStreamReader(
                            new FileInputStream("C:\\Users\\admin\\Desktop\\업종별_전처리결과\\CS100001_한식음식점.csv"), "UTF-8"))
                    .withType(CommercialData.class)
                    .withIgnoreLeadingWhiteSpace(true)
                    .build()
                    .parse();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

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
