package com.ltk.TMR.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.ltk.TMR.entity.LhApplyInfo;
import com.ltk.TMR.repository.LhApplyInfoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;


@Slf4j
@RequiredArgsConstructor
@Service
@Transactional(readOnly = true)
public class LhApplyInfoService {

    private final LhApplyInfoRepository repo;
    private final AtomicBoolean loading = new AtomicBoolean(false);

    private final ObjectMapper mapper = new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .setDateFormat(new SimpleDateFormat("yyyy-MM-dd"))
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

    @Value("${crawler.json-path:python_LH_crawler/data/lh_data.json}")
    private String jsonPath;

    public boolean isLoading() { return loading.get(); }

    @Async
    @Transactional
    public void refreshFromCrawler() {
        if (loading.compareAndSet(false, true)) {
            try {
                // Map 형태로 리딩 후 attachments 별도 처리
                List<Map<String, Object>> rawDataList = mapper.readValue(
                        new File(jsonPath),
                        new TypeReference<>() {}
                );
                log.info("[LH] {}건의 크롤링 데이터를 읽었습니다.", rawDataList.size());

                for (Map<String, Object> rawData : rawDataList) {
                    LhApplyInfo newInfo = mapper.convertValue(rawData, LhApplyInfo.class);

                    // attachments 리스트를 JSON 문자열 변환 후 저장
                    if (rawData.get("attachments") != null) {
                        String attachmentsJson = mapper.writeValueAsString(rawData.get("attachments"));
                        newInfo.setAttachmentsJson(attachmentsJson);
                    }

                    upsert(newInfo);
                }
                log.info("[LH] {}건 적재/업데이트 완료", rawDataList.size());

            } catch (IOException e) {
                log.error("JSON 파일 읽기 또는 처리 중 에러", e);
            } finally {
                loading.set(false);
            }
        }
    }

    private void upsert(LhApplyInfo dto) {
        if (dto.getSiteNo() == null) {
            log.warn("[LH] siteNo 없음 → SKIP : {}", dto.getTitle());
            return;
        }
        repo.findBySiteNo(dto.getSiteNo())
                .ifPresentOrElse(found -> {
                    found.updateFrom(dto);
                    repo.save(found);
                }, () -> repo.save(dto));
    }

    public List<LhApplyInfo> findAllDesc() {
        List<LhApplyInfo> resultList = repo.findAllByOrderBySiteNoDesc();

        // JSON 문자열을 DTO 리스트로 변환
        resultList.forEach(item -> {
            if (item.getAttachmentsJson() != null && !item.getAttachmentsJson().isEmpty()) {
                try {
                    List<LhApplyInfo.AttachmentDto> attachments = mapper.readValue(
                            item.getAttachmentsJson(),
                            new TypeReference<>() {}
                    );
                    item.setAttachments(attachments);
                } catch (JsonProcessingException e) {
                    log.error("Failed to parse attachments JSON for siteNo: {}", item.getSiteNo(), e);
                    item.setAttachments(Collections.emptyList());
                }
            } else {
                item.setAttachments(Collections.emptyList());
            }
        });

        return resultList;
    }
}