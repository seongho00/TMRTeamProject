package com.koreait.exam.tmrteamproject.vo;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import javax.persistence.*;

import com.koreait.exam.tmrteamproject.entity.AttachmentDtoListConverter;
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

    @Column(columnDefinition = "TEXT")
    @Convert(converter = AttachmentDtoListConverter.class)
    private List<AttachmentDto> attachments;

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
