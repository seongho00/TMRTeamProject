package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.UpjongCode;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface UpjongCodeRepository extends JpaRepository<UpjongCode, String> {

    @Query("SELECT u.upjongNm FROM UpjongCode u ORDER BY u.upjongCd")
    List<String> findAllName();

    @Query("SELECT u.upjongNm FROM UpjongCode u WHERE u.upjongNm LIKE %:q% ORDER BY u.upjongCd")
    List<String>searchNames(String q);

    String findUpjongCodeByUpjongNm(String upjongNm);
}
