package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.DataSet;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Collection;
import java.util.List;

public interface DataSetRepository extends JpaRepository<DataSet, Long> {

    @Query(value = """
        SELECT CONCAT_WS('|', base_year_quarter_code, admin_dong_code, service_industry_code) AS k
        FROM data_set
        WHERE CONCAT_WS('|', base_year_quarter_code, admin_dong_code, service_industry_code) IN (:keys)
        """, nativeQuery = true)
    List<String> findExistingKeys(@Param("keys") Collection<String> keys);

    /*
    // 같은 분기 내 최대 유동인구
    @Query("select max(d.totalFloatingPopulation) from DataSet d where d.baseYearQuarterCode = :baseYearQuarterCode")
    Long findMaxFloatingByQuarter(@Param("baseYearQuarterCode") String baseYearQuarterCode);

    // 같은 분기 내 최대 당월 매출금액
    @Query("select max(d.monthlySalesAmount) from DataSet d where d.baseYearQuarterCode = :baseYearQuarterCode")
    Long findMaxSalesByQuarter(@Param("baseYearQuarterCode") String baseYearQuarterCode);

    List<DataSet> findAllByOrderByBaseYearQuarterCodeDesc(String baseYearQuarterCode);
     */
}
