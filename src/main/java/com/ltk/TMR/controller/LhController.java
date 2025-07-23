package com.ltk.TMR.controller;

import com.ltk.TMR.entity.LhApplyInfo;
import com.ltk.TMR.service.LhApplyInfoService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable; // 추가
import org.springframework.web.bind.annotation.RequestMapping;

@Slf4j
@Controller
@RequiredArgsConstructor
@RequestMapping("/lh")
public class LhController {

    private final LhApplyInfoService svc;

    // 목록 페이지
    @GetMapping
    public String list(Model model) {
        var lhList   = svc.findAllDesc();
        model.addAttribute("lhList",  lhList);
        return "lh_list";
    }

    // 상세 페이지
    @GetMapping("/{id}")
    public String detail(@PathVariable Long id, Model model) {
        // ID로 공고 데이터 하나를 찾아 모델에 추가
        LhApplyInfo item = svc.findById(id);
        model.addAttribute("item", item);
        return "lh_detail"; // templates/lh_detail.html
    }
}