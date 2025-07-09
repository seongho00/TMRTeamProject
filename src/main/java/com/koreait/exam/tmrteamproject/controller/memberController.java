package com.koreait.exam.tmrteamproject.controller;


import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.koreait.exam.tmrteamproject.service.KakaoOAuthService;
import com.koreait.exam.tmrteamproject.service.NaverOAuthService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.client.RestTemplate;

import java.io.UnsupportedEncodingException;
import java.math.BigInteger;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;

@Controller
@RequestMapping("usr/member")
@Slf4j
@RequiredArgsConstructor
public class memberController {

    @Value("${kakao.api.clientId}")
    private String kakaoClientId;

    @Value("${naver.api.clientId}")
    private String naverClientId;

    @Autowired
    private KakaoOAuthService kakaoOAuthService;
    @Autowired
    private NaverOAuthService naverOAuthService;


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


        String redirectURI = "http://localhost:8080/usr/member/naverCallback";
        SecureRandom random = new SecureRandom();
        String state = new BigInteger(130, random).toString();
        String apiURL = "https://nid.naver.com/oauth2.0/authorize?response_type=code" + "&client_id=" + naverClientId
                + "&redirect_uri=" + redirectURI + "&state=" + state;

        return "redirect:" + apiURL;
    }

    @GetMapping("/naverCallback")
    public String naverCallback(String code, String state) throws UnsupportedEncodingException {

        String accessToken = naverOAuthService.requestAccessToken(code, state);

        naverOAuthService.getUserInfo(accessToken);


        return "redirect:../home/main";
    }

    @GetMapping("/doLogout")
    public String doLogout() {


        return "redirect:kakaoLogout";
    }

    @GetMapping("/kakaoLogout")
    public String kakaoLogout() {

        String logoutRedirectUri = "http://localhost:8080/usr/home/main";
        String url = "https://kauth.kakao.com/oauth/logout?client_id=" + kakaoClientId + "&logout_redirect_uri="
                + URLEncoder.encode(logoutRedirectUri, StandardCharsets.UTF_8);
        return "redirect:" + url;

    }


}
