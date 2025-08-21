package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.PropertyFileRepository;
import com.koreait.exam.tmrteamproject.vo.PropertyFile;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriComponentsBuilder;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.text.Normalizer;
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
    private String hubKey;

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
        String jjuso = sanitizeForJuso(juso);

        // 1) JUSO 조회 (Map으로 받기)
        Map<String, String> j = jusoLookupAsMap(jjuso);
        String admCd = j.get("admCd");
        String sigunguCd = admCd.substring(0, 5);
        String bjdongCd = admCd.substring(5, 10);
        String bun = z4(j.get("lnbrMnnm"));
        String ji = z4(j.get("lnbrSlno"));
        String platGbCd = "1".equals(j.get("mtYn")) ? "1" : "0";


        System.out.println(admCd);


    }

    private String sanitizeForJuso(String s) {
        if (s == null) return "";
        String x = Normalizer.normalize(s, Normalizer.Form.NFC); // NFD → NFC(합성형)
        x = x.replaceAll("\\p{Cf}", "");  // 제로폭·양방향 표시 등 '포맷 문자'
        x = x.replaceAll("\\p{Cc}", "");  // 제어문자
        x = x.replace('\u00A0', ' ');     // NBSP → 공백
        x = x.replaceAll("\\s+", " ").trim();
        x = x.replaceAll("[%=><\\[\\]]", " "); // 방화벽/필터 민감 문자 예방
        return x.trim();
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
        m = Pattern.compile("동\\s*(\\d+)").matcher(s);
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
        String url = "https://business.juso.go.kr/addrlink/addrLinkApi.do";
        UriComponentsBuilder b = UriComponentsBuilder.fromHttpUrl(url)
                .queryParam("confmKey", jusoKey)
                .queryParam("currentPage", 1)
                .queryParam("countPerPage", 10)  // 1 → 10 (여러 후보 허용)
                .queryParam("keyword", keyword)
                .queryParam("resultType", "json")
                .encode(StandardCharsets.UTF_8); // 인코딩 확실히

        String str = b.toUriString();
        log.info("JUSO GET {}", str);                  // 최종 URL 확인용

        Map<String, Object> resp = rest.getForObject(b.toUriString(), Map.class);
        if (resp == null) throw new IllegalStateException("JUSO 응답이 null");

        System.out.println(resp);
        Map<String, Object> results = asMap(resp.get("results"));
        Map<String, Object> common = asMap(results.get("common"));
        String errorCode = str(common.get("errorCode"));   // "0" 이 정상
        String errorMsg = str(common.get("errorMessage"));
        String totalCount = str(common.get("totalCount"));

        // ❗키 오류/접근제한 등은 여기서 바로 알 수 있음
        if (errorCode != null && !"0".equals(errorCode)) {
            throw new IllegalStateException("JUSO 오류 [" + errorCode + "] " + errorMsg + " / keyword=" + keyword);
        }

        List<Object> jusoList = asList(results.get("juso"));
        if (jusoList.isEmpty() || "0".equals(totalCount)) {
            // --- 재시도 플로우 ---
            String simple = simplifyToLegalLot(keyword); // "대전광역시 동구 천동 515"만 남기기
            if (!simple.equals(keyword)) {
                UriComponentsBuilder b2 = UriComponentsBuilder.fromHttpUrl(url)
                        .queryParam("confmKey", jusoKey)
                        .queryParam("currentPage", 1)
                        .queryParam("countPerPage", 20)
                        .queryParam("keyword", simple)
                        .queryParam("resultType", "json")
                        .encode(StandardCharsets.UTF_8);
                Map<String, Object> resp2 = rest.getForObject(b2.toUriString(), Map.class);
                Map<String, Object> results2 = asMap(resp2.get("results"));
                Map<String, Object> common2 = asMap(results2.get("common"));
                String ec2 = str(common2.get("errorCode"));
                String em2 = str(common2.get("errorMessage"));
                String tc2 = str(common2.get("totalCount"));
                List<Object> jusoList2 = asList(results2.get("juso"));

                if (ec2 != null && !"0".equals(ec2)) {
                    throw new IllegalStateException("JUSO 오류(재시도) [" + ec2 + "] " + em2 + " / keyword=" + simple);
                }
                if (!jusoList2.isEmpty() && !"0".equals(tc2)) jusoList = jusoList2;
            }
        }

        if (jusoList.isEmpty()) {
            // 여기까지 왔는데도 없음 → 실제로는 키 오류/접근제한/오타가 대부분
            throw new IllegalStateException("JUSO 검색 실패: " + keyword + " (errorCode=" + errorCode + ", totalCount=" + totalCount + ")");
        }

        Map<String, Object> first = asMap(jusoList.get(0));
        Map<String, String> out = new HashMap<>();
        out.put("admCd", str(first.get("admCd")));
        out.put("lnbrMnnm", str(first.get("lnbrMnnm")));
        out.put("lnbrSlno", str(first.get("lnbrSlno")));
        out.put("mtYn", str(first.get("mtYn")));
        return out;
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
