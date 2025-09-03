package com.koreait.exam.tmrteamproject.service;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.koreait.exam.tmrteamproject.vo.LhApplyInfo;
import com.koreait.exam.tmrteamproject.repository.LhApplyInfoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.text.SimpleDateFormat;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

@Slf4j
@RequiredArgsConstructor
@Service
@Transactional(readOnly = true)
public class LhApplyInfoService {

    private final LhApplyInfoRepository lhApplyInfoRepository;
    private final AtomicBoolean loading = new AtomicBoolean(false);

    private final ObjectMapper mapper = new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .setDateFormat(new SimpleDateFormat("yyyy-MM-dd"))
            .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

    @Transactional
    public void refreshFromCrawler() {
        if (loading.compareAndSet(false, true)) {
            try {
                Path json = Paths.get( "TMRTeamProjectPython", "python_LH_crawler", "data", "lh_data.json")
                        .normalize().toAbsolutePath();
                log.info("[LH] user.dir={} / json={}", System.getProperty("user.dir"), json);
                List<LhApplyInfo> crawledList = mapper.readValue(
                        json.toFile(),
                        new com.fasterxml.jackson.core.type.TypeReference<List<LhApplyInfo>>() {}
                );
                log.info("[LH] {}건의 크롤링 데이터를 읽었습니다.", crawledList.size());
                for (LhApplyInfo newInfo : crawledList) {
                    upsert(newInfo);
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
        lhApplyInfoRepository.findBySiteNo(dto.getSiteNo())
                .ifPresentOrElse(found -> {
                    found.updateFrom(dto);
                }, () -> lhApplyInfoRepository.save(dto));
    }

    public LhApplyInfo findById(Long id) {
        return lhApplyInfoRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Invalid item Id:" + id));
    }

    public List<LhApplyInfo> findAllByStatus() {
        return lhApplyInfoRepository.findAllByStatusNotContaining("접수마감");
    }

    public List<LhApplyInfo> findAll() {
        return lhApplyInfoRepository.findAll();
    }

    public List<LhApplyInfo> searchNotices(String type, String region, String status, String q) {
        boolean hasType = !type.isBlank() && !"전체".equals(type);
        boolean hasRegion = !region.isBlank() && !"전국".equals(region);
        boolean hasStatus = !status.isBlank() && !"전체".equals(status);
        boolean hasQ = !q.isBlank();

        // 동적 스펙 조합
        Specification<LhApplyInfo> spec = Specification.where(alwaysTrue());

        if (hasType) {
            spec = spec.and(eq("type", type));
        }
        if (hasStatus) {
            spec = spec.and(eq("status", status));
        }
        if (hasRegion) {
            // 주소 LIKE 검색 허용: 예) '%전%'
            spec = spec.and(likeLower("address", region));
        }

        if (hasQ) {
            // LIKE 검색: 예) '%전%'
            spec = spec.and(likeLower("title", q));
        }

        // 정렬: 최신 등록일 → id 내림차순
        Sort sort = Sort.by(Sort.Direction.DESC, "postDate")
                .and(Sort.by(Sort.Direction.DESC, "id"));

        return lhApplyInfoRepository.findAll(spec, sort);
    }

    // 항상 true인 스펙(시작점)
    private static <T> Specification<T> alwaysTrue() {
        return (root, query, cb) -> cb.conjunction();
    }

    // equals 스펙
    private static <T> Specification<T> eq(String field, String value) {
        return (root, query, cb) -> cb.equal(root.get(field), value);
    }

    // lower(field) LIKE %lower(keyword)%
    private static <T> Specification<T> likeLower(String field, String keyword) {
        return (root, query, cb) -> cb.like(
                cb.lower(root.get(field)),
                "%" + keyword.toLowerCase() + "%"
        );
    }
}
