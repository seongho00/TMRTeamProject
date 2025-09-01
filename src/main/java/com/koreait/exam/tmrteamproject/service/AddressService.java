package com.koreait.exam.tmrteamproject.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.koreait.exam.tmrteamproject.util.CrsConverter;
import com.koreait.exam.tmrteamproject.vo.AddressPickReq;
import com.koreait.exam.tmrteamproject.vo.AddressApiResponse;
import com.koreait.exam.tmrteamproject.vo.NormalizedAddress;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import lombok.RequiredArgsConstructor;
import org.locationtech.proj4j.ProjCoordinate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriComponentsBuilder;
import reactor.core.publisher.Mono;

import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
@Slf4j
public class AddressService {

    @Value("${address.confmKey}")
    private String confmKey;

    @Value("${vworld.key}")
    private String vworldKey;

    private final WebClient pythonClient;


    private final RestTemplate rest = new RestTemplate();

    // 금지 특수문자 / 제어문자 / 보이지 않는 공백(NBSP, ZWSP, FEFF)
    private static final Pattern BLOCK_CHARS =
            Pattern.compile("[%=><\\[\\]\"'`^|{}\\\\]");
    private static final Pattern CONTROL_CHARS =
            Pattern.compile("\\p{Cntrl}");
    private static final Pattern INVISIBLE =
            Pattern.compile("[\\u00A0\\u200B\\u200C\\uFEFF]");

    public List<NormalizedAddress> search(String keyword, int page, int size) {
        String cleaned = sanitizeKeyword(keyword);
        if (cleaned.length() < 2) {
            throw new IllegalArgumentException("검색어를 두 글자 이상, 특수문자 없이 입력하세요.");
        }

        // ✅ GET 대신 POST (x-www-form-urlencoded + UTF-8)
        MultiValueMap<String, String> form = new LinkedMultiValueMap<>();
        form.add("confmKey", confmKey);
        form.add("currentPage", String.valueOf(page));
        form.add("countPerPage", String.valueOf(size));
        form.add("keyword", cleaned);
        form.add("resultType", "json");

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
        headers.setAccept(List.of(MediaType.APPLICATION_JSON));
        headers.setAcceptCharset(List.of(StandardCharsets.UTF_8));

        HttpEntity<MultiValueMap<String, String>> req = new HttpEntity<>(form, headers);

        AddressApiResponse res = rest.postForObject(
                "https://business.juso.go.kr/addrlink/addrLinkApi.do",
                req,
                AddressApiResponse.class
        );

        if (res == null || res.getResults() == null || res.getResults().getCommon() == null) {
            throw new IllegalStateException("Juso API 응답 비정상");
        }

        var common = res.getResults().getCommon();
        if (!"0".equals(common.getErrorCode())) {
            // ❗ 여기서 IllegalArgumentException으로 던져야 컨트롤러에서 400으로 변환됨
            throw new IllegalArgumentException("Juso API 오류: " + common.getErrorMessage());
        }

        var list = res.getResults().getJuso();
        if (list == null) return List.of();

        return list.stream().map(this::map).toList();
    }

    private String sanitizeKeyword(String keyword) {
        if (keyword == null) return "";
        String k = keyword.trim();
        k = CONTROL_CHARS.matcher(k).replaceAll(" ");
        k = INVISIBLE.matcher(k).replaceAll(" ");
        k = BLOCK_CHARS.matcher(k).replaceAll(" ");
        k = k.replaceAll("\\s+", " ");
        return k;
    }

