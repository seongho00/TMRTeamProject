package com.koreait.exam.tmrteamproject.vo;

import lombok.*;
import lombok.experimental.SuperBuilder;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;

@Entity
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@SuperBuilder
@ToString(callSuper = true)
public class Learning {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String yearQuarterCode;
    private String hjd_co;
    private String hjd_cn;

    private int totalFloatingPopulation;
    private int maleFloatingPopulation;
    private int femaleFloatingPopulation;
    private int age10FloatingPopulation;
    private int age20FloatingPopulation;
    private int age30FloatingPopulation;
    private int age40FloatingPopulation;
    private int age50FloatingPopulation;
    private int age60PlusFloatingPopulation;

    private int floatingPopulation_00_06;
    private int floatingPopulation_06_11;
    private int floatingPopulation_11_14;
    private int floatingPopulation_14_17;
    private int floatingPopulation_17_21;
    private int floatingPopulation_21_24;

    private int mondayFloatingPopulation;
    private int tuesdayFloatingPopulation;
    private int wednesdayFloatingPopulation;
    private int thursdayFloatingPopulation;
    private int fridayFloatingPopulation;
    private int saturdayFloatingPopulation;
    private int sundayFloatingPopulation;

    private long monthlySales;
    private long weekdaySales;
    private long weekendSales;

    private long salesMonday;
    private long salesTuesday;
    private long salesWednesday;
    private long salesThursday;
    private long salesFriday;
    private long salesSaturday;
    private long salesSunday;

    private long maleSales;
    private long femaleSales;
    private long salesAge10;
    private long salesAge20;
    private long salesAge30;
    private long salesAge40;
    private long salesAge50;
    private long salesAge60Plus;

    private int totalResidentPopulation;
    private int maleResidentPopulation;
    private int femaleResidentPopulation;
    private int residentAge10;
    private int residentAge20;
    private int residentAge30;
    private int residentAge40;
    private int residentAge50;
    private int residentAge60Plus;

    private int totalHouseholds;

    private long averageMonthlyIncome;
    private long totalSpending;
    private long foodSpending;
    private long clothingSpending;
    private long livingSuppliesSpending;
    private long medicalSpending;
    private long leisureSpending;
    private long cultureSpending;

    private int storeCount;
    private int franchiseStoreCount;
    private int newStoreCount;
    private int closedStoreCount;
    private int similarStoreCount;

    private float openingRate;
    private float closingRate;

    private int totalWorkPopulation;
    private int maleWorkPopulation;
    private int femaleWorkPopulation;
    private int workAge10;
    private int workAge20;
    private int workAge30;
    private int workAge40;
    private int workAge50;
    private int workAge60Plus;
}
