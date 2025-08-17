package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.PropertyFileRepository;
import com.koreait.exam.tmrteamproject.vo.PropertyFile;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
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

    // iOS의 경우 image/heic, image/heif 모두 들어올 수 있음
    private static final Set<String> ALLOWED = Set.of(
            "image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"
            // 필요하면 "application/pdf" 추가
    );

    private final WebClient pythonClient;
    private final PropertyFileRepository propertyFileRepository;

    /** 파일을 DB(PropertyFile)로만 저장 */
    public List<PropertyFile> saveFilesToDb(List<MultipartFile> files) {
        if (files == null || files.isEmpty()) {
            throw new IllegalArgumentException("파일이 없습니다.");
        }

        String ts = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
        List<PropertyFile> saved = new ArrayList<>();

        for (MultipartFile f : files) {
            if (f.isEmpty()) continue;

            String ctype = Optional.ofNullable(f.getContentType()).orElse("");
            if (!ALLOWED.contains(ctype)) {
                throw new IllegalArgumentException("허용되지 않은 파일 형식입니다. (허용: jpg, png, webp, heic)");
            }

            String original = Optional.ofNullable(f.getOriginalFilename()).orElse("image");
            String clean = original.replaceAll("[^a-zA-Z0-9._-]", "_");
            String fileName = ts + "_" + UUID.randomUUID() + "_" + clean;

            try {
                // @Lob String 이므로 Base64로 인코딩하여 저장
                String base64 = Base64.getEncoder().encodeToString(f.getBytes());

                PropertyFile pf = PropertyFile.builder()
                        .fileName(fileName)
                        .fileType(ctype)
                        .data(base64)
                        .build();

                saved.add(propertyFileRepository.save(pf));
            } catch (Exception e) {
                log.error("파일 저장 실패: {}", clean, e);
                throw new RuntimeException("파일 저장 실패: " + clean, e);
            }
        }

        if (saved.isEmpty()) {
            throw new IllegalStateException("저장된 파일이 없습니다.");
        }
        return saved;
    }

    /** DB에 저장된 PropertyFile들만으로 FastAPI /analyze 멀티파트 전송 */
    @SuppressWarnings("unchecked")
    public Map<String, Object> analyzeWithPythonFromDb(List<PropertyFile> filesInDb) {
        if (filesInDb == null || filesInDb.isEmpty()) {
            throw new IllegalArgumentException("분석할 파일이 없습니다.");
        }

        MultipartBodyBuilder mb = new MultipartBodyBuilder();

        for (PropertyFile pf : filesInDb) {
            byte[] bytes;
            try {
                // Base64 → 바이너리 복원
                bytes = Base64.getDecoder().decode(pf.getData().getBytes(StandardCharsets.UTF_8));
            } catch (IllegalArgumentException e) {
                throw new RuntimeException("Base64 디코딩 실패: " + pf.getFileName(), e);
            }

            // 파일명/길이를 가진 ByteArrayResource
            ByteArrayResource resource = new ByteArrayResource(bytes) {
                @Override
                public String getFilename() {
                    return pf.getFileName();
                }
                @Override
                public long contentLength() {
                    return bytes.length;
                }
            };

            mb.part("files", resource)
                    .filename(pf.getFileName())
                    .contentType(MediaType.parseMediaType(
                            Optional.ofNullable(pf.getFileType()).orElse(MediaType.APPLICATION_OCTET_STREAM_VALUE)
                    ));
        }

        Map<String, Object> res = pythonClient.post()
                .uri("/analyze")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .bodyValue(mb.build())
                .retrieve()
                .bodyToMono(Map.class)
                .onErrorResume(ex -> {
                    log.error("분석 서버 호출 실패", ex);
                    return Mono.just(Map.of(
                            "ok", false,
                            "error", "analyze_failed",
                            "message", Optional.ofNullable(ex.getMessage()).orElse("unknown")
                    ));
                })
                .block();

        return Objects.requireNonNullElse(res, Map.of("ok", false, "error", "no_response"));
    }
}