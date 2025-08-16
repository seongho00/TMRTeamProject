package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.vo.StoredFile;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.MediaType;
import org.springframework.http.client.MultipartBodyBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
@Slf4j
public class PropertyService {

    private static final Set<String> ALLOWED = Set.of(
            "image/jpeg", "image/png", "image/webp", "image/heic" // HEIC도 허용(아이폰)
            // "application/pdf" 추가 가능
    );

    private final Path uploadRoot;
    private final WebClient pythonClient;

    public PropertyService(WebClient pythonClient) throws IOException {
        this.pythonClient = pythonClient;
        this.uploadRoot = Paths.get(System.getProperty("java.io.tmpdir"), "registry-uploads");
        Files.createDirectories(uploadRoot);
    }

    /** 파일 저장 (검증 포함) */
    public List<StoredFile> saveFiles(List<MultipartFile> files) throws IOException {
        if (files == null || files.isEmpty()) {
            throw new IllegalArgumentException("파일이 없습니다.");
        }

        List<StoredFile> saved = new ArrayList<>();
        String ts = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));

        for (MultipartFile f : files) {
            if (f.isEmpty()) continue;

            String ctype = Optional.ofNullable(f.getContentType()).orElse("");
            if (!ALLOWED.contains(ctype)) {
                throw new IllegalArgumentException("허용되지 않은 파일 형식입니다. (허용: jpg, png, webp, heic)");
            }

            String original = Optional.ofNullable(f.getOriginalFilename()).orElse("image");
            String clean = original.replaceAll("[^a-zA-Z0-9._-]", "_");
            String ext = clean.contains(".") ? clean.substring(clean.lastIndexOf(".")) : ".jpg";
            Path dest = uploadRoot.resolve(ts + "_" + UUID.randomUUID() + ext);

            Files.copy(f.getInputStream(), dest, StandardCopyOption.REPLACE_EXISTING);

            saved.add(StoredFile.builder()
                    .originalName(original)
                    .contentType(ctype)
                    .size(f.getSize())
                    .storedPath(dest.toString())
                    .fileName(dest.getFileName().toString())
                    .build());
        }

        if (saved.isEmpty()) {
            throw new IllegalStateException("저장된 파일이 없습니다.");
        }
        return saved;
    }

    /** 저장된 파일들을 FastAPI /analyze로 멀티파트 포워딩 */
    @SuppressWarnings("unchecked")
    public Map<String, Object> analyzeWithPython(List<StoredFile> stored) {
        MultipartBodyBuilder mb = new MultipartBodyBuilder();
        for (StoredFile sf : stored) {
            mb.part("files", new FileSystemResource(sf.getStoredPath()))
                    .filename(sf.getFileName());
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