package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.vo.LhApplyInfo;
import com.koreait.exam.tmrteamproject.service.LhApplyInfoService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;

import java.util.List;

@Slf4j
@Controller
@RequiredArgsConstructor
@RequestMapping("usr/lh")
public class LhController {

    private final LhApplyInfoService lhApplyInfoService;

    @GetMapping
    public String list(Model model) {
        var lhList = lhApplyInfoService.findAllDesc();
        model.addAttribute("lhList", lhList);
        return "lh_list";
    }

    @GetMapping("/{id}")
    public String detail(@PathVariable Long id, Model model) {
        LhApplyInfo item = lhApplyInfoService.findById(id);
        model.addAttribute("item", item);
        return "lh_detail";
    }

    @RequestMapping("/notice")
    public String notice(Model model) {
        List<LhApplyInfo> lhApplyInfo = lhApplyInfoService.findAll();

        model.addAttribute("lhApplyInfo", lhApplyInfo);
        return "subscription/noticelist";
    }
}
