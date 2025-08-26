package com.koreait.exam.tmrteamproject.vo;

import lombok.*;
import lombok.experimental.SuperBuilder;

import javax.persistence.*;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
@Entity
@Table(name = "risk_score")
public class RiskScore {

    @Id
    @Column(name = "emd_cd")
    private String emdCd;

    @Column(name = "upjong_cd")
    private String upjongCd;

    @Column(name = "reg_date")
    private Double regDate;

    @Column(name = "update_date")
    private Double updateDate;

    @Column(name = "risk_raw")
    private Double riskRaw;

    @Column(name = "risk_label")
    private Integer riskLabel;

    @Column(name = "risk7_label")
    private String risk7Label;

    @Column(name = "risk_pred")
    private Integer riskPred;

    @Column(name = "risk100_all")
    private Double risk100All;

    @Column(name = "risk100_by_biz")
    private Double risk100ByBiz;

}
