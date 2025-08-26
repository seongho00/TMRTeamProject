package com.koreait.exam.tmrteamproject.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.koreait.exam.tmrteamproject.vo.Member;
import com.koreait.exam.tmrteamproject.vo.Rq;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.util.Map;

@Service
public class KakaoOAuthService {

    @Value("${kakao.api.clientId}")
    private String kakaoClientId;
    @Value("${kakao.api.clientSecret}")
    private String kakaoClientSecret;

    @Autowired
    private Rq rq;

    // 토큰 요청 함수
    public String requestAccessToken(String authorizationCode) {

        // 1. 요청 URL
        String url = "https://kauth.kakao.com/oauth/token";

        // 2. 파라미터 설정
        MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
        params.add("grant_type", "authorization_code");
        params.add("client_id", kakaoClientId);
        params.add("redirect_uri", "http://localhost:8080/usr/member/kakaoCallback");
        params.add("code", authorizationCode);
        params.add("client_secret", kakaoClientSecret);

        // 3. 헤더 설정
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
        headers.set("Accept-Charset", "UTF-8");

        // 4. 요청 조합
        HttpEntity<MultiValueMap<String, String>> request = new HttpEntity<>(params, headers);

        // 5. 요청 실행
        RestTemplate restTemplate = new RestTemplate();
        ResponseEntity<String> response = restTemplate.postForEntity(url, request, String.class);
        return parseResponseBody(response.getBody());

    }

    // 토큰 요청 데이터 까보기
    public String parseResponseBody(String responseBody) {

        try {

            ObjectMapper objectMapper = new ObjectMapper();
            JsonNode root = objectMapper.readTree(responseBody);

            String kakaoAccessToken = root.path("access_token").asText();
            String tokenType = root.path("token_type").asText();
            String idToken = root.path("id_token").asText();
            String scope = root.path("scope").asText();
            String refreshToken = root.path("refresh_token").asText();
            int expiresIn = root.path("expires_in").asInt();
            int refreshTokenExpiresIn = root.path("refresh_token_expires_in").asInt();

            return kakaoAccessToken;

        } catch (Exception e) {
            e.printStackTrace();
        }
        return "";
    }

    // 토큰을 통해 유저 데이터 요청
    public Member getUserInfo(String accessToken) {
        String url = "https://kapi.kakao.com/v2/user/me?secure_resource=true";

        // 1. 헤더 설정
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(accessToken); // "Authorization: Bearer {토큰}"
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

        HttpEntity<String> entity = new HttpEntity<>(headers);

        // 2. RestTemplate으로 GET 요청
        RestTemplate restTemplate = new RestTemplate();
        ResponseEntity<String> response = restTemplate.exchange(url, HttpMethod.GET, entity, String.class);

        // 3. 응답 출력
        System.out.println("응답 상태: " + response.getStatusCode());
        System.out.println("응답 바디: " + response.getBody());
        Member member = parseUserResponseBody(response.getBody());
        return member;
    }

    // 유저 데이터 까보기
    public Member parseUserResponseBody(String responseBody) {
        Member member = null;
        try {

            ObjectMapper objectMapper = new ObjectMapper();
            JsonNode root = objectMapper.readTree(responseBody);

            String id = root.path("id").asText();
            String connectedAt = root.path("connected_at").asText();
            String nickname = root.path("properties").path("nickname").asText();
            String profileImage = root.path("properties").path("profile_image").asText();
            String thumbnailImage = root.path("properties").path("thumbnail_image").asText();
            String email = root.path("kakao_account").path("email").asText();
            String phoneNumber = root.path("kakao_account").path("phone_number").asText();

            System.out.println("id: " + id);
            System.out.println("connectedAt: " + connectedAt);
            System.out.println("nickname: " + nickname);
            System.out.println("profileImage: " + profileImage);
            System.out.println("thumbnailImage: " + thumbnailImage);
            System.out.println("email: " + email);
            System.out.println("phoneNumber: " + phoneNumber);

            member = new Member("kakao", nickname, "", email, phoneNumber);
        } catch (Exception e) {
            e.printStackTrace();
        }

        return member;
    }

    public Map<String, Object> searchActualUsage(double lat, double lon) {
        String url = UriComponentsBuilder
                .fromHttpUrl("https://dapi.kakao.com/v2/local/search/category.json")
                .queryParam("category_group_code", "FD6")  // 예: 음식점
                .queryParam("x", lon)
                .queryParam("y", lat)
                .queryParam("radius", 0) // 반경 50m
                .queryParam("sort", "distance")
                .build(true)
                .toUriString();

        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", "KakaoAK " + kakaoClientId);

        RestTemplate rest = new RestTemplate();
        HttpEntity<String> entity = new HttpEntity<>(headers);

        ResponseEntity<Map> res = rest.exchange(url, HttpMethod.GET, entity, Map.class);
        System.out.println(res.getBody());
        return res.getBody(); // 여기 안에 place_name, category_group_name, address_name 등 들어있음
    }
}
