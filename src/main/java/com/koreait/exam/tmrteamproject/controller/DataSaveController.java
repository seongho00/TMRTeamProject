package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.DataSaveService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.nio.file.Paths;
import java.util.concurrent.CompletableFuture;

@Controller
@RequiredArgsConstructor
@Slf4j
@RequestMapping("usr/dataset")
public class DataSaveController {

    private final DataSaveService dataSaveService;

    @GetMapping("/upload")
    public String savedDB(Model model) {
        String csvDir = Paths.get("src/main/resources/seoul_data_merge").toString();
        CompletableFuture<Integer> future = dataSaveService.saveAllFromDirAsync(csvDir);
        System.out.println(future);

        model.addAttribute("message", "저장 작업을 백그라운드에서 시작했습니다. 잠시 후 완료 됩니다.");
        return "dataset/csv";
    }
}
