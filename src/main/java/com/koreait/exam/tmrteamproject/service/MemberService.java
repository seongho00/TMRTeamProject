package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.MemberRepository;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class MemberService {

    private final MemberRepository memberRepository;
    private final PasswordEncoder passwordEncoder;  // ✅ 여기 추가

    @Transactional
    public Member createAccount(String provider, String name, String loginPw, String email, String phoneNum) {
        Member member = Member.builder()
                .provider(provider)
                .name(name)
                .loginPw(passwordEncoder.encode(loginPw))
                .email(email)
                .phoneNum(phoneNum)
                .build();

        memberRepository.save(member);

        return member;
    }


    public ResultData checkDupMemberByEmail(String email) {

        // 이메일로 멤버 가져와보기
        Member loginedMember = memberRepository.getMemberByEmail(email);

        if (loginedMember != null) {
            return ResultData.from("F-1", "이미 가입된 이메일이 있음.");
        }

        return ResultData.from("S-1", "가입 가능");
    }


    public Member getMemberByProviderAndEmail(String provider, String email) {
        Member loginedMember = memberRepository.findMemberByProviderAndEmail(provider, email);
        System.out.println(loginedMember);

        return loginedMember;
    }
}
