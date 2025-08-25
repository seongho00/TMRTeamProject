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

        // 화면 리스트용: 관심일정 전체
        List<LhSupplySchedule> lhSupplySchedules = new ArrayList<>();

        if (memberContext != null) {
            Member loginedMember = memberContext.getMember(); // 로그인된 member

            if (loginedMember != null) {
                List<ScheduleInterest> scheduleInterests = scheduleInterestService.findAllByMemberId(loginedMember.getId());

                for (ScheduleInterest scheduleInterest : scheduleInterests) {
                    lhSupplySchedules.add(lhSupplyScheduleService.findById(scheduleInterest.getScheduleId()));
                }
            }
        }

        // 모델 바인딩
        model.addAttribute("lhSupplySchedules", lhSupplySchedules);
        return "home/main";
    }

    @GetMapping("/notifications")
    public String notifications(@AuthenticationPrincipal MemberContext memberContext, Model model) {

        List<LhSupplySchedule> lhSupplySchedules = new ArrayList<>();

        if (memberContext != null) {
            Member loginedMember = memberContext.getMember(); // 로그인된 member

            if (loginedMember != null) {
                List<ScheduleInterest> scheduleInterests = scheduleInterestService.findAllByMemberId(loginedMember.getId());

                for (ScheduleInterest scheduleInterest : scheduleInterests) {
                    lhSupplySchedules.add(lhSupplyScheduleService.findById(scheduleInterest.getScheduleId()));
                }
            }
        }

        System.out.println(lhSupplySchedules);
        model.addAttribute("lhSupplySchedules", lhSupplySchedules);
        return "home/notifications";
    }
}
