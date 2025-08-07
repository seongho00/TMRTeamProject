package com.koreait.exam.tmrteamproject.vo;

import lombok.*;
import lombok.experimental.SuperBuilder;

import javax.persistence.Entity;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class CommercialProperty extends BaseEntity {

    private String article_no;
    private String price_type;
    private String price;
    private String location;
    private double area_contract;
    private double area_real;
    private String floor_info;
    private String move_in_date;
    private int management_fee;
    private String parking;
    private String heating;
    private String purpose;
    private String use_approval_date;
    private String toilet_count;
    private String broker_name;
    private String broker_ceo;
    private String broker_address;
    private String broker_phone;

}
