package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.UpjongCodeService;
import com.koreait.exam.tmrteamproject.vo.UpjongCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.List;

@Controller
@RequestMapping("usr/upjong")
@Slf4j
@RequiredArgsConstructor
@CrossOrigin(origins = "http://localhost:3000")
public class UpjongCodeController {
    @Autowired
    private UpjongCodeService upjongCodeService;

    @GetMapping("getAllUpjong")
    @ResponseBody
    public List<UpjongCode> getAllUpjong() {
        return upjongCodeService.findAll();
    }
}
