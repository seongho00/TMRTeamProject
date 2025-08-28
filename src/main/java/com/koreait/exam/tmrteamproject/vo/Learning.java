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
@ToString(callSuper = true)
public class Learning {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String hjdCo;                   // 행정동_코드
    private String hjdCn;                   // 행정동_코드_명

    private String serviceTypeCode;         // 서비스_업종_코드
    private String serviceTypeName;         // 서비스_업종_코드_명

    private float riskScore;                // 위험도_점수

    private int riskLabel;                  // 실제_위험도
    private String riskLevel;               // 위험도_단계

    private int predictedRiskLabel;         // 예측_위험도
    private float predictedConfidence;      // 예측_신뢰도

    @Column(name = "risk100_all")
    private float risk100All;

    @Column(name = "risk100_by_biz")
    private float risk100ByBiz;
}
