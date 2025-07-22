package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.DataSaveService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
@RequiredArgsConstructor
@Slf4j
@RequestMapping("usr/dataset")
public class DataSaveController {

    private final DataSaveService dataSaveService;

    @GetMapping("/insert")
    @ResponseBody
    public String insert() {
        dataSaveService.setInsertData();
        return "폐업 정보 데이터 저장 성공";
    }
}
