package com.koreait.exam.tmrteamproject.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.xml.XmlMapper;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.*;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriComponentsBuilder;
import org.springframework.web.util.UriUtils;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import reactor.core.publisher.Mono;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.springframework.beans.factory.annotation.Value;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import org.w3c.dom.Element;

@Service
@Slf4j
@RequiredArgsConstructor
public class PropertyService {

    @Value("${bldrgst.apiKey}")
    private String bldrgstKey;

    @Value("${bldrgst.apiKeyEncoded:false}")
    private boolean apiKeyEncoded;

    @Value("${address.confmKey}")
    private String jusoKey;

    @Value("${rOne.apiKey}")
    private String rOneApiKey;

    @Value("${vworld.key}")
    private String vworldKey;


    public Map<String, Object> fetchAndCalculate(String emdCd, String dealYmd) throws Exception {

        Map<String, String> params = new HashMap<>();
        params.put("LAWD_CD", "11680"); // 강남구
        params.put("DEAL_YMD", "202508");
        params.put("numOfRows", "100");
        params.put("pageNo", "1");

        List<Map<String, Object>> trades = callRtms(
                "https://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade",
                params
        );
        System.out.println(trades);
        return null;
    }


    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> callRtms(String endpoint, Map<String, String> params) {
        UriComponentsBuilder ub = UriComponentsBuilder.fromHttpUrl(endpoint);

        if (apiKeyEncoded) {
            // 이미 인코딩된 키 → 그대로 추가
            ub.queryParam("serviceKey", bldrgstKey);
            params.forEach((k, v) -> {
                if (v != null && !v.isBlank()) {
                    ub.queryParam(k, org.springframework.web.util.UriUtils.encode(v, StandardCharsets.UTF_8));
                }
            });
            String url = ub.build(true).toUriString();
            logUrlMasked(url);

            String xml = rest.getForObject(url, String.class);
            return parseRtmsXml(xml);

        } else {
            // raw 키 → 직접 인코딩
            ub.queryParam("serviceKey", UriUtils.encode(bldrgstKey, StandardCharsets.UTF_8));
            params.forEach((k, v) -> {
                if (v != null && !v.isBlank()) {
                    ub.queryParam(k, v);
                }
            });
            String url = ub.build(true).toUriString();
            logUrlMasked(url);

            HttpHeaders headers = new HttpHeaders();
            headers.set("Accept", "application/xml");
            headers.set("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
            headers.set("User-Agent", "Mozilla/5.0");

            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<byte[]> response = rest.exchange(
                    URI.create(url),
                    HttpMethod.GET,
                    entity,
                    byte[].class
            );
            String xml = new String(response.getBody(), StandardCharsets.UTF_8);
            return parseRtmsXml(xml);
        }
    }

    private List<Map<String, Object>> parseRtmsXml(String xml) {
        if (xml == null || xml.isBlank()) throw new IllegalStateException("빈 응답");
        try {
            XmlMapper xmlMapper = new XmlMapper();
            JsonNode root = xmlMapper.readTree(xml);

            // header 가져오기 (배열/객체 모두 대응)
            JsonNode header = root.path("header");
            if (header.isArray() && header.size() > 0) {
                header = header.get(0);
            }

            String resultCode = header.path("resultCode").asText();
            String resultMsg = header.path("resultMsg").asText();

            if (!"000".equals(resultCode)) {
                throw new IllegalStateException("RTMS 오류: " + resultCode + " / " + resultMsg);
            }

            // items 파싱
            JsonNode itemsNode = root.path("body").path("items").path("item");
            if (itemsNode.isMissingNode() || itemsNode.isNull()) {
                return List.of();
            }

            List<Map<String, Object>> out = new ArrayList<>();
            if (itemsNode.isArray()) {
                for (JsonNode it : itemsNode) {
                    out.add(nodeToMap(it));
                }
            } else {
                out.add(nodeToMap(itemsNode));
            }
            return out;
        } catch (Exception e) {
            // 디버깅을 위해 원본 XML 출력
            System.err.println("RTMS 원본 XML: " + xml);
            throw new RuntimeException("RTMS XML 파싱 실패", e);
        }
    }



    // ✅ PDF만 허용
    private static final Set<String> ALLOWED = Set.of(MediaType.APPLICATION_PDF_VALUE);

    private final WebClient pythonClient;

    private final RestTemplate rest = new RestTemplate();
    private final ObjectMapper objectMapper = new ObjectMapper();  // ✅ 추가

    private static final Pattern FLOOR_PATTERN = Pattern.compile("제(\\d+)층");
    private static final Pattern HO_PATTERN = Pattern.compile("제(\\d+)호");

    public ResponseEntity<?> getBasePrice(
            String raw, Map<String, Object> item) {

        String cleaned = cleanup(raw);

        String juso = simplifyToLegalLot(cleaned);

        Map<String, Object> resp = jusoLookupAsResp(juso);

        Map<String, Object> results = (Map<String, Object>) resp.get("results");

        List<Object> jusoList = (List<Object>) results.get("juso");

        // 첫 번째 결과만 사용
        Map<String, Object> j = (Map<String, Object>) jusoList.get(0);


        String emd_name = j.get("emdNm").toString(); // "서초동"
        String bunji = j.get("lnbrMnnm").toString(); // 1317
        String ho = j.get("lnbrSlno").toString(); // 20
        String floor = item.get("flrGbCdNm").toString() + "층" + item.get("flrNo").toString(); // 지상층12
        String target_ho = item.get("hoNm").toString(); // 1201
        String sidoNm = (String) j.get("siNm");           // "서울특별시"
        String sggNm = (String) j.get("sggNm");         // "서초구"


        Map<String, Object> payload = new HashMap<>();
        payload.put("emd_name", emd_name);
        payload.put("bunji", bunji);
        payload.put("ho", ho);
        payload.put("floor", floor);
        payload.put("target_ho", target_ho);
        payload.put("sidoNm", sidoNm);
        payload.put("sggNm", sggNm);
        try {
            Map response = pythonClient.post()
                    .uri("/get_base_price")
                    .bodyValue(payload)
                    .retrieve()
                    .bodyToMono(Map.class)
                    .block();

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("ok", false, "error", e.getMessage()));
        }
    }

