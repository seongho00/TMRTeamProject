package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.Learning;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface LearningRepository extends JpaRepository<Learning, Long> {

    Learning findAllByHjdCo(String hjdCo);

    List<Learning> findAllByHJDCoAndServiceTypeCode(String hjdCo, String serviceTypeCode);
}
