package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.entity.LhApplyInfo;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface LhApplyInfoRepository extends JpaRepository<LhApplyInfo, Long> {

    Optional<LhApplyInfo> findBySiteNo(int siteNo);

    List<LhApplyInfo> findAllByOrderBySiteNoDesc();
}