    private NormalizedAddress map(AddressApiResponse.Juso j) {
        NormalizedAddress n = new NormalizedAddress();
        n.setRoadAddr(j.getRoadAddr());
        n.setJibunAddr(j.getJibunAddr());
        n.setZipNo(j.getZipNo());
        n.setLawdCd(j.getAdmCd());
        n.setRnMgtSn(j.getRnMgtSn());
        n.setBdMgtSn(j.getBdMgtSn());
        n.setSiNm(j.getSiNm());
        n.setSggNm(j.getSggNm());
        n.setEmdNm(j.getEmdNm());
        n.setRoadName(j.getRn());
        n.setBuldMnnm(parseInt(j.getBuldMnnm()));
        n.setBuldSlno(parseInt(j.getBuldSlno()));
        n.setJibunMain(parseInt(j.getLnbrMnnm()));
        n.setJibunSub(parseInt(j.getLnbrSlno()));
        if (n.getLawdCd() != null && n.getJibunMain() != null) {
            n.setAddressKey(String.format("%s-%d-%d",
                    n.getLawdCd(), n.getJibunMain(), (n.getJibunSub() == null ? 0 : n.getJibunSub())));
        }
        return n;
    }

    private Integer parseInt(String s) {
        try {
            return (s == null || s.isBlank()) ? null : Integer.parseInt(s);
        } catch (Exception e) {
            return null;
        }
    }

    public NormalizedAddress confirm(AddressPickReq req) {

        NormalizedAddress n = req.getSelected(); // ← map() 필요 없음

        Integer dong = parseIntOnlyDigits(req.getDong());
        Integer ho = parseIntOnlyDigits(req.getHo());

        String baseKey = n.getAddressKey();
        if (baseKey == null || baseKey.isBlank()) {
            if (n.getLawdCd() == null || n.getJibunMain() == null) {
                throw new IllegalArgumentException(
                        "선택 항목에 lawdCd/jibunMain이 없어 addressKey를 만들 수 없습니다. /search 응답 그대로 보내주세요.");
            }
            int sub = n.getJibunSub() == null ? 0 : n.getJibunSub();
            baseKey = String.format("%s-%d-%d", n.getLawdCd(), n.getJibunMain(), sub);
        }

        // addressKey: lawdCd-지번본-지번부-동-호
        String finalKey = String.format("%s-%s-%s",
                baseKey,
                (dong == null ? "00" : String.valueOf(dong)),
                (ho == null ? "00" : String.valueOf(ho)));

        n.setAddressKey(finalKey);
        // (선택) 여기서 n을 DB 저장

        return n;
    }

    private Integer parseIntOnlyDigits(String s) {
        if (s == null) return null;
        String d = s.replaceAll("\\D", ""); // "101동" -> "101"
        if (d.isBlank()) return null;
        try {
            return Integer.parseInt(d);
        } catch (Exception e) {
            return null;
        }
    }

    public NormalizedAddress geocodeByVWorld(NormalizedAddress n) {
        if (n.getRoadAddr() == null || n.getRoadAddr().isBlank())
            throw new IllegalArgumentException("roadAddr가 비었습니다.");

        // 괄호 뒤 아파트명 등은 선택적으로 제거 (매칭률 올리고 싶으면)
        String addr = n.getRoadAddr().replaceAll("\\s*\\(.*\\)$", "");

        URI uri = UriComponentsBuilder
                .fromHttpUrl("https://api.vworld.kr/req/address")
                .queryParam("service", "address")
                .queryParam("request", "getcoord")   // 소문자 권장
                .queryParam("format", "json")
                .queryParam("crs", "EPSG:4326")
                .queryParam("type", "road")          // 소문자 권장
                .queryParam("address", addr)         // ★ 한글 포함 → 아래 encode가 처리
                .queryParam("key", vworldKey)
                .encode(StandardCharsets.UTF_8)      // ★ 값만 안전하게 인코딩
                .build()
                .toUri();

        ResponseEntity<Map> res = rest.getForEntity(uri, Map.class);
        Map<?, ?> body = res.getBody();
        Map<?, ?> resp = (Map<?, ?>) body.get("response");
        if (resp == null || !"OK".equalsIgnoreCase(String.valueOf(resp.get("status")))) {
            throw new IllegalStateException("VWorld 응답 비정상: " + body);
        }

        Map<?, ?> result = (Map<?, ?>) resp.get("result");
        Map<?, ?> pt = (Map<?, ?>) result.get("point");
        double lon = Double.parseDouble(String.valueOf(pt.get("x")));
        double lat = Double.parseDouble(String.valueOf(pt.get("y")));


        n.setLon(lon);
        n.setLat(lat);
        n.setCrs("EPSG:4326");

        ProjCoordinate projCoordinate = CrsConverter.toEPSG5179(lon, lat);

        n.setEntX(projCoordinate.x);
        n.setEntY(projCoordinate.y);
        return n;
    }


