package com.koreait.exam.tmrteamproject.vo;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;

@Entity
@Getter
@Setter
@NoArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class AdminDong {
    @Id
    @Column(name = "admi_nm")
    private String admiNm;
    @Column(name = "sido_cd")
    private String sidoCd;
    @Column(name = "sido_nm")
    private String sidoNm;
    @Column(name = "sido_cd")
    private String sidoCd;
    @Column(name = "sgg_cd")
    private String sggCd;
    @Column(name = "sgg_nm")
    private String sggNm;
    @Column(name = "emd_cd")
    private String emdCd;
    @Column(name = "emd_nm")
    private String emdNm;
}
