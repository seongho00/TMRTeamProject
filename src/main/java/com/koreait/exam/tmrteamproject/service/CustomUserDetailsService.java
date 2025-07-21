package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.MemberRepository;
import com.koreait.exam.tmrteamproject.util.Ut;
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
public class CustomUserDetailsService implements UserDetailsService {

    private final MemberRepository memberRepository;


    // UserDetailsService 역할을 할 수 있음
    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        Member member = memberRepository.getMemberByEmail(email);

        System.out.println(member);

        if (member == null) {
            throw new UsernameNotFoundException("가입된 사용자가 없습니다: " + email);
        }

        // 로그인 시 사용할 UserDetails 객체 반환
        return org.springframework.security.core.userdetails.User
                .withUsername(member.getEmail())
                .password(member.getLoginPw())
                .roles("USER")  // 또는 member.getRole()로 권한 가져오기
                .build();
    }
}
