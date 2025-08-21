package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.security.MemberContext;
import com.koreait.exam.tmrteamproject.service.LhSupplyScheduleService;
import com.koreait.exam.tmrteamproject.service.ScheduleInterestService;
import com.koreait.exam.tmrteamproject.vo.LhSupplySchedule;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.ScheduleInterest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import java.util.ArrayList;
import java.util.List;

@Controller
@RequestMapping("usr/home")
@Slf4j
@RequiredArgsConstructor
public class UsrHomeController {

    private final ScheduleInterestService scheduleInterestService;
    private final LhSupplyScheduleService lhSupplyScheduleService;

    @GetMapping("/main")
    public String homeMain(@AuthenticationPrincipal MemberContext memberContext, Model model) {
        Member loginMember = null;
        List<LhSupplySchedule> lhSupplySchedules = new ArrayList<>();
        if (memberContext != null) {
            loginMember = memberContext.getMember();
        }

        if (loginMember != null) {
            List<ScheduleInterest> scheduleInterests = scheduleInterestService.findAllByMemberId(loginMember.getId());

            for (ScheduleInterest scheduleInterest : scheduleInterests) {
                lhSupplySchedules.add(lhSupplyScheduleService.findById(scheduleInterest.getScheduleId()));

            }

            model.addAttribute("loginMemberId", loginMember.getId());
            System.out.println(loginMember.getId());
        }
        System.out.println(lhSupplySchedules);
        model.addAttribute("lhSupplySchedules", lhSupplySchedules);
        return "home/main";
    }

    @GetMapping("/test")
    public String test() {
        return "home/test";
    }

    @GetMapping("/notifications")
    public String notifications() {
        return "home/notifications";
    }
}
