package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.ScheduleInterest;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface ScheduleInterestRepository extends JpaRepository<ScheduleInterest, Long> {

    List<ScheduleInterest> findAllByMemberId(Long memberId);

    @Query("select s.scheduleId from ScheduleInterest s where s.memberId = :memberId")
    List<Long> findScheduleIdsByMemberId(Long memberId);

    double deleteByMemberIdAndScheduleId(Long memberId, Long scheduleId);
}
