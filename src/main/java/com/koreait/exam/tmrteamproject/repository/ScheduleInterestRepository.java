package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.ScheduleInterest;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ScheduleInterestRepository extends JpaRepository<ScheduleInterest, Long> {
    List<ScheduleInterest> findAllByMemberId(Long memberId);
}
