package com.koreait.exam.tmrteamproject.vo;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

@Getter
@Setter
@NoArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class FlaskResult{

    private String intent;
    private double confidence;
    private String sido;
    private String sigungu;
    private String emd;
    private String gender;
    private String ageGroup;
    private String message;
}
