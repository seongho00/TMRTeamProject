package com.ltk.TMR.service;

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
import java.util.List;
import java.util.Map;
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
                // JSON 리딩 방식을 Map에서 LhApplyInfo 리스트로 변경
                List<LhApplyInfo> crawledList = mapper.readValue(
                        new File(jsonPath),
                        new TypeReference<>() {}
                );
                log.info("[LH] {}건의 크롤링 데이터를 읽었습니다.", crawledList.size());

                for (LhApplyInfo newInfo : crawledList) {
                    upsert(newInfo); // attachments가 자동으로 매핑된 newInfo를 바로 사용
                }
                log.info("[LH] {}건 적재/업데이트 완료", crawledList.size());

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
                }, () -> repo.save(dto));
    }

    public List<LhApplyInfo> findAllDesc() {
        return repo.findAllByOrderBySiteNoDesc();
    }

    public LhApplyInfo findById(Long id) {
        LhApplyInfo item = repo.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Invalid item Id:" + id));
        return item;
    }
}