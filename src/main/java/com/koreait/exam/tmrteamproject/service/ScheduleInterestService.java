package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.ScheduleInterestRepository;
import com.koreait.exam.tmrteamproject.vo.ScheduleInterest;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
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

    public List<ScheduleInterest> findPopup(Long memberId, int limit) {
        return scheduleInterestRepository.findByMemberIdAndIsActiveOrderByRegDateDesc(
                memberId,
                1,
                PageRequest.of(0, limit)
        );
    }
}
