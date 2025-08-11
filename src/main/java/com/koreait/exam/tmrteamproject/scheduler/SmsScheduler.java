package com.koreait.exam.tmrteamproject.scheduler;

import com.koreait.exam.tmrteamproject.repository.LhSupplyScheduleRepository;
import com.koreait.exam.tmrteamproject.service.SolapiSmsService;
import com.koreait.exam.tmrteamproject.vo.LhSupplySchedule;
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

    @Scheduled(cron = "0 9 11 * * *") // 매일 오전 9시
    public void checkAndSendSms() {
        LocalDate today = LocalDate.now();

        List<LhSupplySchedule> LhSupplySchedules = lhSupplyScheduleRepository.findAll();
        System.out.println(LhSupplySchedules);

        for (LhSupplySchedule lhSupplySchedule : LhSupplySchedules) {
            LocalDate applyDate = lhSupplySchedule.getApplyStart().toLocalDate();


            long daysUntil = ChronoUnit.DAYS.between(today, applyDate);

            String msg = null;
            if (daysUntil == 7) {
                msg = String.format("[알림] '%s' 신청일이 7일 남았습니다!", lhSupplySchedule.getName());
            } else if (daysUntil == 1) {
                msg = String.format("[알림] '%s' 신청일이 하루 남았습니다!", lhSupplySchedule.getName());
            } else if (daysUntil == 0) {
                msg = String.format("[알림] 오늘은 '%s' 신청일입니다!", lhSupplySchedule.getName());
            }
            if (msg != null) {
                // TODO: 대상자 전화번호 컬럼이 있다면 loop 돌면서 발송
                smsService.sendSms("01022087215", msg);
            }

        }

        // 또는 DB에서 조건 조회 후 문자 발송도 가능
    }
}
