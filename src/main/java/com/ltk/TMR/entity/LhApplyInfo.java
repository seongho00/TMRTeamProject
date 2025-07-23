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

    // 고유번호
    @Column(name = "site_no", nullable = false, unique = true)
    private Integer siteNo;

    // 등록/수정일 자동 생성
    @Column(name = "reg_date", updatable = false)
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

    @Column(columnDefinition = "TEXT")
    @Convert(converter = AttachmentDtoListConverter.class)
    private List<AttachmentDto> attachments;

    // PDF 추출 텍스트 저장
    @Lob // 대용량 텍스트를 위한 어노테이션
    @Column(name = "extracted_text", columnDefinition = "LONGTEXT")
    private String extractedText;


    @PrePersist
    protected void onCreate() {
        regDate = updateDate = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updateDate = LocalDateTime.now();
    }

    /**
     * 최신 정보로 엔티티 내용을 업데이트
     * @param src 크롤링 결과로 생성된 엔티티 객체
     */
    public void updateFrom(LhApplyInfo src) {
        this.type = src.type;
        this.address = src.address;
        this.postDate = src.postDate; // postDate 추가
        this.deadlineDate = src.deadlineDate;
        this.status = src.status;
        this.views = src.views;
        this.callNumber = src.callNumber;
        this.attachments = src.attachments;
        // extractedText는 별도의 PDF 처리 프로세스에서 업데이트, 여기엔 포함 X
    }

    /**
     * 첨부파일 정보를 담기 위한 내부 DTO 클래스
     */
    @Getter
    @Setter
    @ToString
    @NoArgsConstructor
    @AllArgsConstructor
    public static class AttachmentDto {
        private String name; // 파일명
        private String url;  // 다운로드 URL
    }
}