    public NormalizedAddress confirmAndGeocode(AddressPickReq req) {
        NormalizedAddress n = confirm(req); // ← 이미 만들었던 메서드 재사용
        // 2) 지오코딩까지 붙이기 (실패해도 전체 실패는 막고 경고만)
        try {
            n = geocodeByVWorld(n);  // ← 앞서 구현한 Juso 좌표 API 호출
            System.out.println(n);
        } catch (Exception e) {
            log.warn("Geocoding failed for {}: {}", n.getAddressKey(), e.getMessage());
            // 필요시 n.setX(null); n.setY(null);
        }
        return n;

    }

    private Map<String, Object> callViewportCrawl(
            double lat, double lng,
            Integer radiusM, String category,
            Map<String, Object> filters, Integer limitDetailFetch
    ) {
        Map<String, Object> payload = new java.util.HashMap<>();
        payload.put("lat", lat);
        payload.put("lng", lng);
        if (radiusM != null) payload.put("radius_m", radiusM);
        if (category != null) payload.put("category", category);
        payload.put("filters", (filters == null ? Map.of() : filters));
        if (limitDetailFetch != null) payload.put("limit_detail_fetch", limitDetailFetch);

        try {
            return pythonClient.post()
                    .uri("/crawl")
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(new org.springframework.core.ParameterizedTypeReference<Map<String, Object>>() {
                    })
                    .block();
        } catch (Exception ex) {
            log.warn("Viewport crawl failed: {}", ex.toString());
            return Map.of("ok", false, "error", "crawl_failed", "message", ex.getMessage());
        }
    }

    /**
     * 기존 confirmAndGeocode 뒤에, 좌표가 있으면 바로 /crawl 호출해서 함께 반환.
     * 반환도 Map으로 단순화.
     */
    public Map<String, Object> confirmGeoAndCrawl(AddressPickReq req) {
        NormalizedAddress n = confirm(req);
        try {
            n = geocodeByVWorld(n);
            System.out.println("n의 값 : " + n);
        } catch (Exception e) {
            log.warn("Geocoding failed for {}: {}", n.getAddressKey(), e.getMessage());
        }
        Map<String, Object> crawl = Map.of("ok", false, "error", "skip", "message", "no geocode");
        if (n.getLat() != null && n.getLon() != null) {
            // 필요 시 radius/category/limit 을 파라미터로 받을 수도 있음. 일단 기본값으로 호출
            crawl = callViewportCrawl(n.getLat(), n.getLon(),
                    800, "offices", Map.of(), 60);
        }

        // 통합 응답 (Address는 그대로 JSON 직렬화됨)
        return Map.of(
                "ok", true,
                "address", n,
                "crawl", crawl
        );
    }

