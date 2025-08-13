package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.DataSet;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DataSaveRepository extends JpaRepository<DataSet, Long> {
    boolean existsByBaseYearQuarterCodeAndAdminDongCodeAndServiceIndustryCode(String baseYearQuarterCode, String adminDongCode, String serviceIndustryCode);
}
