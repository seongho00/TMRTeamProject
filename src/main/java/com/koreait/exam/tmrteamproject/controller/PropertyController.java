package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.PropertyService;
import com.koreait.exam.tmrteamproject.vo.AdminDong;
import com.koreait.exam.tmrteamproject.vo.PropertyFile;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;


@Controller
@RequestMapping("usr/property")
@Slf4j
@RequiredArgsConstructor
public class PropertyController {

    private final PropertyService propertyService;

    @GetMapping("/upload")
    public String uploadForm() {
        // templates/property/upload.html 렌더링
        return "property/upload";
    }

    // 파일 업로드 및 파이썬으로 파일 보내기
    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> handleUpload(
            @RequestPart(value = "file", required = false) MultipartFile file,
            @RequestPart(value = "files", required = false) List<MultipartFile> files,
            @RequestParam(required = false) Double lat,
            @RequestParam(required = false) Double lng
    ) {
        // 1) 들어온 파일 모으기 (file 또는 files)
        List<MultipartFile> all = new ArrayList<>();
        if (file != null && !file.isEmpty()) all.add(file);
        if (files != null) {
            for (MultipartFile f : files) if (f != null && !f.isEmpty()) all.add(f);
        }
        if (all.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("ok", false, "message", "파일이 없습니다."));
        }

        // 2) PDF만 추리기 (MIME/확장자 + 매직바이트 스니핑)
        List<MultipartFile> pdfOnly = all.stream()
                .filter(f -> isPdfByHeader(f) || looksLikePdf(f))
                .toList();

        if (pdfOnly.isEmpty()) {
            return ResponseEntity.status(415).body(Map.of(
                    "ok", false,
                    "error", "unsupported_media_type",
                    "message", "PDF만 업로드할 수 있습니다."
            ));
        }

        // 3) PDF가 2개 이상이면 경고하고 중단
        if (pdfOnly.size() > 1) {
            List<String> names = pdfOnly.stream()
                    .map(f -> Optional.ofNullable(f.getOriginalFilename()).orElse("noname"))
                    .toList();
            return ResponseEntity.badRequest().body(Map.of(
                    "ok", false,
                    "error", "too_many_pdfs",
                    "message", "PDF는 1개만 업로드하세요.",
                    "count", pdfOnly.size(),
                    "files", names
            ));
        }

        // 4) 좌표 메타(옵션)
        Map<String, String> extra = new HashMap<>();
        if (lat != null) extra.put("lat", String.valueOf(lat));
        if (lng != null) extra.put("lng", String.valueOf(lng));

        // 5) 정상 처리
        MultipartFile thePdf = pdfOnly.get(0);
        Map<String, Object> result = propertyService.analyzeWithPythonDirect(List.of(thePdf), extra);
        return ResponseEntity.ok(result);
    }

    private boolean isPdfByHeader(MultipartFile f) {
        String ct = Optional.ofNullable(f.getContentType()).orElse("");
        return ct.equalsIgnoreCase(MediaType.APPLICATION_PDF_VALUE)
                || Optional.ofNullable(f.getOriginalFilename()).orElse("")
                .toLowerCase().endsWith(".pdf");
    }

    private boolean looksLikePdf(MultipartFile f) {
        try (var is = f.getInputStream()) {
            byte[] buf = is.readNBytes(1024);
            for (int i = 0; i <= buf.length - 4; i++) {
                if (buf[i] == '%' && buf[i + 1] == 'P' && buf[i + 2] == 'D' && buf[i + 3] == 'F') return true;
            }
        } catch (Exception ignored) {
        }
        return false;
    }


    @GetMapping("/selectJuso")
    public String commercialZoneMap(Model model) {

        return "property/selectJuso";
    }


}

