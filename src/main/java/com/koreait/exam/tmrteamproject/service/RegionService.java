package com.koreait.exam.tmrteamproject.service;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.util.ResourceUtils;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

@Service
public class RegionService {

    private final Map<String, Map<String, List<Dong>>> regionData;

    public RegionService() throws IOException {
        this.regionData = new TreeMap<>();

        // 10자리 코드가 포함된 CSV파일 리딩 (파일 이름 수정)
        BufferedReader reader = new BufferedReader(new FileReader(ResourceUtils.getFile("classpath:hangjeongdong_code_final.csv")));

        String line;
        reader.readLine(); // 헤더 건너뛰기

        while ((line = reader.readLine()) != null) {
            String[] parts = line.split(",");
            if (parts.length < 4) continue;

            String sido = parts[0];
            String sigungu = parts[1];
            String dongName = parts[2];
            String dongCode = parts[3];

            regionData.computeIfAbsent(sido, k -> new TreeMap<>());
            regionData.get(sido).computeIfAbsent(sigungu, k -> new ArrayList<>());
            // 동을 생성하여 이름, 코드 저장
            regionData.get(sido).get(sigungu).add(new Dong(dongName, dongCode));
        }
        reader.close();
    }

    // 지역 데이터 반환
    public Map<String, Map<String, List<Dong>>> getRegionData() {
        return this.regionData;
    }

    // 동 이름, 코드를 클래스로
    @Getter
    @RequiredArgsConstructor
    public static class Dong {
        private final String name;
        private final String code;
    }
}
