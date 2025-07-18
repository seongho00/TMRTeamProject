package com.koreait.exam.tmrteamproject.repository;


import com.koreait.exam.tmrteamproject.vo.AdminDong;
import com.koreait.exam.tmrteamproject.vo.PopulationStat;
import com.koreait.exam.tmrteamproject.vo.PopulationSummary;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface AdminDongRepository extends JpaRepository<AdminDong, String> {

    @Query(value = """
                SELECT *
                FROM admin_dong
                WHERE emd_nm = :emdNm
            """, nativeQuery = true)
    AdminDong findRegionByEmdNm(@Param("emdNm") String emdNm);
}