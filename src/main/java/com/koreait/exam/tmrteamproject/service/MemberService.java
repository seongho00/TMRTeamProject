package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.MemberRepository;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;

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

    /* 회원정보 수정 */
    public ResultData modifyWithoutPw(Long loginedMemberId, String name, String phoneNum, String email) {
        Member member = memberRepository.findById(loginedMemberId).orElseThrow(() -> new RuntimeException("회원이 존재하지 않습니다."));

        if (name != null) member.setName(name);
        if (phoneNum != null) member.setPhoneNum(phoneNum);
        if (email != null) member.setEmail(email);

        memberRepository.save(member);

        return ResultData.from("S-1", "회원정보가 수정되었습니다.", "member", member);
    }

    public ResultData modify(Long loginedMemberId, String loginPw, String name, String phoneNum, String email) {
        Member member = memberRepository.findById(loginedMemberId).orElseThrow(() -> new RuntimeException("회원이 존재하지 않습니다."));

        if (name != null) member.setName(name);
        if (loginPw != null) member.setLoginPw(passwordEncoder.encode(loginPw));
        if (phoneNum != null) member.setPhoneNum(phoneNum);
        if (email != null) member.setEmail(email);

        memberRepository.save(member);

        return ResultData.from("S-1", "회원정보가 수정되었습니다.", "member", member);
    }

    public Member getMemberById(Long loginedMemberId) {
        return memberRepository.findById(loginedMemberId).orElseThrow(() -> new RuntimeException("회원이 존재하지 않습니다. id=" + loginedMemberId));
    }
}
