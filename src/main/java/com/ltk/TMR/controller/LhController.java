package com.ltk.TMR.controller;

import com.ltk.TMR.service.LhApplyInfoService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;           // ★ 추가
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Slf4j                                      // ★ 추가
@Controller
@RequiredArgsConstructor
@RequestMapping("/lh")
public class LhController {

    private final LhApplyInfoService svc;

    /** 공고 목록 화면 */
    @GetMapping
    public String list(Model model) {

        // 서비스에서 가져온 데이터
        var lhList   = svc.findAllDesc();
        var isLoading = svc.isLoading();

        // 진단용
        log.info("LH list size  = {}", lhList.size());
        log.info("LH isLoading  = {}", isLoading);

        // 뷰로 전달
        model.addAttribute("lhList",  lhList);
        model.addAttribute("loading", isLoading);

        return "lh_list";   // templates/lh_list.html
    }
}
