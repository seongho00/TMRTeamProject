package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.vo.AddressApiResponse;
import com.koreait.exam.tmrteamproject.vo.NormalizedAddress;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.util.List;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AddressService {

    @Value("${address.confmKey}")     // ✅ application.yml 키와 일치해야 함
    private String confmKey;

    private final RestTemplate rest = new RestTemplate();

    // 금지 문자/키워드 패턴
    private static final Pattern BLOCK_CHARS =
            Pattern.compile("[%=><\\[\\]\"'`^|{}\\\\]");
    private static final Pattern CONTROL_CHARS =
            Pattern.compile("\\p{Cntrl}"); // 개행/탭 등
    private static final Pattern INVISIBLE =
            Pattern.compile("[\\u00A0\\u200B\\u200C\\uFEFF]"); // NBSP/제로폭/FEFF

    public List<NormalizedAddress> search(String keyword, int page, int size) {
        System.out.println(keyword);
        String cleaned = sanitizeKeyword(keyword);
        if (cleaned.length() < 2) {
            throw new IllegalArgumentException("검색어를 두 글자 이상, 특수문자 없이 입력하세요.");
        }

        String url = UriComponentsBuilder
                .fromHttpUrl("https://business.juso.go.kr/addrlink/addrLinkApi.do")
                .queryParam("confmKey", confmKey)
                .queryParam("currentPage", page)
                .queryParam("countPerPage", size)
                .queryParam("keyword", cleaned)
                .queryParam("resultType", "json")
                .toUriString();

        AddressApiResponse res = rest.getForObject(url, AddressApiResponse.class);
        if (res == null || res.getResults() == null || res.getResults().getCommon() == null)
            throw new IllegalStateException("Juso API 응답 비정상");

        var common = res.getResults().getCommon();
        if (!"0".equals(common.getErrorCode())) {
            throw new IllegalStateException("Juso API 오류: " + common.getErrorMessage());
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

    private NormalizedAddress map(AddressApiResponse.Juso j) {  // ✅ 타입 일치
        NormalizedAddress n = new NormalizedAddress();
        // ✅ 세터 사용 (필드가 private일 때 컴파일 문제 방지)
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
                    n.getLawdCd(), n.getJibunMain(), (n.getJibunSub() == null ? 0 : n.getJibunSub())));
        }
        return n;
    }

    private Integer parseInt(String s) {
        try {
            return (s == null || s.isBlank()) ? null : Integer.parseInt(s);
        } catch (Exception e) {
            return null;
        }
    }
}
