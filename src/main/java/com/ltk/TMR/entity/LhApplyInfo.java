package com.ltk.TMR.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.ltk.TMR.entity.AttachmentDtoListConverter;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
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

    @Column(name = "site_no", nullable = false, unique = true)
    private Integer siteNo;

    @Column(name = "reg_date", updatable = false)
    private LocalDateTime regDate;

    @Column(name = "update_date")
    private LocalDateTime updateDate;

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

    @Lob
    @Column(name = "extracted_text", columnDefinition = "LONGTEXT")
    private String extractedText;

    @Lob
    @Column(name = "markdown_text", columnDefinition = "LONGTEXT")
    private String markdownText;

    @Enumerated(EnumType.STRING)
    @Column(name = "markdown_status", nullable = false)
    private MarkdownStatus markdownStatus = MarkdownStatus.PENDING;

    @Enumerated(EnumType.STRING)
    @Column(name = "processing_status", nullable = false)
    private LhProcessingStatus processingStatus = LhProcessingStatus.PENDING;

    @OneToMany(mappedBy = "lhApplyInfo", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<LhShopDetail> details = new ArrayList<>();

    @PrePersist
    protected void onCreate() {
        regDate = updateDate = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updateDate = LocalDateTime.now();
    }

    public void updateFrom(LhApplyInfo src) {
        this.type = src.type;
        this.address = src.address;
        this.postDate = src.postDate;
        this.deadlineDate = src.deadlineDate;
        this.status = src.status;
        this.views = src.views;
        this.callNumber = src.callNumber;
        this.attachments = src.attachments;
    }

    @Getter
    @Setter
    @ToString
    @NoArgsConstructor
    @AllArgsConstructor
    public static class AttachmentDto {
        private String name;
        private String url;
    }
}