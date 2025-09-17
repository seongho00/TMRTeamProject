package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.MemberRepository;
import com.koreait.exam.tmrteamproject.security.MemberContext;
import com.koreait.exam.tmrteamproject.vo.Member;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
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
        // MemberContext로 갈 수 있도록 변경
        return new MemberContext(member);
    }
}
