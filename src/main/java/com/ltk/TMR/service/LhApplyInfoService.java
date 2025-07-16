// com.ltk.TMR.service.LhApplyInfoService
package com.ltk.TMR.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.*;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.fasterxml.jackson.datatype.jsr310.deser.LocalDateDeserializer;
import com.ltk.TMR.entity.LhApplyInfo;
import com.ltk.TMR.repository.LhApplyInfoRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.nio.file.Path;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.ResolverStyle;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

@Slf4j
@RequiredArgsConstructor
@Service
public class LhApplyInfoService {

    private final LhApplyInfoRepository repo;

    /* yyyy-MM-dd, yyyy.MM.dd 모두 허용 */
    private static final DateTimeFormatter FLEXIBLE =
            DateTimeFormatter.ofPattern("uuuu[-MM[-dd]][.MM[.dd]]")
                    .withResolverStyle(ResolverStyle.STRICT);

    private final ObjectMapper mapper = new ObjectMapper()
            /* Java 8 Time 지원 */
            .registerModule(new JavaTimeModule()
                    .addDeserializer(
                            LocalDate.class,
                            new LocalDateDeserializer(FLEXIBLE)))
            /* JSON 필드 초과 허용 */
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false)
            /* timestamp ↔ 문자열 변환 */
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS)
            .disable(DeserializationFeature.ADJUST_DATES_TO_CONTEXT_TIME_ZONE);

    /* JSON 파일 경로 */
    @Value("${crawler.json-path:python_LH_crawler/data/lh_data.json}")
    private String jsonPath;

    private final AtomicBoolean loading = new AtomicBoolean(false);
    public boolean isLoading() { return loading.get(); }

    /* 수동 호출 */
    @Async @Transactional
    public void refreshFromCrawler() {
        if (loading.compareAndSet(false, true)) {
            try { saveFromJson(Path.of(jsonPath)); }
            finally { loading.set(false); }
        }
    }

    /* JSON → DB 저장 */
    void saveFromJson(Path json) {
        try {
            List<LhApplyInfo> list = mapper.readValue(
                    json.toFile(), new TypeReference<>(){});
            list.forEach(this::upsert);
            log.info("[LH] {}건 적재/업데이트 완료", list.size());
        } catch (Exception e) {
            throw new RuntimeException("[LhApplyInfoService] JSON 처리 실패", e);
        }
    }

    /* siteNo 우선, 없으면 (title+postDate) 로 upsert */
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

    /* 화면 조회 */
    public List<LhApplyInfo> findAllDesc() {
        return repo.findAllByOrderBySiteNoDesc();
    }
}
