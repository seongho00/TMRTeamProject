package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.MemberRepository;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class MemberService {

    private final MemberRepository memberRepository;

    @Transactional
    public Member createAccount(String name, String loginPw, String email, String phoneNum) {
        Member member = Member.builder()
                .name(name)
                .loginPw(loginPw)
                .email(email)
                .phoneNum(phoneNum)
                .build();

        memberRepository.save(member);

        return member;
    }


    public Member getMemberByEmail(String email) {
        Member loginedMember = memberRepository.getMemberByEmail(email);
        System.out.println(loginedMember);

        return loginedMember;

    }

    public ResultData checkDupMemberByEmail(String email) {

        // 이메일로 멤버 가져와보기
        Member loginedMember = memberRepository.getMemberByEmail(email);

        if (loginedMember != null) {
            return ResultData.from("F-1", "이미 가입된 이메일이 있음.");
        }

        return ResultData.from("S-1", "가입 가능");
    }
}
