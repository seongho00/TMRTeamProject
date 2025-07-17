package com.koreait.exam.tmrteamproject.controller;


import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("usr/home")
@Slf4j
@RequiredArgsConstructor
public class UsrHomeController {

    @GetMapping("/main")
    public String homeMain(@AuthenticationPrincipal OAuth2User oauthUser) {
        if (oauthUser != null) {
            System.out.println("✅ 사용자 속성 목록:");
            oauthUser.getAttributes().forEach((key, value) -> {
                System.out.println(key + " = " + value);
            });

            // 예시: 특정 속성 접근
            String name = (String) oauthUser.getAttributes().get("name");
            String email = (String) oauthUser.getAttributes().get("email");
            String picture = (String) oauthUser.getAttributes().get("picture");

            System.out.println("이름: " + name);
            System.out.println("이메일: " + email);
            System.out.println("프로필 사진 URL: " + picture);
        }
        return "home/main";
    }
}
