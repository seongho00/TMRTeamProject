package com.koreait.exam.tmrteamproject.repository;


import com.koreait.exam.tmrteamproject.vo.PopulationStat;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.Optional;

public interface PopulationStatRepository extends JpaRepository<PopulationStat, Long> {

    @Query("SELECT p FROM PopulationStat p JOIN AdminDong a ON p.emd_cd = a.emdCd " +
            "WHERE (:sido IS NULL OR a.sidoNm = :sido) " +
            "AND (:sigungu IS NULL OR a.sggNm = :sigungu) " +
            "AND (:emd IS NULL OR a.emdNm = :emdNm)")
    Optional<PopulationStat> findFirstByRegion(@Param("sido") String sido,
                                               @Param("sigungu") String sigungu,
                                               @Param("emdNm") String emdNm);
}
