package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.ScheduleInterestRepository;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.ScheduleInterest;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ScheduleInterestService {

    private final ScheduleInterestRepository scheduleInterestRepository;

    public List<ScheduleInterest> findAllByMemberId(Long memberId) {
        return scheduleInterestRepository.findAllByMemberId(memberId);
    }

    @Transactional
    public void saveSchedule(long memberId, long scheduleId) {

        ScheduleInterest scheduleInterest = ScheduleInterest.builder()
                .memberId(memberId)
                .scheduleId(scheduleId)
                .isActive(1)
                .build();

        scheduleInterestRepository.save(scheduleInterest);

    }

    public List<Long> getScheduleIds(Long memberId) {
        return scheduleInterestRepository.findScheduleIdsByMemberId(memberId);
    }

    @Transactional
    public void deleteSchedule(long memberId, long scheduleId) {
        scheduleInterestRepository.deleteByMemberIdAndScheduleId(memberId, scheduleId);
    }
}
