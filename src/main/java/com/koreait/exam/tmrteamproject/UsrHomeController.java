package com.koreait.exam.tmrteamproject;


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
    public String showRoom() {
        System.out.println("실행");
        return "home/main";
    }
}