    @SuppressWarnings("unchecked")
    public ResultData calculateAverageMonthly(Map<String, Object> response, double myArea) {
        Map<String, Object> crawl = (Map<String, Object>) response.get("crawl");
        if (crawl == null) {
            return ResultData.from("F-0", "크롤링 데이터 없음", null, 0);
        }


        List<Map<String, Object>> items = (List<Map<String, Object>>) crawl.get("items");
        if (items == null || items.isEmpty()) {
            return ResultData.from("F-0", "매물 없음", null, 0);
        }

        // 내 매물 면적 구간 결정
        String myBand;
        if (myArea < 50) myBand = "small";
        else if (myArea < 100) myBand = "medium";
        else myBand = "large";


        double totalMonthly = 0;
        double totalArea = 0;

        System.out.println("아이템들 : " + items);

        for (Map<String, Object> item : items) {
            Map<String, Object> dom = (Map<String, Object>) item.get("dom");
            if (dom == null) continue;

            // "월세"만 대상으로
            String priceType = (String) dom.get("price_type");
            if (!"월세".equals(priceType)) continue;

            // 월세
            Object monthlyObj = dom.get("monthly");
            if (monthlyObj == null) continue;
            double monthly = Double.parseDouble(monthlyObj.toString()) * 10000; // 원 단위 변환

            // 관리비 포함
//            monthly += parseManagementFee(dom.get("관리비"));

            // 전용면적 파싱 (예: "45.87㎡/30.94㎡(전용률67%)")
            double area = parseArea(dom.get("전용면적"));
            if (area <= 0) continue;

            // 같은 면적 구간만 비교
            String band = area < 50 ? "small" : area < 100 ? "medium" : "large";
            if (!band.equals(myBand)) continue;

            // 면적 가중 평균 계산
            totalMonthly += monthly;
            totalArea += area;
            System.out.println("item : " + item);
            System.out.println("totalMonthly : " + totalMonthly);
            System.out.println("totalArea : " + totalArea);
        }

        // 같은 구간이 없으면 전체 평균으로 fallback
        if (totalArea == 0) {
            for (Map<String, Object> item : items) {
                Map<String, Object> dom = (Map<String, Object>) item.get("dom");
                if (dom == null) continue;

                String priceType = (String) dom.get("price_type");
                if (!"월세".equals(priceType)) continue;

                Object monthlyObj = dom.get("monthly");
                if (monthlyObj == null) continue;
                double monthly = Double.parseDouble(monthlyObj.toString()) * 10000;

                double area = parseArea(dom.get("전용면적"));
                if (area <= 0) continue;

                totalMonthly += monthly;
                totalArea += area;
            }

            return ResultData.from("F-1", "⚠️ 같은 구간 매물이 없어 전체 평균으로 계산합니다.", "전체 평균 월세 데이터", totalMonthly / totalArea);
        }

        double result = totalMonthly / totalArea;

        return ResultData.from("S-1", "평균월세 조회 성공", "평균월세 데이터", result);
    }

    private double parseArea(Object areaObj) {
        if (areaObj == null) return 0;
        String s = areaObj.toString().trim();

        // "45.87㎡/30.94㎡(전용률67%)" -> 30.94
        Matcher m = Pattern.compile("([0-9\\.]+)㎡/([0-9\\.]+)㎡").matcher(s);
        if (m.find()) {
            return Double.parseDouble(m.group(2)); // 전용면적(뒤쪽 값)을 반환
        }

        // 혹시 "/" 없는 단일 값일 경우 대비
        Matcher m2 = Pattern.compile("([0-9\\.]+)㎡").matcher(s);
        if (m2.find()) {
            return Double.parseDouble(m2.group(1));
        }

        try {
            return Double.parseDouble(s);
        } catch (Exception e) {
            return 0;
        }
    }


    @SuppressWarnings("unchecked")
    public double calculateAverageDeposit(Map<String, Object> response) {
        Map<String, Object> crawl = (Map<String, Object>) response.get("crawl");
        if (crawl == null) return 0;

        List<Map<String, Object>> items = (List<Map<String, Object>>) crawl.get("items");
        if (items == null || items.isEmpty()) return 0;

        double totalDeposit = 0;
        double totalArea = 0;

        for (Map<String, Object> item : items) {
            Map<String, Object> dom = (Map<String, Object>) item.get("dom");
            if (dom == null) continue;

            // "월세"만 대상으로
            String priceType = (String) dom.get("price_type");
            if (!"월세".equals(priceType)) continue;

            // 월세
            Object depositObj = dom.get("deposit");
            if (depositObj == null) continue;
            double deposit = Double.parseDouble(depositObj.toString()) * 10000; // 원 단위 변환

            // 관리비 포함
//            monthly += parseManagementFee(dom.get("관리비"));

            // 전용면적 파싱 (예: "45.87㎡/30.94㎡(전용률67%)")
            double area = parseArea(dom.get("전용면적"));
            if (area <= 0) continue;

            totalDeposit += (deposit * area);
            totalArea += area;
        }

        return totalArea > 0 ? totalDeposit / totalArea : 0;
    }
}
