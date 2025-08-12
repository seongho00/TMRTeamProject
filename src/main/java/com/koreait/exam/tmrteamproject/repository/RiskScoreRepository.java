package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.AdminDong;
import com.koreait.exam.tmrteamproject.vo.RiskScore;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface RiskScoreRepository extends JpaRepository<RiskScore, String> {

    RiskScore findAllByEmdCd(String emdCd);
}