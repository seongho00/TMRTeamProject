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
@RequestMapping("usr/lh")
public class LhController {

    private final LhApplyInfoService lhApplyInfoService;
    private final ScheduleInterestService scheduleInterestService;

    @GetMapping("/notice")
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

        List<Long> notifiedIds = (memberId != null)
                ? scheduleInterestService.getScheduleIds(memberId)
                : List.of();

        List<LhApplyInfo> lhApplyInfoList = lhApplyInfoService.searchNotices(type, region, status, q);

        model.addAttribute("lhApplyInfoList", lhApplyInfoList);
        model.addAttribute("notifiedIds", notifiedIds);
        model.addAttribute("memberId", memberId); // 로그인 X → null 들어감
        return "subscription/noticeList";
    }

    // 알림설정하기
    @PostMapping("/saveSchedule")
    @ResponseBody
    public String saveSchedule(long scheduleId, long memberId) {

        scheduleInterestService.saveSchedule(memberId, scheduleId);
        return "OK";
    }
}
