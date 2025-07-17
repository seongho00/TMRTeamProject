package com.koreait.exam.tmrteamproject.vo;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

public interface PopulationSummary {
    Integer getTotal();
    Integer getMale();
    Integer getFemale();
    Integer getAge10();
    Integer getAge20();
    Integer getAge30();
    Integer getAge40();
    Integer getAge50();
    Integer getAge60();
}
