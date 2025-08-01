package com.ltk.TMR.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.io.InputStream;
import java.net.URL;
import java.util.Base64;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class GeminiPdfAnalysisService {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${google.cloud.api.key}")
    private String apiKey;
    @Value("${google.cloud.project.id}")
    private String projectId;

    // 모델명을 쉽게 교체할 수 있도록 프로퍼티로 분리하는 것을 추천합니다.
    @Value("${google.gemini.model:gemini-1.5-pro-latest}")
    private String modelName;

    public String generateMarkdownFromPdf(String pdfUrl) {
        log.info("  > Analyzing PDF with Gemini from URL: {}", pdfUrl);
        try {
            // 1. URL에서 PDF 파일을 바이트 배열로 다운로드
            byte[] pdfBytes;
            try (InputStream is = new URL(pdfUrl).openStream()) {
                pdfBytes = is.readAllBytes();
            }

            // 2. PDF 바이트를 Base64로 인코딩
            String base64Pdf = Base64.getEncoder().encodeToString(pdfBytes);

            // 3. Gemini API에 보낼 요청 본문 생성
            String requestBody = buildRequestBody(base64Pdf);
            String url = String.format("https://us-central1-aiplatform.googleapis.com/v1/projects/%s/locations/us-central1/publishers/google/models/%s:generateContent?key=%s", projectId, modelName, apiKey);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<String> entity = new HttpEntity<>(requestBody, headers);

            // 4. API 호출
            String jsonResponse = restTemplate.postForObject(url, entity, String.class);

            // 5. API 응답에서 마크다운 텍스트 추출
            return parseResponse(jsonResponse);

        } catch (Exception e) {
            log.error("  > Failed to analyze PDF with Gemini [{}]: {}", pdfUrl, e.getMessage());
            return "ERROR: Gemini PDF analysis failed. Reason: " + e.getMessage();
        }
    }

    private String buildRequestBody(String base64Pdf) {
        String prompt = "이 PDF 파일은 LH 상가 공고문입니다. 전체 내용을 빠짐없이, 원본의 구조(제목, 목록, 표 등)를 최대한 살려서 정확한 마크다운 형식으로 변환해주세요. 불필요한 설명이나 인사말 없이, 변환된 마크다운 텍스트만 응답해야 합니다.";

        // JSON 문자열 생성을 위해 따옴표 등을 이스케이프 처리
        String escapedPrompt = prompt.replace("\"", "\\\"");

        String jsonPayload = """
        {
          "contents": [
            {
              "parts": [
                {"text": "%s"},
                {
                  "inline_data": {
                    "mime_type": "application/pdf",
                    "data": "%s"
                  }
                }
              ]
            }
          ],
          "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 8192
          }
        }
        """;
        return String.format(jsonPayload, escapedPrompt, base64Pdf);
    }

    private String parseResponse(String jsonResponse) {
        try {
            Map<String, Object> responseMap = objectMapper.readValue(jsonResponse, new TypeReference<>() {});
            List<Map<String, Object>> candidates = (List<Map<String, Object>>) responseMap.get("candidates");
            if (candidates == null || candidates.isEmpty()) {
                log.warn("Gemini response contains no candidates: {}", jsonResponse);
                return "ERROR: Gemini returned no candidates.";
            }
            Map<String, Object> content = (Map<String, Object>) candidates.get(0).get("content");
            List<Map<String, Object>> parts = (List<Map<String, Object>>) content.get("parts");
            return (String) parts.get(0).get("text");
        } catch (Exception e) {
            log.error("Failed to parse Gemini response JSON", e);
            return "ERROR: Failed to parse Gemini response.";
        }
    }
}