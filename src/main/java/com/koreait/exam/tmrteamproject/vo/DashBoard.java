package com.koreait.exam.tmrteamproject.vo;

import lombok.*;
import lombok.experimental.SuperBuilder;

@Getter
@Setter
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@ToString(callSuper = true)
public class DashBoard {

    // 기준_년분기_코드
    private String baseYearQuarterCode;
    // 행정동_코드
    private String adminDongCode;
    // 행정동_코드_명
    private String adminDongName;
    // 총_유동인구_수
    private Long totalFloatingPopulation;
    // 당월_매출_금액
    private Long monthlySalesAmount;

    private int footPercent;          // 도넛 퍼센트(0~100)
    private int salesPercent;         // 도넛 퍼센트(0~100)
}
