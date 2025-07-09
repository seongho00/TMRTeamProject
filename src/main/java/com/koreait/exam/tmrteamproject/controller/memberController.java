package com.koreait.exam.tmrteamproject.controller;


import com.koreait.exam.tmrteamproject.service.KakaoOAuthService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("usr/member")
@Slf4j
@RequiredArgsConstructor
public class memberController {

    @Value("${kakao.api.clientId}")
    private String kakaoClientId;

    @Autowired
    private KakaoOAuthService kakaoOAuthService;

    @GetMapping("/login")
    public String login() {

        return "member/login";
    }

    @GetMapping("/loginKakao")
    public String loginKakao() {
        System.out.println("loginKakao 실행됨");
        String kakaoRedirectUri = "http://localhost:8080/usr/member/kakaoCallback";

        return "redirect:https://kauth.kakao.com/oauth/authorize?response_type=code&client_id=" + kakaoClientId + "&redirect_uri=" + kakaoRedirectUri;
    }

    @GetMapping("/kakaoCallback")
    public String kakaoCallback(String code) {

        String accessToken = kakaoOAuthService.requestAccessToken(code);

        kakaoOAuthService.getUserInfo(accessToken);

        return "redirect:../home/main";
    }


    @GetMapping("/loginNaver")
    public String loginNaver() {

        return "member/login";
    }


}
