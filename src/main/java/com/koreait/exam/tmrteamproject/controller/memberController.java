package com.koreait.exam.tmrteamproject.controller;


import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("usr/member")
@Slf4j
@RequiredArgsConstructor
public class memberController {

    @GetMapping("/login")
    public String login() {

        return "member/login";
    }

    

}
