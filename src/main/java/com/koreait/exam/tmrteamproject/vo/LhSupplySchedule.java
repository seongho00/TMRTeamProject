package com.koreait.exam.tmrteamproject.vo;


import com.fasterxml.jackson.databind.ser.Serializers;
import lombok.*;
import lombok.experimental.SuperBuilder;

import javax.persistence.Column;
import javax.persistence.Entity;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class LhSupplySchedule extends BaseEntity {

    private String name;
    @Column(name = "apply_start")
    private LocalDateTime applyStart;
    @Column(name = "apply_end")
    private LocalDateTime applyEnd;
    @Column(name = "result_time")
    private LocalDateTime resultTime;
    @Column(name = "contract_start")
    private LocalDate contractStart;
    @Column(name = "contract_end")
    private LocalDate contractEnd;
}
