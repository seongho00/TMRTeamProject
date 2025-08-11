package com.koreait.exam.tmrteamproject.scheduler;

import com.koreait.exam.tmrteamproject.repository.LhSupplyScheduleRepository;
import com.koreait.exam.tmrteamproject.repository.MemberRepository;
import com.koreait.exam.tmrteamproject.repository.ScheduleInterestRepository;
import com.koreait.exam.tmrteamproject.service.SolapiSmsService;
import com.koreait.exam.tmrteamproject.vo.LhSupplySchedule;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.ScheduleInterest;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;

@Component
@RequiredArgsConstructor
public class SmsScheduler {
    private final LhSupplyScheduleRepository lhSupplyScheduleRepository;
    private final SolapiSmsService smsService;
    private final ScheduleInterestRepository scheduleInterestRepository;
    private final MemberRepository memberRepository;

    @Scheduled(cron = "0 0 5 * * *") // 시간설정
    public void checkAndSendSms() {
        LocalDate today = LocalDate.now();

        List<ScheduleInterest> scheduleInterests = scheduleInterestRepository.findAll();


        for (ScheduleInterest si : scheduleInterests) {
            // 관심 일정 가져오기
            LhSupplySchedule lhSupplySchedule = lhSupplyScheduleRepository
                    .findById(si.getScheduleId())
                    .orElse(null);

            if (lhSupplySchedule == null || si.getIsActive() == 0) {
                continue; // 일정 없거나 비활성 상태면 건너뜀
            }
            // 멤버 가져오기
            Member member = memberRepository.findById(si.getMemberId()).orElse(null);
            String phoneNum = member.getPhoneNum();

            LocalDate applyDate = lhSupplySchedule.getApplyStart().toLocalDate();
            long daysUntil = ChronoUnit.DAYS.between(today, applyDate);

            String msg = null;
            if (daysUntil == 7) {
                msg = String.format("[알림] '%s' 신청일이 7일 남았습니다!", lhSupplySchedule.getName());
            } else if (daysUntil == 1) {
                msg = String.format("[알림] '%s' 신청일이 하루 남았습니다!", lhSupplySchedule.getName());
            } else if (daysUntil == 0) {
                msg = String.format("[알림] 오늘은 '%s' 신청일입니다! 신청 시작 시간 : %s",
                        lhSupplySchedule.getName(),
                        lhSupplySchedule.getApplyStart().toString());
            }

            if (msg != null && si.getIsActive() == 1 && phoneNum != null) {
                smsService.sendSms(phoneNum, msg);
            }
        }

        // 또는 DB에서 조건 조회 후 문자 발송도 가능
    }
}
