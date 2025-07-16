package com.koreait.exam.tmrteamproject.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@Slf4j
@RequiredArgsConstructor
@RequestMapping("usr/area")
public class MarketAreaController {

    @GetMapping("/page")
    public String binPage() {
        return "trade/binPage";
    }
}
