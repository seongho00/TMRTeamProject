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
public class UpjongCode {
    @Id
    @Column(name = "minor_cd")
    private String minorCd;

    @Column(name = "major_cd")
    private String majorCd;
    @Column(name = "major_nm")
    private String majorNm;
    @Column(name = "middle_cd")
    private String middleCd;
    @Column(name = "middle_nm")
    private String middleNm;
    @Column(name = "minor_nm")
    private String minorNm;
}