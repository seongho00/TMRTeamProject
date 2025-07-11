package com.koreait.exam.tmrteamproject.repository;


import com.koreait.exam.tmrteamproject.vo.Member;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MemberRepository extends JpaRepository<Member, Long> {

}
