package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.security.MemberContext;
import com.koreait.exam.tmrteamproject.service.LhApplyInfoService;
import com.koreait.exam.tmrteamproject.service.ScheduleInterestService;
import com.koreait.exam.tmrteamproject.vo.LhApplyInfo;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.ScheduleInterest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Controller
@RequiredArgsConstructor
@RequestMapping("/usr/lh")
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

        // 청약 알림함 데이터
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

        model.addAttribute("lhApplyInfoList", lhApplyInfoList);
        model.addAttribute("notifiedIds", notifiedIds);
        model.addAttribute("memberId", memberId); // 로그인 X → null 들어감
        model.addAttribute("nowLhSupplySchedules", nowLhSupplySchedules);
        model.addAttribute("yesterdayLhSupplySchedules", yesterdayLhSupplySchedules);
        model.addAttribute("lastLhSupplySchedules", lastLhSupplySchedules);
        return "subscription/noticeList";
    }

    // 알림설정하기
    @PostMapping("/saveSchedule")
    @ResponseBody
    public String saveSchedule(long scheduleId, long memberId) {

        scheduleInterestService.saveSchedule(memberId, scheduleId);
        return "OK";
    }


    @PostMapping("/deleteSchedule")
    @ResponseBody
    public String deleteSchedule(long scheduleId, long memberId) {

        System.out.println("scheduleId : " + scheduleId);
        System.out.println("memberId : " + memberId);
        scheduleInterestService.deleteSchedule(memberId, scheduleId);
        return "OK";
    }
}
