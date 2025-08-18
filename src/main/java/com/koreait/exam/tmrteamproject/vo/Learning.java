package com.koreait.exam.tmrteamproject.vo;

import lombok.*;
import lombok.experimental.SuperBuilder;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;

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

    private String hjdCo;                 // 행정동_코드
    private String hjdCn;                 // 행정동_코드_명

    private String serviceTypeCode;       // 서비스_업종_코드
    private String serviceTypeName;       // 서비스_업종_코드_명

    private float riskScore;             // 위험도_점수

    private int riskLabel;              // 실제_위험도
    private String riskLevel;           // 위험도_단계

    private int predictedRiskLabel;     // 예측_위험도
    private float predictedConfidence;  // 예측_신뢰도
}
