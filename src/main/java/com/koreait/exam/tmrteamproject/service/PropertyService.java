package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.PropertyFileRepository;
import com.koreait.exam.tmrteamproject.vo.PropertyFile;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.*;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriComponentsBuilder;
import org.springframework.web.util.UriUtils;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.regex.Pattern;

import org.springframework.beans.factory.annotation.Value;

@Service
@Slf4j
@RequiredArgsConstructor
public class PropertyService {

    @Value("${bldrgst.apiKey}")
    private String bldrgstKey;

    @Value("${address.confmKey}")
    private String jusoKey;


    // ✅ PDF만 허용
    private static final Set<String> ALLOWED = Set.of(MediaType.APPLICATION_PDF_VALUE);

    private final WebClient pythonClient;

    private final RestTemplate rest = new RestTemplate();


    @SuppressWarnings("unchecked")
    public Map<String, Object> analyzeWithPythonDirect(List<MultipartFile> files, Map<String, String> extra) {
        if (files == null || files.isEmpty()) {
            throw new IllegalArgumentException("분석할 파일이 없습니다.");
        }

        MultipartBodyBuilder mb = new MultipartBodyBuilder();

        for (MultipartFile f : files) {
            if (f == null || f.isEmpty()) continue;

            String headerCtype = Optional.ofNullable(f.getContentType())
                    .orElse(MediaType.APPLICATION_OCTET_STREAM_VALUE);

            // 헤더가 아니더라도 실제로 PDF인지 스니핑
            boolean headerOk = ALLOWED.contains(headerCtype);
            boolean looksPdf = looksLikePdf(f);

            if (!headerOk && !looksPdf) {
                throw new IllegalArgumentException("허용되지 않은 파일 형식입니다. (PDF만 허용)");
            }

            // ✅ Python으로 넘길 때는 확실히 application/pdf로 지정
            MediaType sendType = MediaType.APPLICATION_PDF;

            String filename = Optional.ofNullable(f.getOriginalFilename()).orElse("upload.pdf");
            long length = f.getSize();

            InputStreamResource resource;
            try {
                resource = new InputStreamResource(f.getInputStream()) {
                    @Override
                    public String getFilename() {
                        return filename;
                    }

                    @Override
                    public long contentLength() {
                        return length;
                    }
                };
            } catch (IOException e) {
                throw new RuntimeException("업로드 파일 스트림 열기 실패: " + filename, e);
            }

            mb.part("files", resource)              // ← Python 쪽이 "files"로 받는다면 그대로 유지
                    .filename(filename.endsWith(".pdf") ? filename : (filename + ".pdf"))
                    .contentType(sendType);
        }

        if (extra != null) {
            extra.forEach((k, v) -> {
                if (v != null) mb.part(k, v);
            });
        }

        var parts = mb.build();

        Map<String, Object> res = pythonClient.post()
                .uri("/analyze")                               // ← Python 엔드포인트가 /analyze(멀티 파일)라면 그대로
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(BodyInserters.fromMultipartData(parts))
                .retrieve()
                .bodyToMono(Map.class)
                .onErrorResume(ex -> {
                    log.error("Python 분석 서버 호출 실패", ex);
                    return Mono.just(Map.of(
                            "ok", false,
                            "error", "analyze_failed",
                            "message", Optional.ofNullable(ex.getMessage()).orElse("unknown")
                    ));
                })
                .block();

        return Objects.requireNonNullElse(res, Map.of("ok", false, "error", "no_response"));
    }

    public Map<String, Object> analyzeWithPythonDirect(List<MultipartFile> files) {
        return analyzeWithPythonDirect(files, Map.of());
    }

    // ===== 유틸: 매직바이트로 PDF 판정 =====
    private boolean looksLikePdf(MultipartFile f) {
        try {
            var is = f.getInputStream();
            byte[] buf = is.readNBytes(1024);
            for (int i = 0; i <= buf.length - 4; i++) {
                if (buf[i] == '%' && buf[i + 1] == 'P' && buf[i + 2] == 'D' && buf[i + 3] == 'F') return true;
            }
        } catch (Exception ignored) {
        }
        return false;
    }


