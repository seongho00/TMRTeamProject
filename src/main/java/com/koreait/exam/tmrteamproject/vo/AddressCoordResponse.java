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
        private String entX;  // 문자열로 옴
        private String entY;
        private String roadAddr; // (옵션) 디버깅용
        private String bdMgtSn;  // (옵션)
    }
}
