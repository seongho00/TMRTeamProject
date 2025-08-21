package com.koreait.exam.tmrteamproject.vo;

import lombok.*;
import lombok.experimental.SuperBuilder;

import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
@ToString(callSuper=true)
public class DueAlert {

    // 팝업 창에 띄울 정보들
    // 알림 대상 일정 ID
    private long scheduleId;
    // 공고/일정 이름
    private String name;
    // 신청 시작일시
    private LocalDateTime applyStart;
    // 신청까지 남은 일수
    private int daysUtil;
}
