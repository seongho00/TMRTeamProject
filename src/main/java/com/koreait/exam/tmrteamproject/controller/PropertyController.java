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


    private static final Set<String> ALLOWED = Set.of(
            "image/jpeg", "image/png", "image/webp" // 사진 업로드 기준
            // PDF까지 허용하려면 "application/pdf" 추가
    );

    private final PropertyService propertyService;

    @GetMapping("/upload")
    public String uploadForm() {
        // templates/property/upload.html 렌더링
        return "property/upload";
    }

    // 파일 업로드 및 파이썬으로 파일 보내기
    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> handleUpload(
            @RequestPart("files") List<MultipartFile> files,
            @RequestParam(required = false) Double lat,
            @RequestParam(required = false) Double lng
    ) {
        if (files == null || files.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("ok", false, "message", "파일이 없습니다."));
        }

        // PDF만 필터 (MIME/확장자 또는 매직바이트)
        List<MultipartFile> pdfOnly = files.stream()
                .filter(f -> isPdfByHeader(f) || looksLikePdf(f))
                .toList();

        if (pdfOnly.isEmpty()) {
            // PDF가 하나도 없음
            return ResponseEntity.status(415).body(Map.of(
                    "ok", false,
                    "error", "unsupported_media_type",
                    "message", "PDF만 업로드할 수 있습니다."
            ));
        }

        if (pdfOnly.size() > 1) {
            // ✅ PDF 2개 이상 → 경고하고 처리 중단
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

        // 여기까지 왔으면 PDF 1개
        MultipartFile firstPdf = pdfOnly.get(0);

        Map<String, String> extra = new HashMap<>();
        if (lat != null) extra.put("lat", String.valueOf(lat));
        if (lng != null) extra.put("lng", String.valueOf(lng));

        Map<String, Object> result = propertyService.analyzeWithPythonDirect(List.of(firstPdf), extra);
        return ResponseEntity.ok(result);
    }

    // ===== 도우미 =====
    private boolean isPdfByHeader(MultipartFile f) {
        String ct = Optional.ofNullable(f.getContentType()).orElse("");
        return ct.equalsIgnoreCase(MediaType.APPLICATION_PDF_VALUE)
                || (f.getOriginalFilename() != null && f.getOriginalFilename().toLowerCase().endsWith(".pdf"));
    }

    private boolean looksLikePdf(MultipartFile f) {
        try (var is = f.getInputStream()) {
            byte[] buf = is.readNBytes(1024);
            for (int i = 0; i <= buf.length - 4; i++) {
                if (buf[i] == '%' && buf[i+1] == 'P' && buf[i+2] == 'D' && buf[i+3] == 'F') return true;
            }
        } catch (Exception ignored) {}
        return false;
    }


    @GetMapping("/selectJuso")
    public String commercialZoneMap(Model model) {

        return "property/selectJuso";
    }


}

