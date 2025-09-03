package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.LhApplyInfo;

import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface LhApplyInfoRepository extends JpaRepository<LhApplyInfo, Long> {

    Optional<LhApplyInfo> findBySiteNo(int siteNo);

    List<LhApplyInfo> findAllByStatusNotContaining(String status);

    List<LhApplyInfo> findAll(Specification<LhApplyInfo> spec, Sort sort);
}
