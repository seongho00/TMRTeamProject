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

    /* 회원정보 수정 (비밀번호 제외) */
    @Transactional
    public ResultData modifyWithoutPw(Long loginedMemberId, String name, String phoneNum) {
        Member member = memberRepository.findById(loginedMemberId)
                .orElseThrow(() -> new RuntimeException("회원이 존재하지 않습니다."));

        if (name != null) member.setName(name);
        if (phoneNum != null) member.setPhoneNum(phoneNum);

        // 주석: save() 호출 → 팀 차원에서 '명시적 업데이트' 의도 드러냄
        memberRepository.save(member);

        return ResultData.from("S-1", "회원정보가 수정되었습니다.", "member", member);
    }

    public Member getMemberById(Long loginedMemberId) {
        return memberRepository.findById(loginedMemberId).orElseThrow(() -> new RuntimeException("회원이 존재하지 않습니다. id=" + loginedMemberId));
    }

    // 비밀번호 변경
    @Transactional
    public ResultData changePassword(Long loginedMemberId, String oldPw, String newPw) {

        // 주석: 회원 조회
        Member member = memberRepository.findById(loginedMemberId)
                .orElseThrow(() -> new RuntimeException("회원이 존재하지 않습니다."));

        // 주석: 기존 비밀번호 검증 (저장된 비밀번호가 해시인 경우 matches 사용)
        if (!passwordEncoder.matches(oldPw, member.getLoginPw())) {
            return ResultData.from("F-1", "현재 비밀번호가 일치하지 않아");
        }

        // 주석: 동일 비밀번호 방지(선택) - 필요 없으면 제거
        if (passwordEncoder.matches(newPw, member.getLoginPw())) {
            return ResultData.from("F-2", "이전과 동일한 비밀번호는 사용할 수 없어");
        }

        // 주석: 새 비밀번호 저장
        member.setLoginPw(passwordEncoder.encode(newPw));
        memberRepository.save(member);

        return ResultData.from("S-1", "비밀번호 변경 완료", "memberId", member.getId());
    }
}
