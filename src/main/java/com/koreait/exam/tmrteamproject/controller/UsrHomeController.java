package com.koreait.exam.tmrteamproject.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("usr/home")
@Slf4j
@RequiredArgsConstructor
public class UsrHomeController {

    @GetMapping("/main")
    public String homeMain() {

        return "home/main";
    }
    @GetMapping("/test")
    public String test() {

        return "home/test";
    }
}