    public double getRentYield(String region, String type, int page, int perPage) {
        RestTemplate restTemplate = new RestTemplate();

        String statblId = BuildingType.getStatblIdByName(type);
        String clsId = RegionCode.getClsIdByName(region);

        // URL 생성
        String url = UriComponentsBuilder
                .fromHttpUrl("https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do")
                .queryParam("STATBL_ID", statblId)             // 통계표 ID (예시)
                .queryParam("DTACYCLE_CD", "YY")                      // 주기: 매년
                .queryParam("WRTTIME_IDTFR_ID", "2024")              // 년도 구분
                .queryParam("Type", "json")                          // 응답 타입
                .queryParam("ITM_ID", "100002")                   // 소득수익률
                .queryParam("CLS_ID", clsId)                 // 지역코드
                .build(true)                                          // 자동 인코딩
                .toUriString();

        try {
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            JsonNode root = objectMapper.readTree(response.getBody());

            // row[0].DTA_VAL 추출
            JsonNode rows = root.path("SttsApiTblData").get(1).path("row");
            if (rows.isArray() && rows.size() > 0) {
                return rows.get(0).path("DTA_VAL").asDouble();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        return -1;
    }


    @Getter
    public enum RegionCode {
        SEOUL("서울", "500002"),
        BUSAN("부산", "500003"),
        DAEGU("대구", "500004"),
        INCHEON("인천", "500005"),
        GWANGJU("광주", "500006"),
        DAEJEON("대전", "500007"),
        ULSAN("울산", "500008"),
        SEJONG("세종", "500009"),
        GYEONGGI("경기", "500010"),
        GANGWON("강원", "500011"),
        CHUNGBUK("충북", "500012"),
        CHUNGNAM("충남", "500013"),
        JEONBUK("전북", "500014"),
        JEONNAM("전남", "500015"),
        GYEONGBUK("경북", "500016"),
        GYEONGNAM("경남", "500017"),
        JEJU("제주", "500018");

        private final String name;
        private final String clsId;

        RegionCode(String name, String clsId) {
            this.name = name;
            this.clsId = clsId;
        }

        public static String getClsIdByName(String name) {
            for (RegionCode rc : values()) {
                if (name.contains(rc.getName())) {
                    return rc.getClsId();
                }
            }
            throw new IllegalArgumentException("지역명을 찾을 수 없습니다: " + name);
        }
    }

    @Getter
    public enum BuildingType {
        SMALL_SHOP("소규모", "T246253134913401"),
        OFFICE("오피스", "T245883135037859"),
        LARGE_SHOP("중대형", "T242083134887473"),
        COMPLEX_SHOP("집합", "T246393134978815");

        private final String name;
        private final String statblId;

        BuildingType(String name, String statblId) {
            this.name = name;
            this.statblId = statblId;
        }

        public static String getStatblIdByName(String input) {
            for (BuildingType bt : values()) {
                if (input.contains(bt.getName())) {  // contains 매칭
                    return bt.getStatblId();
                }
            }
            throw new IllegalArgumentException("상가 유형을 찾을 수 없습니다: " + input);
        }
    }

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


    public double resolveAreaFromLine(String raw) throws JsonProcessingException {
        List<Map<String, Object>> items = fetchBldRgstItems(raw);

        System.out.println(items);
        // 5) 면적 합산 (필드명이 'area')
        String[] areaKeys = {"area"};
        double sum = 0.0;

        for (Map<String, Object> it : items) {
            // exposPubuseGbCdNm 값 확인
            Object gbNm = it.get("exposPubuseGbCdNm");
            if (gbNm == null) continue;
            String gb = String.valueOf(gbNm).trim();

            // ✅ 전유인 경우만 합산
            if ("전유".equals(gb)) {
                for (String k : areaKeys) {
                    Object v = it.get(k);
                    if (v != null) {
                        try {
                            sum += Double.parseDouble(String.valueOf(v));
                            break;
                        } catch (NumberFormatException ignore) {
                        }
                    }
                }
            }
        }

        log.info("총 면적 합계: {}", sum);
        return sum;
    }

    public List<Map<String, Object>> fetchBldRgstItems(String raw) {
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
        String bun = z4(j.get("lnbrMnnm"));
        String ji = z4(j.get("lnbrSlno"));
        String platGbCd = "1".equals(j.get("mtYn")) ? "1" : "0";

        // 3) HUB getBrExposPubuseAreaInfo 호출 (전유=1, 주건축물=0)
        // 3) 파라미터 구성
        Map<String, String> q = new LinkedHashMap<>();
        q.put("sigunguCd", sigunguCd);
        q.put("bjdongCd", bjdongCd);
        q.put("platGbCd", platGbCd);
        q.put("bun", bun);
        q.put("ji", ji);
//        if (dongNm != null) q.put("dongNm", dongNm);
        if (hoNm != null) q.put("hoNm", hoNm);
        q.put("numOfRows", "100");
        q.put("pageNo", "1");

        // 4) 호출
        List<Map<String, Object>> items = callBldRgst(
                "https://apis.data.go.kr/1613000/BldRgstHubService/getBrExposPubuseAreaInfo", q
        );

        // ✅ totalCount==0 이거나 결과 없음 → fallback 실행
        if (items.isEmpty()) {
            String[] parsed = parseBunJi(raw); // [bun, ji]
            if (parsed != null) {
                bun = z4(parsed[0]);
                ji = z4(parsed[1]);

                q.put("bun", bun);
                q.put("ji", ji);

                items = callBldRgst(
                        "https://apis.data.go.kr/1613000/BldRgstHubService/getBrExposPubuseAreaInfo", q
                );

            }
        }

        return items;
    }

    public String[] parseBunJi(String addr) {
        // "515-2" → bun=515, ji=2
        Matcher m1 = Pattern.compile("(\\d+)-(\\d+)").matcher(addr);
        if (m1.find()) {
            return new String[]{m1.group(1), m1.group(2)};
        }

        // "515번지" or "515 " → bun=515, ji=0
        Matcher m2 = Pattern.compile("(\\d+)").matcher(addr);
        if (m2.find()) {
            return new String[]{m2.group(1), "0"};
        }

        return null; // 못 찾으면 null
    }

    public String cleanup(String s) {
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

    public String simplifyToLegalLot(String s) {
        // "서울특별시 서초구 서초동 1317-16 ..." → "서울특별시 서초구 서초동 1317-16"
        var m = Pattern.compile("(.+?\\s[가-힣]+동)\\s(\\d+(?:-\\d+)?)").matcher(s);
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
    private Map<String, Object> jusoLookupAsResp(String keyword) {
        final String url = "https://business.juso.go.kr/addrlink/addrLinkApi.do";

        System.out.println(keyword);
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

        System.out.println(resp.toString());

        return resp;
    }

    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> callBldRgst(String endpoint, Map<String, String> params) {
        // serviceKey만 “그대로” 넣고, 나머지는 개별 인코딩
        UriComponentsBuilder ub = UriComponentsBuilder.fromHttpUrl(endpoint);

        if (apiKeyEncoded) {
            // 이미 인코딩된 키 → 그대로 추가
            ub.queryParam("serviceKey", bldrgstKey);
            // 다른 파라미터는 값만 인코딩
            params.forEach((k, v) -> {
                if (v != null && !v.isBlank()) {
                    ub.queryParam(k, org.springframework.web.util.UriUtils.encode(v, java.nio.charset.StandardCharsets.UTF_8));
                }
            });
            // ⚠️ 이미 인코딩되었다고 빌더에 알려서 “추가 인코딩 금지”
            //    (serviceKey의 %2B, %3D 등을 그대로 유지)
            String url = ub.build(true).toUriString();
            logUrlMasked(url);
            String xml = rest.getForObject(url, String.class);
            return parseBldRgstXml(xml);

        } else {
            // raw 키 → 빌더가 전체 UTF-8 인코딩
            ub.queryParam("serviceKey", UriUtils.encode(bldrgstKey, StandardCharsets.UTF_8));
            params.forEach((k, v) -> {
                if (v != null && !v.isBlank()) {
                    ub.queryParam(k, v);
                }
            });
            String url = ub.build(true).toUriString();  // 여기서는 build(true)
            logUrlMasked(url);

            // ✅ 헤더 세팅
            HttpHeaders headers = new HttpHeaders();
            headers.set("Accept", "application/xml");
            headers.set("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8");
            headers.set("User-Agent", "Mozilla/5.0");

            HttpEntity<String> entity = new HttpEntity<>(headers);
            ResponseEntity<byte[]> response = rest.exchange(
                    URI.create(url),
                    HttpMethod.GET,
                    entity,
                    byte[].class
            );
            String xml = new String(response.getBody(), StandardCharsets.UTF_8);

            return parseBldRgstXml(xml);
        }
    }

    private List<Map<String, Object>> parseBldRgstXml(String xml) {
        if (xml == null || xml.isBlank()) throw new IllegalStateException("빈 응답");
        try {
            com.fasterxml.jackson.dataformat.xml.XmlMapper xmlMapper = new com.fasterxml.jackson.dataformat.xml.XmlMapper();
            com.fasterxml.jackson.databind.JsonNode root = xmlMapper.readTree(xml);

            // 1) 표준 오류(<OpenAPI_ServiceResponse>) 먼저
            com.fasterxml.jackson.databind.JsonNode cmm = findCmmMsgHeader(root);
            if (cmm != null) {
                String reason = cmm.path("returnReasonCode").asText(null);
                String auth = cmm.path("returnAuthMsg").asText(null);
                String err = cmm.path("errMsg").asText(null);
                throw new IllegalStateException("BldRgst 인증/요청 오류: code=" + reason + ", auth=" + auth + ", msg=" + err);
            }

            // 2) 정상 헤더(<response><header>)
            com.fasterxml.jackson.databind.JsonNode header = root.path("response").path("header");
            String resultCode = header.path("resultCode").asText(null);
            String resultMsg = header.path("resultMsg").asText(null);

            if ("00".equals(resultCode)) {
                // ok
            } else if ("03".equals(resultCode)) {
                log.info("BldRgst: 데이터 없음(03) - {}", resultMsg);
                return java.util.List.of();
            } else if (resultCode != null) {
                throw new IllegalStateException("BldRgst 오류: " + resultCode + " / " + resultMsg);
            }

            // 3) items 추출
            com.fasterxml.jackson.databind.JsonNode itemNode = bestItemNode(root);
            if (itemNode == null || itemNode.isNull() || itemNode.isMissingNode()) return java.util.List.of();

            java.util.List<java.util.Map<String, Object>> out = new java.util.ArrayList<>();
            if (itemNode.isArray()) {
                for (com.fasterxml.jackson.databind.JsonNode it : itemNode) out.add(nodeToMap(it));
            } else {
                out.add(nodeToMap(itemNode));
            }
            return out;
        } catch (RuntimeException re) {
            throw re;
        } catch (Exception e) {
            throw new RuntimeException("XML 파싱 실패", e);
        }
    }

    private void logUrlMasked(String url) {
        if (log.isInfoEnabled()) {
            log.info("BldRgst GET {}", url);
        }
    }

    // JsonNode → Map 변환 간단 헬퍼
    private Map<String, Object> nodeToMap(JsonNode it) {
        Map<String, Object> m = new LinkedHashMap<>();
        it.fields().forEachRemaining(e -> m.put(e.getKey(), e.getValue().asText(null)));
        return m;
    }

    // 가장 흔한 두 경로를 모두 탐색: <response><body><items><item> 또는 <body><items><item>
    private JsonNode bestItemNode(JsonNode root) {
        JsonNode p1 = root.path("response").path("body").path("items").path("item");
        if (!p1.isMissingNode() && !p1.isNull() && (p1.isArray() || p1.size() > 0 || p1.fieldNames().hasNext()))
            return p1;
        JsonNode p2 = root.path("body").path("items").path("item");
        if (!p2.isMissingNode() && !p2.isNull() && (p2.isArray() || p2.size() > 0 || p2.fieldNames().hasNext()))
            return p2;
        return null;
    }

    // ===== 표준 오류 응답(<OpenAPI_ServiceResponse><cmmMsgHeader>) 탐지 헬퍼 =====
    private JsonNode findCmmMsgHeader(JsonNode root) {
        // 1) 루트에 OpenAPI_ServiceResponse가 있는 케이스
        if (root.has("OpenAPI_ServiceResponse")) {
            JsonNode n = root.path("OpenAPI_ServiceResponse").path("cmmMsgHeader");
            if (!isEmpty(n)) return n;
        }
        // 2) 루트 바로 아래에 cmmMsgHeader가 있는 케이스
        if (root.has("cmmMsgHeader")) {
            JsonNode n = root.path("cmmMsgHeader");
            if (!isEmpty(n)) return n;
        }
        // 3) 어디 깊숙이 있든 첫 매치 찾기
        JsonNode n = root.findPath("cmmMsgHeader");
        return isEmpty(n) ? null : n;
    }

    private static boolean isEmpty(JsonNode n) {
        return n == null || n.isMissingNode() || n.isNull()
                || (n.isObject() && !n.fieldNames().hasNext())
                || (n.isArray() && n.size() == 0);
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


    @SuppressWarnings("unchecked")
    public Map<String, Object> printNormalAddresses(Map<String, Object> result) {
        List<Map<String, Object>> addresses =
                (List<Map<String, Object>>) result.get("jointCollateralAddresses");

        if (addresses == null) {
            return Map.of(
                    "ok", false,
                    "message", "jointCollateralAddresses 없음"
            );
        }

        // normal만 필터링
        List<Map<String, Object>> normals = addresses.stream()
                .filter(addr -> "normal".equalsIgnoreCase((String) addr.get("status")))
                .toList();

        // 결과 맵 반환
        Map<String, Object> filtered = new HashMap<>();
        filtered.put("ok", true);
        filtered.put("normalCount", normals.size());
        filtered.put("normalAddresses", normals);

        // 로그 찍기
        System.out.println("✅ 정상(normal) 주소 추출 = " + normals);

        return filtered;
    }


}
