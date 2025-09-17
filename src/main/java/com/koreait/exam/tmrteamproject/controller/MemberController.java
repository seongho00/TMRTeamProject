package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.security.MemberContext;
import com.koreait.exam.tmrteamproject.service.KakaoOAuthService;
import com.koreait.exam.tmrteamproject.service.MemberService;
import com.koreait.exam.tmrteamproject.service.NaverOAuthService;
import com.koreait.exam.tmrteamproject.util.Ut;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import com.koreait.exam.tmrteamproject.vo.Rq;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletRequest;
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
    private MemberService memberService;

    @Autowired
    private Rq rq;
    @Autowired
    private PasswordEncoder passwordEncoder;

    @GetMapping("/joinAndLogin")
    public String joinAndLogin() {

        return "member/joinAndLogin";
    }

    @PostMapping("/createAccount")
    @ResponseBody
    public String createAccount(String name, String loginPw, String email, String phoneNum) {

        // 겹치는 이메일 있는지 확인
        ResultData checkDupMemberRd = memberService.checkDupMemberByEmail(email);

        if (checkDupMemberRd.isFail()) {
            return Ut.jsHistoryBack("F-1", "가입된 이메일이 있습니다.");
        }

        memberService.createAccount("local", name, loginPw, email, phoneNum);

        return Ut.jsReplace("S-1", name + "님 가입을 환영합니다.", "joinAndLogin");

    }

    @GetMapping("/login")
    @ResponseBody
    public String loginPage(HttpServletRequest request) {
        Object errorMessage = request.getSession().getAttribute("errorMessage");
        System.out.println(errorMessage);

        if (errorMessage != null) {
            request.getSession().removeAttribute("errorMessage");
            return Ut.jsHistoryBack("F-1", errorMessage.toString());
        }
        return "redirect:../home/main";
    }

    @PostMapping("/doLogin")
    public String doLogin(@RequestParam String email, @RequestParam String loginPw) {

        Member member = memberService.getMemberByProviderAndEmail("local", email);

        if (member == null) {
            return Ut.jsHistoryBack("F-1", "가입되지 않은 이메일입니다.");
        }
        if (!"local".equals(member.getProvider())) {
            // 소셜 계정이면 여기서 차단
            return Ut.jsHistoryBack("F-2", "소셜 계정입니다. 소셜 로그인을 사용하세요.");
        }

        // 비밀번호 검증
        if (Ut.isEmptyOrNull(member.getLoginPw()) || !passwordEncoder.matches(loginPw, member.getLoginPw())) {
            return Ut.jsHistoryBack("F-3", "비밀번호가 일치하지 않습니다.");
        }

        // SecurityContext에 사용자 로그인 처리
        MemberContext memberContext = new MemberContext(member);
        Authentication auth = new UsernamePasswordAuthenticationToken(memberContext, null, memberContext.getAuthorities());
        SecurityContextHolder.getContext().setAuthentication(auth);

        // 이동
        return "redirect:../home/main";
    }

    @GetMapping("/loginKakao")
    public String loginKakao() {
        String kakaoRedirectUri = "http://localhost:8080/usr/member/kakaoCallback";

        return "redirect:https://kauth.kakao.com/oauth/authorize?response_type=code&client_id=" + kakaoClientId + "&redirect_uri=" + kakaoRedirectUri;
    }

    @GetMapping("/kakaoCallback")
    public String kakaoCallback(String code) {

        String accessToken = kakaoOAuthService.requestAccessToken(code);

        Member kakaoUser = kakaoOAuthService.getUserInfo(accessToken);

        String kakaoEmail = kakaoUser.getEmail();

        // 1. DB에 사용자 있는지 확인 (없으면 회원가입 처리)
        Member member = memberService.getMemberByProviderAndEmail("kakao", kakaoEmail); // 없으면 생성해서 리턴
        if (member == null) {
            memberService.createAccount("kakao", kakaoUser.getName(), kakaoUser.getLoginPw(), kakaoUser.getEmail(), kakaoUser.getPhoneNum());
            member = memberService.getMemberByProviderAndEmail("kakao", kakaoEmail);
        }

        // 2. SecurityContext에 사용자 로그인 처리
        MemberContext memberContext = new MemberContext(member);
        Authentication auth = new UsernamePasswordAuthenticationToken(memberContext, null, memberContext.getAuthorities());
        SecurityContextHolder.getContext().setAuthentication(auth);

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

        Member naverUser = naverOAuthService.getUserInfo(accessToken);

        String naverEmail = naverUser.getEmail();

        // 1. DB에 사용자 있는지 확인 (없으면 회원가입 처리)
        Member member = memberService.getMemberByProviderAndEmail("naver", naverEmail); // 없으면 생성해서 리턴
        if (member == null) {
            memberService.createAccount("naver", naverUser.getName(), naverUser.getLoginPw(), naverUser.getEmail(), naverUser.getPhoneNum());
            member = memberService.getMemberByProviderAndEmail("naver", naverEmail);
        }

        // 2. SecurityContext에 사용자 로그인 처리
        MemberContext memberContext = new MemberContext(member);
        Authentication auth = new UsernamePasswordAuthenticationToken(memberContext, null, memberContext.getAuthorities());
        SecurityContextHolder.getContext().setAuthentication(auth);

        return "redirect:../home/main";
    }

    @GetMapping("/conditionalLogout")
    public String conditionalLogout() {

        Authentication auth = SecurityContextHolder.getContext().getAuthentication();

        if (auth != null && auth.getPrincipal() instanceof MemberContext) {
            MemberContext memberContext = (MemberContext) auth.getPrincipal();
            String provider = memberContext.getMember().getProvider(); // "kakao", "local" 등

            if ("kakao".equals(provider)) {
                // ✅ 카카오 로그아웃 URL로 리디렉션
                String logoutRedirectUri = "http://localhost:8080/usr/member/doLogout";
                String url = "https://kauth.kakao.com/oauth/logout?client_id=" + kakaoClientId
                        + "&logout_redirect_uri=" + URLEncoder.encode(logoutRedirectUri, StandardCharsets.UTF_8);

                return "redirect:" + url;
            }

        }

        // ✅ 일반 로그아웃 처리
        return "redirect:/usr/member/doLogout";
    }

    // 구글 로그인 체크
    @PostMapping("/googleCallback")
    @ResponseBody
    public ResultData googleCallback(@RequestBody Map<String, String> body) {
        String idToken = body.get("idToken");
        String name = body.get("name");
        String email = body.get("email");
        String phone = body.get("phone");
        String photoUrl = body.get("photoUrl");

        System.out.println("idToken: " + idToken);
        System.out.println("name: " + name);
        System.out.println("email: " + email);
        System.out.println("phone: " + phone);
        System.out.println("photoUrl: " + photoUrl);


        // 1. DB에 해당 이메일이 있는지 확인
        Member member = memberService.getMemberByProviderAndEmail("google", email);

        if (member == null) {
            // 없으면 회원가입 처리
            memberService.createAccount("google", name, "", email, phone); // 커스텀 로직 작성 필요
            member = memberService.getMemberByProviderAndEmail("google", email);
        }

        // 2. SecurityContext에 사용자 로그인 처리
        MemberContext memberContext = new MemberContext(member);
        Authentication auth = new UsernamePasswordAuthenticationToken(memberContext, null, memberContext.getAuthorities());
        SecurityContextHolder.getContext().setAuthentication(auth);

        return ResultData.from("S-1", "구글 로그인 성공", "구글 멤버", member);

    }

    @GetMapping("/myPage")
    public String profile(Model model) {

        Member member = memberService.getMemberById(rq.getLoginedMemberId());
        model.addAttribute("member", member);

        return "member/myPage";
    }

    @GetMapping("/checkPw")
    public String checkPw() {
        return "member/checkPw";
    }

    @GetMapping("/doCheckPw")
    @ResponseBody
    public String doCheckPw(String pw) {
        if (Ut.isEmptyOrNull(pw)) {
            return Ut.jsHistoryBack("F-1", "비번 써");
        }

        if (!rq.getLoginedMember().getLoginPw().equals(pw)) {
            return Ut.jsHistoryBack("F-2", "비번 틀림");
        }

        return Ut.jsReplace("S-1", Ut.f("비밀번호 확인 성공"), "modify");
    }

    @GetMapping("/doModify")
    @ResponseBody
    public String doModify(String loginPw, String name, String phoneNum, String email) {

        // 비번은 안바꾸는거 가능(사용자) 비번 null 체크는 x
        if (Ut.isEmptyOrNull(name)) {
            return Ut.jsHistoryBack("F-3", "이름 입력 x");
        }
        if (Ut.isEmptyOrNull(phoneNum)) {
            return Ut.jsHistoryBack("F-5", "전화번호 입력 x");
        }
        if (Ut.isEmptyOrNull(email)) {
            return Ut.jsHistoryBack("F-6", "이메일 입력 x");
        }

        ResultData modifyRd;

        if (Ut.isEmptyOrNull(loginPw)) {
            modifyRd = memberService.modifyWithoutPw(rq.getLoginedMemberId(), name, phoneNum, email);
        } else {
            modifyRd = memberService.modify(rq.getLoginedMemberId(), loginPw, name, phoneNum, email);
        }

        return Ut.jsReplace(modifyRd.getResultCode(), modifyRd.getMsg(), "../member/myPage");
    }
}
