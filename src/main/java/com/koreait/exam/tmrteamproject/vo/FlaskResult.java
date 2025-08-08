package com.koreait.exam.tmrteamproject.vo;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

import javax.persistence.Entity;

@Getter
@Setter
@NoArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class FlaskResult{

    private int intent;
    private double confidence;
    private String sido;
    private String sigungu;
    private String emd;
    private String gender;
    private String ageGroup;
    private String message;
    private String upjong_nm;
}
