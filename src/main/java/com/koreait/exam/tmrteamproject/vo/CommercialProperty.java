package com.koreait.exam.tmrteamproject.vo;

import lombok.*;
import lombok.experimental.SuperBuilder;

import javax.persistence.Column;
import javax.persistence.Entity;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class CommercialProperty extends BaseEntity {

    @Column(name = "article_no")
    private String articleNo;

    @Column(name = "price_type")
    private String priceType;

    private String price;

    private String location;

    @Column(name = "area_contract")
    private double areaContract;

    @Column(name = "area_real")
    private double areaReal;

    @Column(name = "floor_info")
    private String floorInfo;

    @Column(name = "move_in_date")
    private String moveInDate;

    @Column(name = "management_fee")
    private int managementFee;

    private String parking;

    private String heating;

    private String purpose;

    @Column(name = "use_approval_date")
    private String useApprovalDate;

    @Column(name = "toilet_count")
    private String toiletCount;

    @Column(name = "broker_name")
    private String brokerName;

    @Column(name = "broker_ceo")
    private String brokerCeo;

    @Column(name = "broker_address")
    private String brokerAddress;

    @Column(name = "broker_phone")
    private String brokerPhone;
}
