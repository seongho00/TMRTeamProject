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

    // 허용 MIME (필요 시 추가)
    private static final Set<String> ALLOWED = Set.of(
            "image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"
            // "application/pdf"
    );

    private final WebClient pythonClient; // baseUrl은 별도 Bean에서 주입

    /**
     * 업로드 받은 파일을 DB에 저장하지 않고 곧바로 Python /analyze 로 멀티파트 전송
     * @param files  업로드 파일 목록 (form field name: "files")
     * @param extra  함께 보낼 추가 필드(옵션: lat/lng 등 메타데이터)
     * @return       Python이 반환한 JSON(Map)
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> analyzeWithPythonDirect(List<MultipartFile> files, Map<String, String> extra) {
        if (files == null || files.isEmpty()) {
            throw new IllegalArgumentException("분석할 파일이 없습니다.");
        }

        MultipartBodyBuilder mb = new MultipartBodyBuilder();

        // 파일 파트 구성 (스트리밍 전송)
        for (MultipartFile f : files) {
            if (f == null || f.isEmpty()) continue;

            String ctype = Optional.ofNullable(f.getContentType())
                    .orElse(MediaType.APPLICATION_OCTET_STREAM_VALUE);
            if (!ALLOWED.contains(ctype)) {
                throw new IllegalArgumentException("허용되지 않은 파일 형식입니다. (허용: jpg, png, webp, heic)");
            }

            String filename = Optional.ofNullable(f.getOriginalFilename()).orElse("upload");
            long length = f.getSize();

            // InputStreamResource로 메모리 전체 복사 없이 전달
            InputStreamResource resource;
            try {
                resource = new InputStreamResource(f.getInputStream()) {
                    @Override public String getFilename() { return filename; }
                    @Override public long contentLength() { return length; }
                };
            } catch (IOException e) {
                throw new RuntimeException("업로드 파일 스트림 열기 실패: " + filename, e);
            }

            mb.part("files", resource)
                    .filename(filename)
                    .contentType(MediaType.parseMediaType(ctype));
        }

        // 추가 필드(선택: 좌표, 옵션 등)
        if (extra != null) {
            extra.forEach((k, v) -> {
                if (v != null) mb.part(k, v);
            });
        }

        MultiValueMap<String, HttpEntity<?>> parts = mb.build();

        Map<String, Object> res = pythonClient.post()
                .uri("/analyze")
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

    // 오버로드: extra 없이 호출하고 싶을 때
    public Map<String, Object> analyzeWithPythonDirect(List<MultipartFile> files) {
        return analyzeWithPythonDirect(files, Map.of());
    }
}