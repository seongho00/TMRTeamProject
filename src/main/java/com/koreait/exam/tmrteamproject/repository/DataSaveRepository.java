package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.ClosedBiz;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DataSaveRepository extends JpaRepository<ClosedBiz, Long> {
}
