package com.koreait.exam.tmrteamproject.vo;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;

@Entity
@Getter
@Setter
@NoArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class PopulationStat extends BaseEntity {

    private String emd_cd;
    private int total;
    private int male ;
    private int female;
    private int age_10;
    private int age_20;
    private int age_30;
    private int age_40;
    private int age_50;
    private int age_60;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "emd_cd", referencedColumnName = "emd_cd", insertable = false, updatable = false)
    private AdminDong adminDong;

}
