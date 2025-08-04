package com.koreait.exam.tmrteamproject.vo;

import com.opencsv.bean.CsvBindByName;
import lombok.*;
import lombok.experimental.SuperBuilder;

import javax.persistence.Entity;

@Getter
@Setter
@NoArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class CommercialData{
    @CsvBindByName(column = "총_유동인구_수")
    private int total;

    @CsvBindByName(column = "남성_유동인구_수")
    private int male;

    @CsvBindByName(column = "여성_유동인구_수")
    private int female;

    @CsvBindByName(column = "연령대_10_유동인구_수")
    private int age10;

    @CsvBindByName(column = "연령대_20_유동인구_수")
    private int age20;

    @CsvBindByName(column = "연령대_30_유동인구_수")
    private int age30;

    @CsvBindByName(column = "연령대_40_유동인구_수")
    private int age40;

    @CsvBindByName(column = "연령대_50_유동인구_수")
    private int age50;

    @CsvBindByName(column = "연령대_60_이상_유동인구_수")
    private int age60plus;

}
