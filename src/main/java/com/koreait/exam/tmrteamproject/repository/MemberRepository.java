package com.koreait.exam.tmrteamproject.repository;

import com.koreait.exam.tmrteamproject.vo.Member;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MemberRepository extends JpaRepository<Member, Long> {

    Member getMemberByEmailAndLoginPw(String email, String loginPw);

    Member getMemberByEmail(String email);

    Member findMemberByProviderAndEmail(String provider, String email);
}
