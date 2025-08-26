package com.koreait.exam.tmrteamproject.vo;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

// 우리 서비스에서 쓰는 정규화 스키마(간단)
@Getter
@Setter
@NoArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class NormalizedAddress {
    public String roadAddr, jibunAddr, zipNo;
    public String lawdCd, rnMgtSn, bdMgtSn;
    public String siNm, sggNm, emdNm, roadName;
    public Integer buldMnnm, buldSlno, jibunMain, jibunSub;
    public String addressKey; // lawdCd-jibunMain-jibunSub
    private Double lon;
    private Double lat;
    private Double entX;
    private Double entY;
    private String crs;    // "EPSG:5179" 등 표기

}