    public void resolveAreaFromLine(String raw) {
        // 1) 전처리: ‘외 n필지’, 대괄호 태그 제거, 공백 정리
        String cleaned = cleanup(raw);

        // 2) 동/호 힌트 추출 (등기부가 “제1층 제103호”처럼 오는 케이스 처리)
        String dongNm = extractDong(cleaned); // “제1동/1동/동1” → 1
        String hoNm = extractHo(cleaned);   // “제103호/103호” → 103
        // 층(층수)은 HUB 파라미터로 쓰지 않으므로 무시

        String juso = simplifyToLegalLot(cleaned);

        // 1) JUSO 조회 (Map으로 받기)
        Map<String, String> j = jusoLookupAsMap(juso);


        String admCd = j.get("admCd");
        String sigunguCd = admCd.substring(0, 5);
        String bjdongCd = admCd.substring(5, 10);
        String bun = "0515";
        String ji = z4(j.get("lnbrSlno"));
        String platGbCd = "1".equals(j.get("mtYn")) ? "1" : "0";


        // 3) HUB getBrExposPubuseAreaInfo 호출 (전유=1, 주건축물=0)
        Map<String, String> q = new LinkedHashMap<>();
        q.put("serviceKey", bldrgstKey);
        q.put("sigunguCd", sigunguCd);
        q.put("bjdongCd", bjdongCd);
        q.put("platGbCd", platGbCd);
        q.put("bun", bun);
        q.put("ji", ji);
        q.put("_type", "json");
        if (dongNm != null) q.put("dongNm", String.valueOf(dongNm));
        if (hoNm != null) q.put("hoNm", String.valueOf(hoNm));

        List<Map<String, Object>> items = callBldRgst(
                "https://apis.data.go.kr/1613000/BldRgstHubService/getBrExposPubuseAreaInfo", q);

        System.out.println(items);
        // 4) 결과 합산(보통 1건)
        double sum = 0.0;
        for (Map<String, Object> it : items) {
            Object area = it.get("area");
            if (area != null) {
                try {
                    sum += Double.parseDouble(String.valueOf(area));
                } catch (Exception ignore) {
                }
            }
        }

    }

    private String cleanup(String s) {
        String x = s;
        x = x.replaceAll("【.*?】", "");
        x = x.replaceAll("\\[.*?\\]", "");
        x = x.replaceAll("외\\s*\\d+\\s*필지", "");
        x = x.replaceAll("\\s+", " ").trim();
        return x;
    }

    private String extractDong(String s) {
        // "제1동", "1동", "동1" 모두 처리
        var m = Pattern.compile("(?:제)?\\s*(\\d+)\\s*동").matcher(s);
        if (m.find()) return m.group(1);
        return null;
    }

    private String extractHo(String s) {
        // "제103호", "103호" 처리
        var m = Pattern.compile("(?:제)?\\s*(\\d+)\\s*호").matcher(s);
        if (m.find()) return m.group(1);
        return null;
    }

    private String z4(String n) {
        if (n == null || n.isBlank()) return "0000";
        String t = n.replaceAll("\\D", "");
        if (t.isBlank()) t = "0";
        return String.format("%04d", Integer.parseInt(t));
    }

    private String simplifyToLegalLot(String s) {
        // "대전광역시 동구 천동 515 ..." → "대전광역시 동구 천동 515"
        var m = Pattern.compile("(.+?\\s[가-힣]+동)\\s(\\d+)(?:-\\d+)?").matcher(s);
        if (m.find()) return m.group(1) + " " + m.group(2);
        return s;
    }

