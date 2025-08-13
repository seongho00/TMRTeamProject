package com.koreait.exam.tmrteamproject.vo;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter @Setter @NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class AddressApiResponse {
    private Results results;

    @Getter @Setter @NoArgsConstructor
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Results {
        private Common common;
        private List<Juso> juso;   // ✅ 타입 수정
    }

    @Getter @Setter @NoArgsConstructor
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Common {
        private String errorCode;     // "0"이면 정상
        private String errorMessage;
        private String totalCount;
    }

    @Getter @Setter @NoArgsConstructor
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Juso {        // ✅ 클래스명 대문자 + public
        private String roadAddr;      // 표준 도로명주소
        private String jibunAddr;     // 표준 지번주소
        private String zipNo;         // 우편번호
        private String admCd;         // 법정동코드(10)
        private String rnMgtSn;       // 도로명코드
        private String bdMgtSn;       // 건물관리번호
        private String siNm, sggNm, emdNm, liNm, rn;
        private String buldMnnm, buldSlno;   // 건물번호 본/부번
        private String lnbrMnnm, lnbrSlno;   // 지번 본/부번
        private String bdNm, detBdNmList;
    }
}
