package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.vo.AdminDong;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import java.util.List;

@Controller
@RequestMapping("usr/property")
@Slf4j
@RequiredArgsConstructor
public class PropertyController {

    @GetMapping("/selectJuso")
    public String commercialZoneMap(Model model) {

        return "property/selectJuso";
    }

}

