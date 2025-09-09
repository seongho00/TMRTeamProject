package com.koreait.exam.tmrteamproject.vo;

import lombok.*;
import lombok.experimental.SuperBuilder;

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
public class LhApplyInfo extends BaseEntity {

    private Integer listNo;                 // 번호
    private String postType;                // 유형
    private String name;                    // 공고명
    private String region;                  // 지역
    private boolean hasAttach;              // 첨부파일 유무
    private LocalDate postedDate;           // 공고일
    private LocalDate dueDate;              // 마감일
    private String status;                  // 상태
    private String linkEl;                  // link 추출용
    private LocalDateTime applyStart;       // 신청시작
    private LocalDateTime applyEnd;         // 신청마감
    private LocalDateTime resultTime;       // 결과 발표일
    private LocalDate contractStart;        // 계약 체결 시작
    private LocalDate contractEnd;          // 계약 체결 마감

    public void updateFrom(LhApplyInfo dto) {
        this.listNo = dto.getListNo();
        this.postType = dto.getPostType();
        this.name = dto.getName();
        this.region = dto.getRegion();
        this.hasAttach = dto.isHasAttach();
        this.postedDate = dto.getPostedDate();
        this.dueDate = dto.getDueDate();
        this.status = dto.getStatus();
        this.linkEl = dto.getLinkEl();
        this.applyStart = dto.getApplyStart();
        this.applyEnd = dto.getApplyEnd();
        this.resultTime = dto.getResultTime();
        this.contractStart = dto.getContractStart();
        this.contractEnd = dto.getContractEnd();
    }
}
