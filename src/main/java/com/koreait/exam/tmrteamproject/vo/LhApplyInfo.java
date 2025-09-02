package com.koreait.exam.tmrteamproject.vo;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import javax.persistence.*;

import com.koreait.exam.tmrteamproject.entity.AttachmentDtoListConverter;
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
public class LhApplyInfo extends BaseEntity {

    @Column(name = "site_no", nullable = false, unique = true)
    private Integer siteNo;

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
