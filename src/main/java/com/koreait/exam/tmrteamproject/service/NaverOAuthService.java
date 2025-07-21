package com.koreait.exam.tmrteamproject.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.firebase.auth.UserInfo;
import com.koreait.exam.tmrteamproject.vo.Member;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;

@Service
public class NaverOAuthService {

    @Value("${naver.api.clientId}")
    private String naverClientId;

    @Value("${naver.api.clientSecret}")
    private String naverClientSecret;

    public String requestAccessToken(String code, String state) throws UnsupportedEncodingException {

        String redirectURI = URLEncoder.encode("http://localhost:8080/usr/home/main", "UTF-8");

        String url = "https://nid.naver.com/oauth2.0/token" + "?grant_type=authorization_code" + "&client_id="
                + naverClientId + "&client_secret=" + naverClientSecret + "&redirect_uri=" + redirectURI + "&code=" + code
                + "&state=" + state;

        // 1. 헤더 설정
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

        // 2. 요청 생성 (GET 방식은 보통 파라미터만 넣음)
        HttpEntity<String> request = new HttpEntity<>(headers);

        // 3. RestTemplate로 요청
        RestTemplate restTemplate = new RestTemplate();
        ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, request, String.class);

        // 4. 응답 출력 및 반환
//		System.out.println("응답 코드: " + response.getStatusCode());
//		System.out.println("응답 바디: " + response.getBody());

        String accessToken = parseResponseBody(response.getBody());
//		System.out.println(accessToken);
        return accessToken; // 필요시 JSON 파싱 가능
    }

    public String parseResponseBody(String responseBody) {

        try {

            ObjectMapper objectMapper = new ObjectMapper();
            JsonNode root = objectMapper.readTree(responseBody);

            String naverAccessToken = root.path("access_token").asText();
            String tokenType = root.path("token_type").asText();
            String refreshToken = root.path("refresh_token").asText();
            int expiresIn = root.path("expires_in").asInt();

            return naverAccessToken;

        } catch (Exception e) {
            e.printStackTrace();
        }
        return "";
    }

    public Member getUserInfo(String accessToken) {
        String url = "https://openapi.naver.com/v1/nid/me";

        // 1. 헤더 구성
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(accessToken); // "Authorization: Bearer {accessToken}"
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

        HttpEntity<String> requestEntity = new HttpEntity<>(headers);

        // 2. 요청 실행
        RestTemplate restTemplate = new RestTemplate();
        ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, requestEntity, String.class);

        // 3. 응답 처리
//		System.out.println("응답 코드: " + response.getStatusCode());
        System.out.println("응답 바디: " + response.getBody());

        Member naverUser = parseUserResponseBody(response.getBody());

        return naverUser;
    }

    // 유저 데이터 까보기
    public Member parseUserResponseBody(String responseBody) {
        Member naverUser = null;
        try {

            ObjectMapper objectMapper = new ObjectMapper();
            JsonNode root = objectMapper.readTree(responseBody);

            String resultCode = root.path("resultcode").asText();
            String message = root.path("message").asText();
            String id = root.path("response").path("id").asText();
            String nickname = root.path("response").path("nickname").asText();
            String email = root.path("response").path("email").asText();
            String name = root.path("response").path("name").asText();
            String profileImage = root.path("response").path("profile_image").asText();
            String mobile = root.path("response").path("mobile").asText();

            System.out.println("resultCode: " + resultCode);
            System.out.println("message: " + message);
            System.out.println("id: " + id);
            System.out.println("nickname: " + nickname);
            System.out.println("email: " + email);
            System.out.println("name: " + name);
            System.out.println("profileImage: " + profileImage);
            System.out.println("mobile: " + mobile);

            naverUser = new Member("naver", name, "", email, mobile);

        } catch (Exception e) {
            e.printStackTrace();
        }
        return naverUser;
    }
}
