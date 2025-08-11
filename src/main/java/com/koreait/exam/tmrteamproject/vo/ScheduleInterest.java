package com.koreait.exam.tmrteamproject.vo;

import lombok.*;
import lombok.experimental.SuperBuilder;

import javax.persistence.Column;
import javax.persistence.Entity;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class ScheduleInterest extends BaseEntity {

    @Column(name = "member_id")
    private Long memberId;
    @Column(name = "schedule_id")
    private Long scheduleId;
    @Column(name = "is_active")
    private int isActive;
}
