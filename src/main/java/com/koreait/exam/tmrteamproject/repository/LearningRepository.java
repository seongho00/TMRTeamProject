package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.Learning;
import org.springframework.data.jpa.repository.JpaRepository;

public interface LearningRepository extends JpaRepository<Learning, Long> {
    Learning findAllByHjdCo(String hjdCo);
}
