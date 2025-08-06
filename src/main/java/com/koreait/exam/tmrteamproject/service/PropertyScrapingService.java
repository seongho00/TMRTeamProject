package com.koreait.exam.tmrteamproject.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.koreait.exam.tmrteamproject.vo.PropertyListingDto;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

@Service
public class PropertyScrapingService {

    public List<PropertyListingDto> getProperties(String dongCode) {
        String pythonScriptPath = "C:/Users/tk758/Desktop/TMR/naver_crawler/naver_property_scraper.py";
        String pythonExecutable = "python";

        ProcessBuilder processBuilder = new ProcessBuilder(pythonExecutable, pythonScriptPath, dongCode);

        processBuilder.environment().put("PYTHONIOENCODING", "UTF-8");

        processBuilder.redirectErrorStream(true);

        try {
            Process process = processBuilder.start();

            StringBuilder output = new StringBuilder();
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), "UTF-8"));

            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line);
            }

            int exitCode = process.waitFor();
            if (exitCode != 0) {
                System.out.println("Python script exited with error code: " + exitCode);
                return new ArrayList<>();
            }

            ObjectMapper objectMapper = new ObjectMapper();
            return objectMapper.readValue(output.toString(), new TypeReference<List<PropertyListingDto>>() {});

        } catch (Exception e) {
            System.out.println("Python 스크립트 실행 중 오류 발생: " + e.getMessage());
            return new ArrayList<>();
        }
    }
}