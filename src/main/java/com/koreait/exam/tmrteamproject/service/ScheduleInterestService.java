package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.MemberRepository;
import com.koreait.exam.tmrteamproject.repository.ScheduleInterestRepository;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import com.koreait.exam.tmrteamproject.vo.ScheduleInterest;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ScheduleInterestService {

    private final ScheduleInterestRepository scheduleInterestRepository;
    private final PasswordEncoder passwordEncoder;  // ✅ 여기 추가

    public List<ScheduleInterest> findAllByMemberId(Long memberId) {
        return scheduleInterestRepository.findAllByMemberId(memberId);
    }
}
