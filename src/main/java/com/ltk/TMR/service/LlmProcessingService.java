package com.ltk.TMR.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ltk.TMR.entity.LhApplyInfo;
import com.ltk.TMR.entity.LhProcessingStatus;
import com.ltk.TMR.entity.LhShopDetail;
import com.ltk.TMR.repository.LhApplyInfoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class LlmProcessingService {

    private final LhApplyInfoRepository lhRepository;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${google.cloud.api.key}")
    private String apiKey;
    @Value("${google.cloud.project.id}")
    private String projectId;

    @Async
    @Transactional
    public void processAndSaveDetails(LhApplyInfo lhInfo) {
        lhInfo.setProcessingStatus(LhProcessingStatus.PROCESSING);
        lhRepository.save(lhInfo);
        log.info("  > LLM 처리 시작 (siteNo: {})", lhInfo.getSiteNo());

        try {
            String prompt = createPrompt(lhInfo.getMarkdownText());
            String requestBody = buildRequestBodyWithParams(prompt);
            String url = String.format("https://us-central1-aiplatform.googleapis.com/v1/projects/%s/locations/us-central1/publishers/google/models/gemini-2.5-flash:generateContent?key=%s", projectId, apiKey);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<String> entity = new HttpEntity<>(requestBody, headers);

            String jsonResponse = restTemplate.postForObject(url, entity, String.class);

            List<LhShopDetail> details = parseResponseAndCreateDetails(jsonResponse);

            if (!details.isEmpty()) {
                details.forEach(detail -> detail.setLhApplyInfo(lhInfo));
                lhInfo.getDetails().clear();
                lhInfo.getDetails().addAll(details);
                lhInfo.setProcessingStatus(LhProcessingStatus.COMPLETED);
            } else {
                lhInfo.setProcessingStatus(LhProcessingStatus.FAILED);
            }

        } catch (Exception e) {
            log.error("  > LLM 처리 실패 (siteNo: {}): {}", lhInfo.getSiteNo(), e.getMessage());
            lhInfo.setProcessingStatus(LhProcessingStatus.FAILED);
        }
        lhRepository.save(lhInfo);
    }

    private String createPrompt(String markdownText) {
        return "당신은 부동산 공고문 분석 전문가입니다. 다음 마크다운 텍스트는 LH 상가 공고문의 일부입니다. " +
                "이 텍스트에서 공급되는 각 상가 호수별로 상세 정보를 추출하여 JSON 배열 형태로 반환해주세요. " +
                "키는 'dong', 'ho', 'floor', 'shopUsage', 'areaExclusive', 'deposit', 'rentMonthly'를 사용하고, " +
                "숫자 값에서 콤마(,)는 모두 제거해주세요. 해당하는 정보가 없으면 null로 처리하세요. " +
                "불필요한 설명 없이 순수한 JSON 배열만 응답하세요.\\n\\n" +
                "--- 마크다운 텍스트 시작 ---\\n" +
                markdownText +
                "\\n--- 마크다운 텍스트 끝 ---";
    }

    private String buildRequestBodyWithParams(String prompt) {
        String escapedPrompt = prompt.replace("\"", "\\\"").replace("\n", "\\n");
        String jsonPayload = """
        {
          "contents": [{"parts": [{"text": "%s"}]}],
          "generationConfig": { "temperature": 0.2, "maxOutputTokens": 4096 }
        }
        """;
        return String.format(jsonPayload, escapedPrompt);
    }

    private List<LhShopDetail> parseResponseAndCreateDetails(String jsonResponse) {
        try {
            Map<String, Object> responseMap = objectMapper.readValue(jsonResponse, new TypeReference<>() {});
            List<Map<String, Object>> candidates = (List<Map<String, Object>>) responseMap.get("candidates");
            Map<String, Object> content = (Map<String, Object>) candidates.get(0).get("content");
            List<Map<String, Object>> parts = (List<Map<String, Object>>) content.get("parts");
            String text = (String) parts.get(0).get("text");

            String pureJson = text.replace("```json", "").replace("```", "").trim();

            List<Map<String, Object>> rawDetails = objectMapper.readValue(pureJson, new TypeReference<>() {});
            return rawDetails.stream().map(raw -> {
                LhShopDetail detail = new LhShopDetail();
                detail.setDong(String.valueOf(raw.getOrDefault("dong", "")));
                detail.setHo(String.valueOf(raw.getOrDefault("ho", "")));
                detail.setFloor(String.valueOf(raw.getOrDefault("floor", "")));
                detail.setShopUsage(String.valueOf(raw.getOrDefault("shopUsage", "")));
                try {
                    detail.setAreaExclusive(Double.parseDouble(String.valueOf(raw.get("areaExclusive"))));
                } catch (Exception e) { /* ignore */ }
                try {
                    detail.setDeposit(Long.parseLong(String.valueOf(raw.get("deposit"))));
                } catch (Exception e) { /* ignore */ }
                try {
                    detail.setRentMonthly(Long.parseLong(String.valueOf(raw.get("rentMonthly"))));
                } catch (Exception e) { /* ignore */ }
                return detail;
            }).collect(Collectors.toList());
        } catch (Exception e) {
            log.error("LLM 응답 JSON 파싱 실패", e);
            return Collections.emptyList();
        }
    }
}