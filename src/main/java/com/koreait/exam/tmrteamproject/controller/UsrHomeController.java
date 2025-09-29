package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.security.MemberContext;
import com.koreait.exam.tmrteamproject.service.DataSetService;
import com.koreait.exam.tmrteamproject.service.LhApplyInfoService;
import com.koreait.exam.tmrteamproject.service.ScheduleInterestService;
import com.koreait.exam.tmrteamproject.vo.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;

@Controller
@RequestMapping("/usr/home")
@Slf4j
@RequiredArgsConstructor
public class UsrHomeController {

    private final ScheduleInterestService scheduleInterestService;
    private final LhApplyInfoService lhApplyInfoService;
    private final DataSetService dataSetService;

    @GetMapping("/main")
    public String homeMain(@AuthenticationPrincipal MemberContext memberContext, @RequestParam(name = "admCd", required = false) String adminDongCode, Model model) {

        // 오늘
        List<LhApplyInfo> nowLhSupplySchedules = new ArrayList<>();
        // 어제
        List<LhApplyInfo> yesterdayLhSupplySchedules = new ArrayList<>();
        // 지난 날(이틀 전 부터)
        List<LhApplyInfo> lastLhSupplySchedules = new ArrayList<>();
        LocalDate now = LocalDate.now(ZoneId.of("Asia/Seoul"));

        if (memberContext != null) {
            Member loginedMember = memberContext.getMember(); // 로그인된 member

            if (loginedMember != null) {
                List<ScheduleInterest> scheduleInterests = scheduleInterestService.findAllByMemberId(loginedMember.getId());

                for (ScheduleInterest scheduleInterest : scheduleInterests) {
                    LhApplyInfo schedule = lhApplyInfoService.findById(scheduleInterest.getScheduleId());

                    LocalDate startDate = schedule.getApplyStart().toLocalDate();

                    if(startDate.isBefore(now)) {
                        lastLhSupplySchedules.add(schedule);
                    } else {
                        nowLhSupplySchedules.add(schedule);
                    }
                }
            }
        }

        // 행정동 코드 기본값 설정
        if (adminDongCode == null || adminDongCode.isBlank()) {
            adminDongCode = "11110615";
        }

        DashBoard dashboard = dataSetService.getDashboardData(adminDongCode);

        model.addAttribute("dashboard", dashboard);
        model.addAttribute("nowLhSupplySchedules", nowLhSupplySchedules);
        model.addAttribute("yesterdayLhSupplySchedules", yesterdayLhSupplySchedules);
        model.addAttribute("lastLhSupplySchedules", lastLhSupplySchedules);
        return "home/main";
    }

    @GetMapping("/notifications")
    public String notifications(@AuthenticationPrincipal MemberContext memberContext, Model model) {

        // 오늘
        List<LhApplyInfo> nowLhApplySchedules = new ArrayList<>();
        // 어제
        List<LhApplyInfo> yesterdayLhApplySchedules = new ArrayList<>();
        // 지난 날(이틀 전 부터)
        List<LhApplyInfo> lastLhApplySchedules = new ArrayList<>();
        LocalDate now = LocalDate.now(ZoneId.of("Asia/Seoul"));

        if (memberContext != null) {
            Member loginedMember = memberContext.getMember(); // 로그인된 member

            if (loginedMember != null) {
                List<ScheduleInterest> scheduleInterests = scheduleInterestService.findAllByMemberId(loginedMember.getId());

                for (ScheduleInterest scheduleInterest : scheduleInterests) {
                    LhApplyInfo schedule = lhApplyInfoService.findById(scheduleInterest.getScheduleId());

                    LocalDate startDate = schedule.getApplyStart().toLocalDate();

                    if(startDate.isBefore(now)) {
                        lastLhApplySchedules.add(schedule);
                    } else {
                        nowLhApplySchedules.add(schedule);
                    }
                }
            }
        }

        model.addAttribute("nowLhApplySchedules", nowLhApplySchedules);
        model.addAttribute("yesterdayLhApplySchedules", yesterdayLhApplySchedules);
        model.addAttribute("lastLhApplySchedules", lastLhApplySchedules);
        return "home/notifications";
    }
}
