package com.koreait.exam.tmrteamproject.vo;

import javax.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

@Entity
@Table(name = "lh_shop_detail")
@Getter
@Setter
@NoArgsConstructor
@ToString(exclude = "lhApplyInfo") // 순환 참조 방지를 위해 ToString에서 제외
public class LhShopDetail {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "lh_apply_info_id")
    private LhApplyInfo lhApplyInfo;

    // ## 공급 유형 정보 ##
    @Column(name = "supply_type_detail")
    private String supplyTypeDetail;

    @Column(name = "complex_type")
    private String complexType;

    @Column(name = "shop_usage")
    private String shopUsage;

    // ## 위치 정보 ##
    private String dong;
    private String floor;
    private String ho;

    // ## 면적 정보 (단위: ㎡) ##
    @Column(name = "area_exclusive")
    private Double areaExclusive;

    @Column(name = "area_common")
    private Double areaCommon;

    // ▼▼▼ [추가된 필드] ▼▼▼
    @Column(name = "area_common_etc")
    private Double areaCommonEtc;
    // ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    @Column(name = "area_total")
    private Double areaTotal;

    @Column(name = "land_stake")
    private Double landStake;

    // ## 가격 정보 (단위: 원) ##
    private Long deposit;

    // ▼▼▼ [추가된 필드] ▼▼▼
    @Column(name = "deposit_down_payment")
    private Long depositDownPayment;

    @Column(name = "deposit_balance")
    private Long depositBalance;
    // ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    @Column(name = "rent_monthly")
    private Long rentMonthly;

    @Column(name = "price_estimated")
    private Long priceEstimated;

    @Column(name = "rent_total_period")
    private Long rentTotalPeriod;

    @Column(name = "rent_period_months")
    private Integer rentPeriodMonths;

    // 단지 및 기타 정보
    @Column(name = "housing_units")
    private Integer housingUnits;

    @Column(name = "capacity_personnel")
    private Integer capacityPersonnel;

    @Column(name = "move_in_date")
    private String moveInDate;

    private String remarks;
}
