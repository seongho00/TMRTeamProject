package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.vo.AddressApiResponse;
import com.koreait.exam.tmrteamproject.vo.NormalizedAddress;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AddressService {

    @Value("${address.confmKey}")
    private String confmKey;

    private final RestTemplate rest = new RestTemplate();

    // 금지 특수문자 / 제어문자 / 보이지 않는 공백(NBSP, ZWSP, FEFF)
    private static final Pattern BLOCK_CHARS =
            Pattern.compile("[%=><\\[\\]\"'`^|{}\\\\]");
    private static final Pattern CONTROL_CHARS =
            Pattern.compile("\\p{Cntrl}");
    private static final Pattern INVISIBLE =
            Pattern.compile("[\\u00A0\\u200B\\u200C\\uFEFF]");

    public List<NormalizedAddress> search(String keyword, int page, int size) {
        String cleaned = sanitizeKeyword(keyword);
        if (cleaned.length() < 2) {
            throw new IllegalArgumentException("검색어를 두 글자 이상, 특수문자 없이 입력하세요.");
        }

        // ✅ GET 대신 POST (x-www-form-urlencoded + UTF-8)
        MultiValueMap<String, String> form = new LinkedMultiValueMap<>();
        form.add("confmKey", confmKey);
        form.add("currentPage", String.valueOf(page));
        form.add("countPerPage", String.valueOf(size));
        form.add("keyword", cleaned);
        form.add("resultType", "json");

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);
        headers.setAccept(List.of(MediaType.APPLICATION_JSON));
        headers.setAcceptCharset(List.of(StandardCharsets.UTF_8));

        HttpEntity<MultiValueMap<String, String>> req = new HttpEntity<>(form, headers);

        AddressApiResponse res = rest.postForObject(
                "https://business.juso.go.kr/addrlink/addrLinkApi.do",
                req,
                AddressApiResponse.class
        );

        if (res == null || res.getResults() == null || res.getResults().getCommon() == null) {
            throw new IllegalStateException("Juso API 응답 비정상");
        }

        var common = res.getResults().getCommon();
        if (!"0".equals(common.getErrorCode())) {
            // ❗ 여기서 IllegalArgumentException으로 던져야 컨트롤러에서 400으로 변환됨
            throw new IllegalArgumentException("Juso API 오류: " + common.getErrorMessage());
        }

        var list = res.getResults().getJuso();
        if (list == null) return List.of();

        return list.stream().map(this::map).toList();
    }

    private String sanitizeKeyword(String keyword) {
        if (keyword == null) return "";
        String k = keyword.trim();
        k = CONTROL_CHARS.matcher(k).replaceAll(" ");
        k = INVISIBLE.matcher(k).replaceAll(" ");
        k = BLOCK_CHARS.matcher(k).replaceAll(" ");
        k = k.replaceAll("\\s+", " ");
        return k;
    }

    private NormalizedAddress map(AddressApiResponse.Juso j) {
        NormalizedAddress n = new NormalizedAddress();
        n.setRoadAddr(j.getRoadAddr());
        n.setJibunAddr(j.getJibunAddr());
        n.setZipNo(j.getZipNo());
        n.setLawdCd(j.getAdmCd());
        n.setRnMgtSn(j.getRnMgtSn());
        n.setBdMgtSn(j.getBdMgtSn());
        n.setSiNm(j.getSiNm());
        n.setSggNm(j.getSggNm());
        n.setEmdNm(j.getEmdNm());
        n.setRoadName(j.getRn());
        n.setBuldMnnm(parseInt(j.getBuldMnnm()));
        n.setBuldSlno(parseInt(j.getBuldSlno()));
        n.setJibunMain(parseInt(j.getLnbrMnnm()));
        n.setJibunSub(parseInt(j.getLnbrSlno()));
        if (n.getLawdCd() != null && n.getJibunMain() != null) {
            n.setAddressKey(String.format("%s-%d-%d",
                    n.getLawdCd(), n.getJibunMain(), (n.getJibunSub()==null?0:n.getJibunSub())));
        }
        return n;
    }

    private Integer parseInt(String s) {
        try { return (s == null || s.isBlank()) ? null : Integer.parseInt(s); }
        catch (Exception e) { return null; }
    }
}
