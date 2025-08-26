package com.koreait.exam.tmrteamproject.vo;

import lombok.*;
import lombok.experimental.SuperBuilder;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import java.time.LocalDate;
import java.time.LocalDateTime;

import static javax.persistence.GenerationType.IDENTITY;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class LhSupplySchedule {

    @Id
    @GeneratedValue(strategy = IDENTITY)
    private Long id;
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
