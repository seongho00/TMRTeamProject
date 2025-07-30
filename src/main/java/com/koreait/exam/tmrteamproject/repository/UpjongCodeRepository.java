package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.UpjongCode;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface UpjongCodeRepository extends JpaRepository<UpjongCode, String> {

    List<UpjongCode> getUpjongCodesByMajorNm(String majorNm);

    @Query(value = """
                SELECT *
                FROM upjong_code
                WHERE major_cd = :majorCd
                GROUP BY middle_cd
            """, nativeQuery = true)
    List<UpjongCode> getGroupedUpjongCodesByMajorCd(String majorCd);

    List<UpjongCode> getUpjongCodesByMiddleCd(String middleCd);

    UpjongCode getUpjongCodeByMinorCd(String minorCd);

    @Query("""
                SELECT u
                FROM UpjongCode u
                WHERE u.majorNm LIKE CONCAT('%', :keyword, '%')
                   OR u.middleNm LIKE CONCAT('%', :keyword, '%')
                   OR u.minorNm LIKE CONCAT('%', :keyword, '%')
            """)
    List<UpjongCode> getUpjongCodeByKeyword(String keyword);
}
