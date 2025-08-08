package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.entity.LhApplyInfo;
import com.koreait.exam.tmrteamproject.service.LhApplyInfoService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;

@Slf4j
@Controller
@RequiredArgsConstructor
@RequestMapping("/lh")
public class LhController {

    private final LhApplyInfoService svc;

    @GetMapping
    public String list(Model model) {
        var lhList = svc.findAllDesc();
        model.addAttribute("lhList", lhList);
        return "lh_list";
    }

    @GetMapping("/{id}")
    public String detail(@PathVariable Long id, Model model) {
        LhApplyInfo item = svc.findById(id);
        model.addAttribute("item", item);
        return "lh_detail";
    }
}