package com.ltk.TMR.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "lh_apply_info")
@Getter
@Setter
@ToString
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class LhApplyInfo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 공고 고유번호
    @Column(name = "site_no", nullable = false)
    private Integer siteNo;

    // 등록/수정일 자동 생성
    @Column(name = "reg_date")
    private LocalDateTime regDate;
    @Column(name = "update_date")
    private LocalDateTime updateDate;

    // --- 크롤링 데이터 ---
    private String type;
    private String title;
    private String address;

    @Column(name = "post_date")
    private LocalDate postDate;
    @Column(name = "deadline_date")
    private LocalDate deadlineDate;

    private String status;
    private Integer views;

    @Column(name = "call_number")
    private String callNumber;

    // 첨부파일 정보를 JSON 문자열로 저장
    @Column(columnDefinition = "TEXT")
    private String attachmentsJson;

    // 화면(Thymeleaf)에서 사용하기 위한 임시 필드 (DB에는 저장 x)
    @Transient
    private List<AttachmentDto> attachments;


    @PrePersist
    void onCreate() {
        regDate = updateDate = LocalDateTime.now();
    }

    @PreUpdate
    void onUpdate() {
        updateDate = LocalDateTime.now();
    }

    // JSON 정보로 기존 엔티티 업데이트
    public void updateFrom(LhApplyInfo src) {
        this.type = src.type;
        this.address = src.address;
        this.deadlineDate = src.deadlineDate;
        this.status = src.status;
        this.views = src.views;
        this.callNumber = src.callNumber;
        // ★★★ 3. JSON 필드도 업데이트 되도록 추가 ★★★
        this.attachmentsJson = src.attachmentsJson;
    }

    // 첨부파일 정보를 담을 DTO
    @Getter @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    public static class AttachmentDto {
        private String name; // 파일명
        private String url;  // 다운로드 URL
    }
}