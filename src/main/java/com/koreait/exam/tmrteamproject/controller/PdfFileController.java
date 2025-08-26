package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.PdfFileService;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
@Slf4j
@RequiredArgsConstructor
@RequestMapping("usr/pdf")
public class PdfFileController {

    private final PdfFileService pdfFileService;

    @GetMapping("/upload")
    @ResponseBody
    public ResultData upload() {
        String foldPath = "C:/Users/user/Desktop/TeamProject/SimpAnly/";

        // 비동기 실행으로 바꾸기
        pdfFileService.savePdfsAsync(foldPath);

        return ResultData.from("S-1", "PDF 저장 작업이 백그라운드에서 실행됩니다.");
    }
}
