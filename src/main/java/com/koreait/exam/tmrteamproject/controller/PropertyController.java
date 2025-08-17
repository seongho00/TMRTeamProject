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
        // templates/registry/upload.html 렌더링
        return "property/upload";
    }

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @ResponseBody
    public ResponseEntity<?> handleUpload(@RequestParam("files") List<MultipartFile> files) throws IOException {
        List<PropertyFile> saved = propertyService.saveFilesToDb(files);
        Map<String, Object> analyze = propertyService.analyzeWithPythonFromDb(saved);

        return ResponseEntity.ok(Map.of(
                "ok", true,
                "count", saved.size(),
                "files", saved,
                "analyze", analyze
        ));
    }

    @GetMapping("/selectJuso")
    public String commercialZoneMap(Model model) {

        return "property/selectJuso";
    }


}

