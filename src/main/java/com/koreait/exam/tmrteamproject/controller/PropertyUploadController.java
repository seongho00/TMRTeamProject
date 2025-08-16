package com.koreait.exam.tmrteamproject.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Controller
@RequestMapping("usr/property")
@RequiredArgsConstructor
public class PropertyUploadController {

    private static final Set<String> ALLOWED = Set.of(
            "image/jpeg", "image/png", "image/webp" // 사진 업로드 기준
            // PDF까지 허용하려면 "application/pdf" 추가
    );

    private final Path uploadRoot;

    public PropertyUploadController() throws IOException {
        // OS 임시폴더 하위에 저장 폴더 생성
        this.uploadRoot = Paths.get(System.getProperty("java.io.tmpdir"), "registry-uploads");
        Files.createDirectories(uploadRoot);
    }

    @GetMapping("/upload")
    public String uploadForm() {
        // templates/registry/upload.html 렌더링
        return "property/upload";
    }

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseBody
    public ResponseEntity<?> handleUpload(@RequestParam("files") List<MultipartFile> files) throws IOException {
        if (files == null || files.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("ok", false, "message", "파일이 없습니다."));
        }

        List<Map<String, Object>> saved = new ArrayList<>();
        String ts = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));

        for (MultipartFile f : files) {
            if (f.isEmpty()) continue;

            String ctype = Optional.ofNullable(f.getContentType()).orElse("");
            if (!ALLOWED.contains(ctype)) {
                return ResponseEntity.badRequest().body(Map.of(
                        "ok", false,
                        "message", "허용되지 않은 파일 형식입니다. (허용: jpg, png, webp)"
                ));
            }

            String original = Optional.ofNullable(f.getOriginalFilename()).orElse("image");
            String clean = original.replaceAll("[^a-zA-Z0-9._-]", "_");
            String ext = clean.contains(".") ? clean.substring(clean.lastIndexOf(".")) : "";
            Path dest = uploadRoot.resolve(ts + "_" + UUID.randomUUID() + ext);

            // 실제 저장
            Files.copy(f.getInputStream(), dest, StandardCopyOption.REPLACE_EXISTING);

            saved.add(Map.of(
                    "originalName", original,
                    "storedPath", dest.toString(),
                    "size", f.getSize(),
                    "contentType", ctype
            ));
        }

        if (saved.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("ok", false, "message", "저장된 파일이 없습니다."));
        }

        // 여기서는 "저장만". 다음 단계에서 파이썬 분석으로 넘길 예정.
        return ResponseEntity.ok(Map.of(
                "ok", true,
                "count", saved.size(),
                "files", saved
        ));
    }
}
