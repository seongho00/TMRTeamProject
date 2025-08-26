package com.koreait.exam.tmrteamproject.security;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import com.koreait.exam.tmrteamproject.vo.Member;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.User;

import java.util.List;

public class MemberContext extends User {

    private final Member member;

    public MemberContext(Member member) {
        super(
                member.getEmail(),
                member.getLoginPw() == null ? "SOCIAL_LOGIN" : member.getLoginPw(),
                List.of(new SimpleGrantedAuthority("ROLE_USER"))
        );
        this.member = member;
    }

    public Member getMember() {
        return member;
    }

    // 로그인 여부 확인
    public boolean isLogined() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();

        if (auth == null || !auth.isAuthenticated()) {
            return false;
        }

        return auth.getPrincipal() instanceof MemberContext;
    }

    // Member 반환
    public Member getLoginedMember() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();

        if (auth == null || !auth.isAuthenticated()) {
            return null;
        }

        Object principal = auth.getPrincipal();
        return (principal instanceof MemberContext mc) ? mc.getMember() : null;
    }

    // 로그인된 Member ID 반환 (없으면 null)
    public Long getLoginedMemberId() {
        Member m = getLoginedMember();
        return m != null ? m.getId() : null;
    }
}
