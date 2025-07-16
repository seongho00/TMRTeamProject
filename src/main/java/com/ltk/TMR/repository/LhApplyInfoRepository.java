package com.ltk.TMR.repository;

import com.ltk.TMR.entity.LhApplyInfo;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface LhApplyInfoRepository extends JpaRepository<LhApplyInfo, Long> {

    Optional<LhApplyInfo> findBySiteNo(Integer siteNo);

    // 정렬 기준을 siteNo로 설정
    List<LhApplyInfo> findAllByOrderBySiteNoDesc();
}