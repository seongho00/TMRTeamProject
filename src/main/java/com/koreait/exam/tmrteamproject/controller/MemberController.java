package com.koreait.exam.tmrteamproject.controller;

import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.auth.FirebaseAuthException;
import com.google.firebase.auth.FirebaseToken;
import com.koreait.exam.tmrteamproject.service.KakaoOAuthService;
import com.koreait.exam.tmrteamproject.service.MemberService;
import com.koreait.exam.tmrteamproject.service.NaverOAuthService;
import com.koreait.exam.tmrteamproject.service.SolapiSmsService;
import com.koreait.exam.tmrteamproject.vo.Rq;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

import java.io.UnsupportedEncodingException;
import java.math.BigInteger;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Map;

@Controller
@RequestMapping("usr/member")
@Slf4j
@RequiredArgsConstructor
public class MemberController {

    @Value("${kakao.api.clientId}")
    private String kakaoClientId;

    @Value("${naver.api.clientId}")
    private String naverClientId;

    @Autowired
    private KakaoOAuthService kakaoOAuthService;
    @Autowired
    private NaverOAuthService naverOAuthService;
    @Autowired
    private SolapiSmsService smsService;
    @Autowired
    private MemberService memberService;

    @Autowired
    private Rq rq;

    @GetMapping("/joinAndLogin")
    public String joinAndLogin() {

        return "member/joinAndLogin";
    }



    @PostMapping("/createAccount")
    public String createAccount(String name, String loginPw, String email, String phoneNum) {

        memberService.createAccount(name, loginPw, email, phoneNum);

        return "redirect:login";
    }

    @GetMapping("/loginKakao")
    public String loginKakao() {
        String kakaoRedirectUri = "http://localhost:8080/usr/member/kakaoCallback";

        return "redirect:https://kauth.kakao.com/oauth/authorize?response_type=code&client_id=" + kakaoClientId + "&redirect_uri=" + kakaoRedirectUri;
    }

    @GetMapping("/kakaoCallback")
    public String kakaoCallback(String code) {

        String accessToken = kakaoOAuthService.requestAccessToken(code);

        kakaoOAuthService.getUserInfo(accessToken);

//        rq.getSession().setAttribute("accessToken", accessToken);

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

        rq.logout();
//        if (rq.getSession().getAttribute("accessToken") != null) {
//            rq.getSession().removeAttribute("accessToken");
//            return "redirect:kakaoLogout";
//        }

        return "redirect:../home/main";
    }

    @GetMapping("/kakaoLogout")
    public String kakaoLogout() {

        String logoutRedirectUri = "http://localhost:8080/usr/home/main";
        String url = "https://kauth.kakao.com/oauth/logout?client_id=" + kakaoClientId + "&logout_redirect_uri="
                + URLEncoder.encode(logoutRedirectUri, StandardCharsets.UTF_8);
        return "redirect:" + url;

    }

    @PostMapping("/login-check")
    public ResponseEntity<?> loginCheck(@RequestBody Map<String, String> body) {
        String idToken = body.get("idToken");

        System.out.println(body);

        if (idToken == null) {
            return ResponseEntity.badRequest().body("idToken 누락됨");
        }

        try {
            FirebaseToken decodedToken = FirebaseAuth.getInstance().verifyIdToken(idToken);
            String uid = decodedToken.getUid();
            String email = decodedToken.getEmail();

            // ✅ 사용자 정보 처리 (회원 가입 또는 기존 사용자 확인)
            // 예시:
            // Optional<Member> member = memberRepository.findByUid(uid);
            // if (!member.isPresent()) -> 회원가입 로직 실행
            System.out.println("로그인 성공: UID = " + uid + ", email = " + email);
            return ResponseEntity.ok("로그인 성공: UID = " + uid + ", email = " + email);
        } catch (FirebaseAuthException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body("토큰 검증 실패: " + e.getMessage());
        }
    }
}
