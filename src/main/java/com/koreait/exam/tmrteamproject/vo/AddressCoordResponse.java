package com.koreait.exam.tmrteamproject.vo;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter @Setter @NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class AddressCoordResponse {
    private Results results;

    @Getter @Setter public static class Results {
        private Common common;
        private List<Item> juso;
    }
    @Getter @Setter public static class Common {
        private String errorCode;     // "0" 정상
        private String errorMessage;
        private String totalCount;
    }
    @Getter @Setter public static class Item {
        private String admCd;
        private String rnMgtSn;
        private String bdMgtSn;
        private String udrtYn;
        private String buldMnnm;
        private String buldSlno;
        private String entX;     // ✅ 좌표
        private String entY;     // ✅ 좌표
        private String bdNm;     // (옵션)
        private String roadAddr; // (옵션)
    }
}
