package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.repository.LhApplyInfoRepository;
import com.koreait.exam.tmrteamproject.security.MemberContext;
import com.koreait.exam.tmrteamproject.service.ScheduleInterestService;
import com.koreait.exam.tmrteamproject.vo.LhApplyInfo;
import com.koreait.exam.tmrteamproject.service.LhApplyInfoService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Controller
@Slf4j
@RequiredArgsConstructor
@RequestMapping("usr/lh/notice")
public class LhController {

    private final LhApplyInfoService lhApplyInfoService;
    private final ScheduleInterestService scheduleInterestService;

    @GetMapping
    public String notice(
            @RequestParam(required = false, defaultValue = "") String type,
            @RequestParam(required = false, defaultValue = "") String region,
            @RequestParam(required = false, defaultValue = "") String status,
            @RequestParam(required = false, defaultValue = "") String q,
            Model model, @AuthenticationPrincipal MemberContext memberContext) {

        Long memberId = null;
        if (memberContext != null) {
            memberId = memberContext.getMember().getId();
        }

        List<LhApplyInfo> lhApplyInfoList = lhApplyInfoService.searchNotices(type, region, status, q);

        model.addAttribute("lhApplyInfoList", lhApplyInfoList);
        model.addAttribute("memberId", memberId); // 로그인 X → null 들어감
        return "subscription/noticeList";
    }

    // 알림설정하기
    @PostMapping
    @ResponseBody
    public String saveSchedule(long scheduleId, long memberId) {


        System.out.println("실행됨");
        System.out.println("scheduleId:" + scheduleId);
        System.out.println("memberId:" + memberId);

//        scheduleInterestService.saveSchedule(null, 1);

        return "subscription/noticeAdd";
    }
}
