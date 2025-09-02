package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.DataSet;
import com.koreait.exam.tmrteamproject.vo.UpjongCode;
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


    @Query(value =
            "SELECT d.* " +
                    "FROM data_set d " +
                    "WHERE d.base_year_quarter_code = :quarter " +
                    "GROUP BY d.admin_dong_code " +
                    "ORDER BY MAX(d.female_floating_population) DESC",
            nativeQuery = true)
    List<DataSet> findGroupedByAdminDongOrderByFemale(@Param("quarter") String quarter);

    @Query(value =
            "SELECT d.* " +
                    "FROM data_set d " +
                    "WHERE d.base_year_quarter_code = :quarter " +
                    "GROUP BY d.admin_dong_code " +
                    "ORDER BY MAX(d.male_floating_population) DESC",
            nativeQuery = true)
    List<DataSet> findGroupedByAdminDongOrderByMale(@Param("quarter") String quarter);

    @Query(value =
            "SELECT d.* " +
                    "FROM data_set d " +
                    "WHERE d.base_year_quarter_code = :quarter " +
                    "GROUP BY d.admin_dong_code " +
                    "ORDER BY MAX(d.age10floating_population) DESC",
            nativeQuery = true)
    List<DataSet> findGroupedOrderByAge10(@Param("quarter") String quarter);

    @Query(value = "SELECT d.* FROM data_set d GROUP BY d.admin_dong_code ORDER BY MAX(d.age20floating_population) DESC", nativeQuery = true)
    List<DataSet> findGroupedOrderByAge20(@Param("quarter") String quarter);

    @Query(value = "SELECT d.* FROM data_set d GROUP BY d.admin_dong_code ORDER BY MAX(d.age30floating_population) DESC", nativeQuery = true)
    List<DataSet> findGroupedOrderByAge30(@Param("quarter") String quarter);

    @Query(value = "SELECT d.* FROM data_set d GROUP BY d.admin_dong_code ORDER BY MAX(d.age40floating_population) DESC", nativeQuery = true)
    List<DataSet> findGroupedOrderByAge40(@Param("quarter") String quarter);

    @Query(value = "SELECT d.* FROM data_set d GROUP BY d.admin_dong_code ORDER BY MAX(d.age50floating_population) DESC", nativeQuery = true)
    List<DataSet> findGroupedOrderByAge50(@Param("quarter") String quarter);

    @Query(value = "SELECT d.* FROM data_set d GROUP BY d.admin_dong_code ORDER BY MAX(d.age60plus_floating_population) DESC", nativeQuery = true)
    List<DataSet> findGroupedOrderByAge60Plus(@Param("quarter") String quarter);

    @Query(value = "SELECT * FROM data_set d " +
            "WHERE d.admin_dong_code = :emdCd " +
            "AND d.service_industry_code = :upjongCode ",
            nativeQuery = true)
    List<DataSet> findAllByEmdCdAndUpjongCodeGroupByAdminDongCode(@Param("emdCd") String emdCd, @Param("upjongCode") String upjongCode);

    // 행정동 + 분기 데이터 가져오기
    List<DataSet> findByAdminDongCodeAndBaseYearQuarterCode(String adminDongCode, String baseYearQuarterCode);

    // 퍼센트용 계산 구하기
    // 평균 매출액
    @Query("SELECT AVG(d.monthlySalesAmount) FROM DataSet d WHERE d.baseYearQuarterCode = :quarter AND d.adminDongCode = :adminDongCode")
    Double findAvgSalesByQuarter(@Param("quarter") String quarter, String adminDongCode);

    // 분기별 행정동별 점포수 합
    @Query("SELECT SUM(d.storeCount) FROM DataSet d WHERE d.baseYearQuarterCode = :quarter AND d.adminDongCode = :adminDongCode")
    Long findSumStoreCountByQuarter(@Param("quarter") String quarter, String adminDongCode);

    //분기별 행정동별 평균 유동인구
    @Query("SELECT AVG(d.totalFloatingPopulation) FROM DataSet d WHERE d.baseYearQuarterCode = :quarter AND d.adminDongCode = :adminDongCode")
    Double findAvgFloatingByQuarter(@Param("quarter") String quarter, String adminDongCode);
}
