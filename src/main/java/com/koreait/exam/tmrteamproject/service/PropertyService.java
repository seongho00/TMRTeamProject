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
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
@Slf4j
@RequiredArgsConstructor
public class PropertyService {

    // ✅ PDF만 허용
    private static final Set<String> ALLOWED = Set.of(MediaType.APPLICATION_PDF_VALUE);

    private final WebClient pythonClient;

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
                    @Override public String getFilename() { return filename; }
                    @Override public long contentLength() { return length; }
                };
            } catch (IOException e) {
                throw new RuntimeException("업로드 파일 스트림 열기 실패: " + filename, e);
            }

            mb.part("files", resource)              // ← Python 쪽이 "files"로 받는다면 그대로 유지
                    .filename(filename.endsWith(".pdf") ? filename : (filename + ".pdf"))
                    .contentType(sendType);
        }

        if (extra != null) {
            extra.forEach((k, v) -> { if (v != null) mb.part(k, v); });
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
                if (buf[i] == '%' && buf[i+1] == 'P' && buf[i+2] == 'D' && buf[i+3] == 'F') return true;
            }
        } catch (Exception ignored) {}
        return false;
    }
}
