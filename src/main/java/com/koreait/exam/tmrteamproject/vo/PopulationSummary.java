package com.koreait.exam.tmrteamproject.vo;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

public interface PopulationSummary {
    int getTotal();
    int getMale();
    int getFemale();
    int getAge10();
    int getAge20();
    int getAge30();
    int getAge40();
    int getAge50();
    int getAge60();
}
