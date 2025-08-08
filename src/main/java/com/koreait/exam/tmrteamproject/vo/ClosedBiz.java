package com.koreait.exam.tmrteamproject.vo;

import lombok.*;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Table;

import static javax.persistence.GenerationType.IDENTITY;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@ToString(callSuper = true)
@Table(name = "closed_biz")
public class ClosedBiz {

    @Id
    @GeneratedValue(strategy = IDENTITY)
    private Long id;

    private String dongName;
    private String upjongType;
    private String closeYm;
    private String closeCount;
}
