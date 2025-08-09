package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.LearningService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
@RequiredArgsConstructor
@Slf4j
@RequestMapping("usr/learn")
public class LearningController {

    @Autowired
    private LearningService learningService;

    @GetMapping("/savedDB")
    @ResponseBody
    public String saveData() {
        String csvfile = "C:/Users/user/Downloads/seoul_data_merge/서울_데이터_병합_20231.csv";
        learningService.setSaved(csvfile);

        return "db에 저장됨";
    }

    @GetMapping("/test")
    public String test() {
        return "map/test";
    }
}
