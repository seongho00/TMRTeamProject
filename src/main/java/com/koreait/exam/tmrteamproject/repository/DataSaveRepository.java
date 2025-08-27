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


    @Query(value = "SELECT * FROM data_set d " +
            "WHERE d.admin_dong_code = :emdCd " +
            "AND d.base_year_quarter_code = :quarter " +
            "LIMIT 1",
            nativeQuery = true)
    DataSet findAllByAdminDongCodeAndBaseYearQuarterCodeGroupByAdminDongCode(@Param("emdCd") String emdCd,
                                             @Param("quarter") String quarter);

    @Query(value =
            "SELECT d.* " +
                    "FROM data_set d " +
                    "WHERE d.base_year_quarter_code = :quarter " +
                    "GROUP BY d.admin_dong_code " +
                    "ORDER BY MAX(d.total_floating_population) DESC", // ⚡️ 중요
            nativeQuery = true)
    List<DataSet> findGroupedByAdminDong(@Param("quarter") String quarter);
}
