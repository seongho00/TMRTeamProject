package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.TradeArea;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TradeAreaRepository extends JpaRepository<TradeArea, Long> {
    boolean existsByRegionNameAndIndustry(String regionName, String industry);
}
