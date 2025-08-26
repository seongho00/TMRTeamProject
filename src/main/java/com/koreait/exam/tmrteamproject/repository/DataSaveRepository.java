package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.DataSet;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Collection;
import java.util.List;
import java.util.Set;

public interface DataSaveRepository extends JpaRepository<DataSet, Long> {

    @Query(value = """
        SELECT CONCAT_WS('|', base_year_quarter_code, admin_dong_code, service_industry_code) AS k
        FROM data_set
        WHERE CONCAT_WS('|', base_year_quarter_code, admin_dong_code, service_industry_code) IN (:keys)
        """, nativeQuery = true)
    List<String> findExistingKeys(@Param("keys") Collection<String> keys);

    List<DataSet> findAllByAdminDongCodeAndServiceIndustryCode(String adminDongCode, String serviceIndustryCode);
}
