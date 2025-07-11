package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.MemberRepository;
import com.koreait.exam.tmrteamproject.vo.Member;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class MemberService {

    private final MemberRepository memberRepository;

    @Transactional
    public Member createAccount(String name, String loginPw, String email,String phoneNum) {
        Member member = Member.builder()
                .name(name)
                .loginPw(loginPw)
                .email(email)
                .phoneNum(phoneNum)
                .build();

        memberRepository.save(member);

        return member;
    }

}
