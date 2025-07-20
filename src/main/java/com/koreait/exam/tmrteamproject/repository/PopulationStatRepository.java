package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.AdminDong;
import com.koreait.exam.tmrteamproject.vo.PopulationStat;
import com.koreait.exam.tmrteamproject.vo.PopulationSummary;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Map;
import java.util.Optional;

public interface PopulationStatRepository extends JpaRepository<PopulationStat, Long> {

    @Query(value = """
            SELECT 
                SUM(p.total) AS total,
                SUM(p.male) AS male,
                SUM(p.female) AS female,
                SUM(p.age_10) AS age10,
                SUM(p.age_20) AS age20,
                SUM(p.age_30) AS age30,
                SUM(p.age_40) AS age40,
                SUM(p.age_50) AS age50,
                SUM(p.age_60) AS age60
            FROM population_stat p
            JOIN admin_dong a ON p.emd_cd = a.emd_cd
            WHERE a.sido_nm = :sido AND a.sgg_nm = :sigungu AND a.emd_nm = :emd
            """, nativeQuery = true)
    PopulationSummary findBySidoAndSigunguAndEmd(@Param("sido") String sido, @Param("sigungu") String sigungu, @Param("emd") String emd);


    @Query(value = """
            SELECT 
                SUM(p.total) AS total,
                SUM(p.male) AS male,
                SUM(p.female) AS female,
                SUM(p.age_10) AS age10,
                SUM(p.age_20) AS age20,
                SUM(p.age_30) AS age30,
                SUM(p.age_40) AS age40,
                SUM(p.age_50) AS age50,
                SUM(p.age_60) AS age60
            FROM population_stat p
            JOIN admin_dong a ON p.emd_cd = a.emd_cd
            WHERE a.sido_nm = :sido AND a.sgg_nm = :sigungu
            """, nativeQuery = true)
    PopulationSummary findBySidoAndSigungu(@Param("sido") String sido, @Param("sigungu") String sigungu);

    @Query(value = """
            SELECT 
                SUM(p.total) AS total,
                SUM(p.male) AS male,
                SUM(p.female) AS female,
                SUM(p.age_10) AS age10,
                SUM(p.age_20) AS age20,
                SUM(p.age_30) AS age30,
                SUM(p.age_40) AS age40,
                SUM(p.age_50) AS age50,
                SUM(p.age_60) AS age60
            FROM population_stat p
            JOIN admin_dong a ON p.emd_cd = a.emd_cd
            WHERE a.sido_nm = :sido AND a.emd_nm = :emd
            GROUP BY a.sgg_nm
            """, nativeQuery = true)
    List<PopulationSummary> findBySidoAndEmd(@Param("sido") String sido, @Param("emd") String emd);


    @Query(value = """
            SELECT 
                SUM(p.total) AS total,
                SUM(p.male) AS male,
                SUM(p.female) AS female,
                SUM(p.age_10) AS age10,
                SUM(p.age_20) AS age20,
                SUM(p.age_30) AS age30,
                SUM(p.age_40) AS age40,
                SUM(p.age_50) AS age50,
                SUM(p.age_60) AS age60
            FROM population_stat p
            JOIN admin_dong a ON p.emd_cd = a.emd_cd
            WHERE a.sgg_nm = :sigungu AND a.emd_nm = :emd
            """, nativeQuery = true)
    PopulationSummary findBySigunguAndEmd(@Param("sigungu") String sigungu, @Param("emd") String emd);

    @Query(value = """
            SELECT 
                SUM(p.total) AS total,
                SUM(p.male) AS male,
                SUM(p.female) AS female,
                SUM(p.age_10) AS age10,
                SUM(p.age_20) AS age20,
                SUM(p.age_30) AS age30,
                SUM(p.age_40) AS age40,
                SUM(p.age_50) AS age50,
                SUM(p.age_60) AS age60
            FROM population_stat p
            JOIN admin_dong a ON p.emd_cd = a.emd_cd
            WHERE a.sido_nm = :sido
            """, nativeQuery = true)
    PopulationSummary findBySido(@Param("sido") String sido);

    @Query(value = """
            SELECT 
                SUM(p.total) AS total,
                SUM(p.male) AS male,
                SUM(p.female) AS female,
                SUM(p.age_10) AS age10,
                SUM(p.age_20) AS age20,
                SUM(p.age_30) AS age30,
                SUM(p.age_40) AS age40,
                SUM(p.age_50) AS age50,
                SUM(p.age_60) AS age60
            FROM population_stat p
            JOIN admin_dong a ON p.emd_cd = a.emd_cd
            WHERE a.sgg_nm = :sigungu
            """, nativeQuery = true)
    PopulationSummary findBySigungu(@Param("sigungu") String sigungu);

    @Query(value = """
            SELECT 
                SUM(p.total) AS total,
                SUM(p.male) AS male,
                SUM(p.female) AS female,
                SUM(p.age_10) AS age10,
                SUM(p.age_20) AS age20,
                SUM(p.age_30) AS age30,
                SUM(p.age_40) AS age40,
                SUM(p.age_50) AS age50,
                SUM(p.age_60) AS age60
            FROM population_stat p
            JOIN admin_dong a ON p.emd_cd = a.emd_cd
            WHERE a.emd_nm = :emd
            GROUP BY a.sgg_nm
            """, nativeQuery = true)
    List<PopulationSummary> findByEmd(@Param("emd") String emd);

    @Query(value = """
                SELECT *
                FROM admin_dong
                WHERE emd_nm = :emdNm
                GROUP BY sido_nm, sgg_nm
            """, nativeQuery = true)
    AdminDong findRegionByEmdNm(@Param("emdNm") String emdNm);
}
