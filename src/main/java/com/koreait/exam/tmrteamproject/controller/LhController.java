package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.vo.LhApplyInfo;
import com.koreait.exam.tmrteamproject.service.LhApplyInfoService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

@Controller
@Slf4j
@RequiredArgsConstructor
@RequestMapping("usr/lh/notice")
public class LhController {

    private final LhApplyInfoService lhApplyInfoService;

    @GetMapping
    public String notice(
            @RequestParam(required = false, defaultValue = "")String type,
            @RequestParam(required = false, defaultValue = "")String region,
            @RequestParam(required = false, defaultValue = "")String status,
            @RequestParam(required = false, defaultValue = "")String q,
            Model model) {

        List<LhApplyInfo> lhApplyInfoList = lhApplyInfoService.searchNotices(type, region, status, q);

        model.addAttribute("lhApplyInfoList", lhApplyInfoList);
        return "subscription/noticeList";
    }
}
