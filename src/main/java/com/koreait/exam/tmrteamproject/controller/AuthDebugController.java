package com.koreait.exam.tmrteamproject.controller;

import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class AuthDebugController {

    @GetMapping("/auth-info")
    public String authInfo() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication == null || !authentication.isAuthenticated()) {
            return "🔒 로그인되지 않음";
        }

        Object principal = authentication.getPrincipal();

        if (principal instanceof UserDetails userDetails) {
            String username = userDetails.getUsername();
            String roles = userDetails.getAuthorities().toString();

            return """
                    ✅ 로그인 상태입니다:
                    - 사용자명: %s
                    - 권한 목록: %s
                    """.formatted(username, roles);
        }

        return "❗ 인증은 되어있지만 UserDetails 타입 아님: " + principal.toString();
    }
}
