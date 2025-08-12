package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.LearningService;
import com.koreait.exam.tmrteamproject.vo.Learning;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.List;

@Controller
@RequiredArgsConstructor
@Slf4j
@RequestMapping("usr/learn")
public class LearningController {

    @Autowired
    private LearningService learningService;

    @RequestMapping("/savedDB")
    @ResponseBody
    public String saveData(@RequestBody List<Learning> data) {
        int saved = learningService.setSaved(data);
        return saved + "건 저장됨";
    }

    @GetMapping("/test")
    public String test() {
        return "map/test";
    }
}
