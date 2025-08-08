package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.DataSaveService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.io.IOException;

@Controller
@RequiredArgsConstructor
@Slf4j
@RequestMapping("usr/dataset")
public class DataSaveController {

    private final DataSaveService dataSaveService;

    @GetMapping("/upload")
    public String upload(@RequestParam(required = false) boolean run, Model model) {
        if (run) {
            try {
                // 리소스 폴더 내 디렉토리 접근 (개발 환경에서만 동작)
                File folder = new ClassPathResource("dataset").getFile();
                File[] files = folder.listFiles((dir, name) -> name.endsWith(".xlsx") || name.endsWith(".xls"));

                if (files == null || files.length == 0) {
                    model.addAttribute("message", "엑셀 파일이 존재하지 않습니다.");
                    return "dataset/excel";
                }

                int success = 0;
                for (File file : files) {
                    String result = dataSaveService.setInsertData(file, model);
                    log.info("처리된 파일: {}, 결과: {}", file.getName(), result);
                    success++;
                }

                model.addAttribute("message", success + "개의 파일을 처리했습니다.");
            } catch (IOException e) {
                model.addAttribute("message", "리소스 폴더 접근 실패: " + e.getMessage());
            }
        }

        return "dataset/excel";
    }
}
