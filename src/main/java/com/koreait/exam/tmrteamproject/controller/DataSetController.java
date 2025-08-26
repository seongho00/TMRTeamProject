package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.DataSetService;
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
public class DataSetController {

    private final DataSetService dataSetService;

    @GetMapping("/upload")
    public String savedDB(Model model) {
        String csvDir = Paths.get("src/main/resources/seoul_data_merge").toString();
        CompletableFuture<Integer> future = dataSetService.saveAllFromDirAsync(csvDir);
        System.out.println(future);

        model.addAttribute("message", "저장 작업을 백그라운드에서 시작했습니다. 잠시 후 완료 됩니다.");
        return "dataset/csv";
    }

    @GetMapping("/usr/home/main")
    public String homeMain(Model model) {
        model.addAttribute("20251", 20251);
        return "redirect:../home/main";
    }
}
