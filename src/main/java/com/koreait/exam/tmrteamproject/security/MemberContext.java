package com.koreait.exam.tmrteamproject.security;

import org.springframework.security.core.authority.SimpleGrantedAuthority;
import com.koreait.exam.tmrteamproject.vo.Member;
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
}
