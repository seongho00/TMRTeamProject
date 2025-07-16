package com.ltk.TMR.entity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import lombok.ToString;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Getter @Setter @ToString
@JsonIgnoreProperties(ignoreUnknown = true)
@Entity
@Table(name = "lh_apply_info")
public class LhApplyInfo {

    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "site_no", nullable = false)
    private Integer siteNo;
    
    @Column(name = "reg_date")    private LocalDateTime regDate;
    @Column(name = "update_date") private LocalDateTime updateDate;

    private String type;

    private String title;
    private String address;

    @Column(name = "post_date")     private LocalDate postDate;
    @Column(name = "deadline_date") private LocalDate deadlineDate;

    private String status;
    private Integer views;
    @Column(name = "call_number")   private String callNumber;

    @PrePersist void onCreate() { regDate = updateDate = LocalDateTime.now(); }
    @PreUpdate  void onUpdate() { updateDate = LocalDateTime.now(); }

    /* 편의 메서드 */
    public void updateFrom(LhApplyInfo src) {
        type         = src.type;
        address      = src.address;
        deadlineDate = src.deadlineDate;
        status       = src.status;
        views        = src.views;
        callNumber   = src.callNumber;
    }
}