    @SuppressWarnings("unchecked")
    private Map<String, String> jusoLookupAsMap(String keyword) {
        final String url = "https://business.juso.go.kr/addrlink/addrLinkApi.do";

        // 1) POST form 데이터 구성
        org.springframework.util.MultiValueMap<String, String> form = new org.springframework.util.LinkedMultiValueMap<>();
        form.add("confmKey", jusoKey);
        form.add("currentPage", "1");
        form.add("countPerPage", "10");
        form.add("keyword", (keyword == null ? "" : keyword.trim())); // 예: "대전광역시 동구 천동 515"
        form.add("resultType", "json");

        // 2) 헤더: UTF-8 form-data + JSON 응답
        org.springframework.http.HttpHeaders headers = new org.springframework.http.HttpHeaders();
        headers.setContentType(org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED);
        headers.setAccept(java.util.List.of(org.springframework.http.MediaType.APPLICATION_JSON));
        headers.setAcceptCharset(java.util.List.of(java.nio.charset.StandardCharsets.UTF_8));
        headers.set(org.springframework.http.HttpHeaders.USER_AGENT, "Mozilla/5.0"); // 일부 환경에서 필요

        org.springframework.http.HttpEntity<org.springframework.util.MultiValueMap<String, String>> req =
                new org.springframework.http.HttpEntity<>(form, headers);

        // 3) POST 호출 (원문 로그 찍고 Map 파싱)
        org.springframework.http.ResponseEntity<String> respEntity =
                rest.postForEntity(url, req, String.class);
        String body = respEntity.getBody();

        if (body == null) throw new IllegalStateException("JUSO 응답 body가 null");

        java.util.Map<String, Object> resp;
        try {
            resp = new com.fasterxml.jackson.databind.ObjectMapper()
                    .readValue(body, new com.fasterxml.jackson.core.type.TypeReference<java.util.Map<String, Object>>() {
                    });
        } catch (Exception e) {
            throw new IllegalStateException("JUSO 응답 파싱 실패", e);
        }

        // 4) 공통부/결과 파싱
        java.util.Map<String, Object> results = asMap(resp.get("results"));
        System.out.println(results);
        java.util.Map<String, Object> common = asMap(results.get("common"));
        String errorCode = str(common.get("errorCode"));   // "0" 정상
        String errorMsg = str(common.get("errorMessage"));
        String totalCount = str(common.get("totalCount"));

        if (errorCode != null && !"0".equals(errorCode)) {
            throw new IllegalStateException("JUSO 오류 [" + errorCode + "] " + errorMsg + " / keyword=" + keyword);
        }

        java.util.List<Object> jusoList = asList(results.get("juso"));
        if (jusoList.isEmpty() || "0".equals(totalCount)) {
            throw new IllegalStateException("JUSO 검색 실패: " + keyword + " (errorCode=" + errorCode + ", totalCount=" + totalCount + ")");
        }

        java.util.Map<String, Object> first = asMap(jusoList.get(0));
        java.util.Map<String, String> out = new java.util.HashMap<>();
        out.put("admCd", str(first.get("admCd")));
        out.put("lnbrMnnm", str(first.get("lnbrMnnm")));
        out.put("lnbrSlno", str(first.get("lnbrSlno")));
        out.put("mtYn", str(first.get("mtYn")));
        return out;
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> callBldRgst(String endpoint, Map<String, String> params) {
        params.putIfAbsent("numOfRows", "100");
        params.putIfAbsent("pageNo", "1");
        params.putIfAbsent("_type", "json");

        // URL 빌드
        String serviceKey = params.remove("serviceKey"); // 분리

        UriComponentsBuilder ub = UriComponentsBuilder.fromHttpUrl(endpoint);
        params.forEach(ub::queryParam);
        ub.queryParam("serviceKey", serviceKey);

        boolean encodedKey = serviceKey.contains("%");
        String url = encodedKey
                ? ub.build(true).toUriString()                 // ✅ 이미 인코딩된 값 보존 (재인코딩 금지)
                : ub.encode(StandardCharsets.UTF_8).toUriString(); // 일반키면 한 번만 인코딩

        try {
            // 👇 브라우저처럼 헤더 추가
            HttpHeaders headers = new HttpHeaders();
            headers.set(HttpHeaders.ACCEPT, "application/json");
            headers.set(HttpHeaders.USER_AGENT, "Mozilla/5.0");

            HttpEntity<Void> entity = new HttpEntity<>(headers);

            ResponseEntity<Map> resp = rest.exchange(url, HttpMethod.GET, entity, Map.class);
            Map<String, Object> root = resp.getBody();
            if (root == null) return List.of();

            Map<String, Object> response = (Map<String, Object>) root.get("response");
            if (response == null) return List.of();

            Map<String, Object> body  = (Map<String, Object>) response.get("body");
            Map<String, Object> items = (Map<String, Object>) body.get("items");
            Object itemObj = items.get("item");

            List<Map<String, Object>> list = new ArrayList<>();
            if (itemObj instanceof Map) {
                list.add((Map<String, Object>) itemObj);
            } else if (itemObj instanceof List) {
                for (Object o : (List<?>) itemObj) list.add((Map<String, Object>) o);
            }
            return list;
        } catch (Exception e) {
            log.error("BldRgst 호출 실패: {}", e.getMessage(), e);
            return List.of();
        }
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> extractBldItems(Map<String, Object> root) {
        Map<String, Object> response = (Map<String, Object>) root.getOrDefault("response", Map.of());
        Map<String, Object> body = (Map<String, Object>) response.getOrDefault("body", Map.of());
        Map<String, Object> items = (Map<String, Object>) body.getOrDefault("items", Map.of());
        Object itemObj = items.get("item");
        List<Map<String, Object>> list = new ArrayList<>();
        if (itemObj instanceof Map) {
            list.add((Map<String, Object>) itemObj);
        } else if (itemObj instanceof List) {
            for (Object o : (List<?>) itemObj) list.add((Map<String, Object>) o);
        }
        return list;
    }



    /* ------------ 캐스팅/파싱 헬퍼 ------------ */

    @SuppressWarnings("unchecked")
    private Map<String, Object> asMap(Object o) {
        return o instanceof Map ? (Map<String, Object>) o : new LinkedHashMap<>();
    }

    private List<Object> asList(Object o) {
        if (o instanceof List) return (List<Object>) o;
        if (o == null) return Collections.emptyList();
        return List.of(o);
    }

    private String str(Object o) {
        return o == null ? null : String.valueOf(o);
    }

    private double toDouble(Object o, double def) {
        if (o == null) return def;
        try {
            return Double.parseDouble(String.valueOf(o));
        } catch (Exception e) {
            return def;
        }
    }


}
