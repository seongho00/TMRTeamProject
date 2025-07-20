package com.koreait.exam.tmrteamproject.vo;

import lombok.*;
import lombok.experimental.SuperBuilder;

import javax.persistence.*;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
@ToString
public class TradeArea {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String regionName;         // 지역명 (파일명에서 추출)
    private String industry;           // 업종 (파일명에서 추출)

    private int storeCount;            // 업소 수
    private double storeCountYoyChange; // 업소수 전년동월대비 증감률

    private int footTraffic;           // 유동인구
    private int monthlySales;          // 월평균 매출

    private double salesYoyChange;     // 매출 전년동월대비
    private double salesMomChange;     // 매출 전월대비

    private String peakDay;            // 피크 요일
    private String peakTime;           // 피크 시간대
}
