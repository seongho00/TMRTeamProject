package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.vo.LhApplyInfo;
import com.koreait.exam.tmrteamproject.repository.LhApplyInfoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.persistence.criteria.Predicate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

@Slf4j
@RequiredArgsConstructor
@Service
@Transactional(readOnly = true)
public class LhApplyInfoService {

    private final LhApplyInfoRepository lhApplyInfoRepository;

    @Transactional
    public int upsertBatch(List<LhApplyInfo> items) {
        int affected = 0;
        if (items == null || items.isEmpty()) return affected;

        for (LhApplyInfo dto : items) {
            if (dto == null || dto.getListNo() == null) {
                log.warn("ListNo 없음 → SKIP : {}", dto != null ? dto.getName() : "null");
                continue;
            }
            lhApplyInfoRepository.findByListNo(dto.getListNo())
                    .ifPresentOrElse(found -> {
                        // 기존 레코드 갱신
                        found.updateFrom(dto);
                    }, () -> {
                        // 신규 저장
                        lhApplyInfoRepository.save(dto);
                    });
            affected++;
        }
        return affected;
    }

    public LhApplyInfo findById(Long id) {
        return lhApplyInfoRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Invalid item Id:" + id));
    }

    public List<LhApplyInfo> findAllByStatus() {
        return lhApplyInfoRepository.findAllByStatusNotContaining("접수마감");
    }

    public List<LhApplyInfo> searchNotices(String type, String region, String status, String q) {
        boolean hasType = !type.isBlank() && !"전체".equals(type);
        boolean hasRegion = !region.isBlank() && !"전국".equals(region);
        boolean hasStatus = !status.isBlank() && !"전체".equals(status);
        boolean hasQ = !q.isBlank();

        // 동적 스펙 조합
        Specification<LhApplyInfo> spec = Specification.where(alwaysTrue());

        if (hasType) {
            spec = spec.and(eq("postType", type));
        }
        if (hasStatus) {
            spec = spec.and(eq("status", status));
        }
        if (hasRegion) {
            // 주소 LIKE 검색 허용: 예) '%전%'
            spec = spec.and(likeLower("region", region));
        }

        if (hasQ) {
            List<String> fields = Arrays.asList("name", "region", "postType", "status");
            spec = spec.and(tokensInAnyField(q, fields, true));
        }

        // 정렬: 최신 등록일 → 내림차순
        Sort sort = Sort.by(Sort.Direction.DESC, "postedDate");

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

    private static Specification<LhApplyInfo> tokensInAnyField(String q, List<String> fields, boolean tokens) {
        List<String> allTokens = Arrays.stream(q.trim().split("\\s"))
                .filter(s -> !s.isBlank())
                .map(String::toLowerCase)
                .toList();

        Specification<LhApplyInfo> acc = alwaysTrue();
        for (String token : allTokens) {
            Specification<LhApplyInfo> tokenSpec = anyFieldLike(fields, token);

            // 숫자 토큰이면 siteNo = token 도 OR로 포함
            if (token.chars().allMatch(Character::isDigit)) {
                try {
                    Integer val = Integer.valueOf(token);
                    Specification<LhApplyInfo> bySiteNo = (root, query, cb) -> cb.equal(root.get("siteNo"), val);
                    tokenSpec = tokenSpec.or(bySiteNo);
                } catch (NumberFormatException ignored) {
                }
            }

            acc = tokens ? acc.and(tokenSpec) : acc.or(tokenSpec);
        }
        return acc;
    }

    /** fields 중 아무거나 lower LIKE %token% 매칭되면 OK (OR) */
    private static Specification<LhApplyInfo> anyFieldLike(List<String> fields, String token) {
        return (root, query, cb) -> {
            String like = "%" + token + "%";
            List<Predicate> ors = new ArrayList<>();
            for (String f : fields) {
                ors.add(cb.like(cb.lower(root.get(f)), like));
            }
            return cb.or(ors.toArray(new Predicate[0]));
        };
    }


}
