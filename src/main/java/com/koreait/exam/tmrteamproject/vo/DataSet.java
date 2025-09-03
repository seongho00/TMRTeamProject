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
public class DataSet extends BaseEntity {

    // 기준_년분기_코드
    private String baseYearQuarterCode;
    // 행정동_코드
    private String adminDongCode;
    // 행정동_코드_명
    private String adminDongName;
    // 총_유동인구_수
    private Long totalFloatingPopulation;
    // 남성_유동인구_수
    private Long maleFloatingPopulation;
    // 여성_유동인구_수
    private Long femaleFloatingPopulation;
    // 연령대_10_유동인구_수
    private Long age10FloatingPopulation;
    // 연령대_20_유동인구_수
    private Long age20FloatingPopulation;
    // 연령대_30_유동인구_수
    private Long age30FloatingPopulation;
    // 연령대_40_유동인구_수
    private Long age40FloatingPopulation;
    // 연령대_50_유동인구_수
    private Long age50FloatingPopulation;
    // 연령대_60_이상_유동인구_수
    private Long age60PlusFloatingPopulation;
    // 시간대_00_06_유동인구_수
    private Long time00to06FloatingPopulation;
    // 시간대_06_11_유동인구_수
    private Long time06to11FloatingPopulation;
    // 시간대_11_14_유동인구_수
    private Long time11to14FloatingPopulation;
    // 시간대_14_17_유동인구_수
    private Long time14to17FloatingPopulation;
    // 시간대_17_21_유동인구_수
    private Long time17to21FloatingPopulation;
    // 시간대_21_24_유동인구_수
    private Long time21to24FloatingPopulation;
    // 월요일_유동인구_수
    private Long mondayFloatingPopulation;
    // 화요일_유동인구_수
    private Long tuesdayFloatingPopulation;
    // 수요일_유동인구_수
    private Long wednesdayFloatingPopulation;
    // 목요일_유동인구_수
    private Long thursdayFloatingPopulation;
    // 금요일_유동인구_수
    private Long fridayFloatingPopulation;
    // 토요일_유동인구_수
    private Long saturdayFloatingPopulation;
    // 일요일_유동인구_수
    private Long sundayFloatingPopulation;
    // 상권_변화_지표
    private String commercialChangeIndex;
    // 상권_변화_지표_명
    private String commercialChangeIndexName;
    // 운영_영업_개월_평균
    private Double avgOperatingMonths;
    // 폐업_영업_개월_평균
    private Double avgClosedMonths;
    // 서울_운영_영업_개월_평균
    private Double avgOperatingMonthsSeoul;
    // 서울_폐업_영업_개월_평균
    private Double avgClosedMonthsSeoul;
    // 총_상주인구_수
    private Long totalResidentPopulation;
    // 남성_상주인구_수
    private Long maleResidentPopulation;
    // 여성_상주인구_수
    private Long femaleResidentPopulation;
    // 연령대_10_상주인구_수
    private Long age10ResidentPopulation;
    // 연령대_20_상주인구_수
    private Long age20ResidentPopulation;
    // 연령대_30_상주인구_수
    private Long age30ResidentPopulation;
    // 연령대_40_상주인구_수
    private Long age40ResidentPopulation;
    // 연령대_50_상주인구_수
    private Long age50ResidentPopulation;
    // 연령대_60_이상_상주인구_수
    private Long age60PlusResidentPopulation;
    // 남성연령대_10_상주인구_수
    private Long maleAge10ResidentPopulation;
    // 남성연령대_20_상주인구_수
    private Long maleAge20ResidentPopulation;
    // 남성연령대_30_상주인구_수
    private Long maleAge30ResidentPopulation;
    // 남성연령대_40_상주인구_수
    private Long maleAge40ResidentPopulation;
    // 남성연령대_50_상주인구_수
    private Long maleAge50ResidentPopulation;
    // 남성연령대_60_이상_상주인구_수
    private Long maleAge60PlusResidentPopulation;
    // 여성연령대_10_상주인구_수
    private Long femaleAge10ResidentPopulation;
    // 여성연령대_20_상주인구_수
    private Long femaleAge20ResidentPopulation;
    // 여성연령대_30_상주인구_수
    private Long femaleAge30ResidentPopulation;
    // 여성연령대_40_상주인구_수
    private Long femaleAge40ResidentPopulation;
    // 여성연령대_50_상주인구_수
    private Long femaleAge50ResidentPopulation;
    // 여성연령대_60_이상_상주인구_수
    private Long femaleAge60PlusResidentPopulation;
    // 총_가구_수
    private Long totalHouseholds;
    // 아파트_가구_수
    private Long apartmentHouseholds;
    // 비_아파트_가구_수
    private Long nonApartmentHouseholds;
    // 월_평균_소득_금액
    private Long avgMonthlyIncome;
    // 소득_구간_코드
    private String incomeSectionCode;
    // 지출_총금액
    private Long totalExpenditure;
    // 식료품_지출_총금액
    private Long foodExpenditure;
    // 의류_신발_지출_총금액
    private Long clothingExpenditure;
    // 생활용품_지출_총금액
    private Long householdGoodsExpenditure;
    // 의료비_지출_총금액
    private Long medicalExpenditure;
    // 교통_지출_총금액
    private Long transportExpenditure;
    // 교육_지출_총금액
    private Long educationExpenditure;
    // 유흥_지출_총금액
    private Long entertainmentExpenditure;
    // 여가_문화_지출_총금액
    private Long leisureCultureExpenditure;
    // 기타_지출_총금액
    private Long otherExpenditure;
    // 음식_지출_총금액
    private Long diningExpenditure;
    // 총_직장_인구_수
    private Long totalWorkplacePopulation;
    // 남성_직장_인구_수
    private Long maleWorkplacePopulation;
    // 여성_직장_인구_수
    private Long femaleWorkplacePopulation;
    // 연령대_10_직장_인구_수
    private Long age10WorkplacePopulation;
    // 연령대_20_직장_인구_수
    private Long age20WorkplacePopulation;
    // 연령대_30_직장_인구_수
    private Long age30WorkplacePopulation;
    // 연령대_40_직장_인구_수
    private Long age40WorkplacePopulation;
    // 연령대_50_직장_인구_수
    private Long age50WorkplacePopulation;
    // 연령대_60_이상_직장_인구_수
    private Long age60PlusWorkplacePopulation;
    // 남성연령대_10_직장_인구_수
    private Long maleAge10WorkplacePopulation;
    // 남성연령대_20_직장_인구_수
    private Long maleAge20WorkplacePopulation;
    // 남성연령대_30_직장_인구_수
    private Long maleAge30WorkplacePopulation;
    // 남성연령대_40_직장_인구_수
    private Long maleAge40WorkplacePopulation;
    // 남성연령대_50_직장_인구_수
    private Long maleAge50WorkplacePopulation;
    // 남성연령대_60_이상_직장_인구_수
    private Long maleAge60PlusWorkplacePopulation;
    // 여성연령대_10_직장_인구_수
    private Long femaleAge10WorkplacePopulation;
    // 여성연령대_20_직장_인구_수
    private Long femaleAge20WorkplacePopulation;
    // 여성연령대_30_직장_인구_수
    private Long femaleAge30WorkplacePopulation;
    // 여성연령대_40_직장_인구_수
    private Long femaleAge40WorkplacePopulation;
    // 여성연령대_50_직장_인구_수
    private Long femaleAge50WorkplacePopulation;
    // 여성연령대_60_이상_직장_인구_수
    private Long femaleAge60PlusWorkplacePopulation;
    // 집객시설_수
    private Long attractingFacilityCount;
    // 관공서_수
    private Long governmentOfficeCount;
    // 은행_수
    private Long bankCount;
    // 종합병원_수
    private Long generalHospitalCount;
    // 일반_병원_수
    private Long hospitalCount;
    // 약국_수
    private Long pharmacyCount;
    // 유치원_수
    private Long kindergartenCount;
    // 초등학교_수
    private Long elementarySchoolCount;
    // 중학교_수
    private Long middleSchoolCount;
    // 고등학교_수
    private Long highSchoolCount;
    // 대학교_수
    private Long universityCount;
    // 백화점_수
    private Long departmentStoreCount;
    // 슈퍼마켓_수
    private Long supermarketCount;
    // 극장_수
    private Long theaterCount;
    // 숙박_시설_수
    private Long lodgingFacilityCount;
    // 공항_수
    private Long airportCount;
    // 철도_역_수
    private Long railwayStationCount;
    // 버스_터미널_수
    private Long busTerminalCount;
    // 지하철_역_수
    private Long subwayStationCount;
    // 버스_정거장_수
    private Long busStopCount;
    // 서비스_업종_코드
    private String serviceIndustryCode;
    // 서비스_업종_코드_명
    private String serviceIndustryName;
    // 점포_수
    private Long storeCount;
    // 유사_업종_점포_수
    private Long similarIndustryStoreCount;
    // 개업_율
    private Double openingRate;
    // 개업_점포_수
    private Long openingStoreCount;
    // 폐업_률
    private Double closingRate;
    // 폐업_점포_수
    private Long closingStoreCount;
    // 프랜차이즈_점포_수
    private Long franchiseStoreCount;
    // 당월_매출_금액
    private Long monthlySalesAmount;
    // 당월_매출_건수
    private Long monthlySalesCount;
    // 주중_매출_금액
    private Long weekdaySalesAmount;
    // 주말_매출_금액
    private Long weekendSalesAmount;
    // 월요일_매출_금액
    private Long mondaySalesAmount;
    // 화요일_매출_금액
    private Long tuesdaySalesAmount;
    // 수요일_매출_금액
    private Long wednesdaySalesAmount;
    // 목요일_매출_금액
    private Long thursdaySalesAmount;
    // 금요일_매출_금액
    private Long fridaySalesAmount;
    // 토요일_매출_금액
    private Long saturdaySalesAmount;
    // 일요일_매출_금액
    private Long sundaySalesAmount;
    // 시간대_00~06_매출_금액
    private Long time00to06SalesAmount;
    // 시간대_06~11_매출_금액
    private Long time06to11SalesAmount;
    // 시간대_11~14_매출_금액
    private Long time11to14SalesAmount;
    // 시간대_14~17_매출_금액
    private Long time14to17SalesAmount;
    // 시간대_17~21_매출_금액
    private Long time17to21SalesAmount;
    // 시간대_21~24_매출_금액
    private Long time21to24SalesAmount;
    // 남성_매출_금액
    private Long maleSalesAmount;
    // 여성_매출_금액
    private Long femaleSalesAmount;
    // 연령대_10_매출_금액
    private Long age10SalesAmount;
    // 연령대_20_매출_금액
    private Long age20SalesAmount;
    // 연령대_30_매출_금액
    private Long age30SalesAmount;
    // 연령대_40_매출_금액
    private Long age40SalesAmount;
    // 연령대_50_매출_금액
    private Long age50SalesAmount;
    // 연령대_60_이상_매출_금액
    private Long age60PlusSalesAmount;
    // 주중_매출_건수
    private Long weekdaySalesCount;
    // 주말_매출_건수
    private Long weekendSalesCount;
    // 월요일_매출_건수
    private Long mondaySalesCount;
    // 화요일_매출_건수
    private Long tuesdaySalesCount;
    // 수요일_매출_건수
    private Long wednesdaySalesCount;
    // 목요일_매출_건수
    private Long thursdaySalesCount;
    // 금요일_매출_건수
    private Long fridaySalesCount;
    // 토요일_매출_건수
    private Long saturdaySalesCount;
    // 일요일_매출_건수
    private Long sundaySalesCount;
    // 시간대_건수~06_매출_건수
    private Long time00to06SalesCount;
    // 시간대_건수~11_매출_건수
    private Long time06to11SalesCount;
    // 시간대_건수~14_매출_건수
    private Long time11to14SalesCount;
    // 시간대_건수~17_매출_건수
    private Long time14to17SalesCount;
    // 시간대_건수~21_매출_건수
    private Long time17to21SalesCount;
    // 시간대_건수~24_매출_건수
    private Long time21to24SalesCount;
    // 남성_매출_건수
    private Long maleSalesCount;
    // 여성_매출_건수
    private Long femaleSalesCount;
    // 연령대_10_매출_건수
    private Long age10SalesCount;
    // 연령대_20_매출_건수
    private Long age20SalesCount;
    // 연령대_30_매출_건수
    private Long age30SalesCount;
    // 연령대_40_매출_건수
    private Long age40SalesCount;
    // 연령대_50_매출_건수
    private Long age50SalesCount;
    // 연령대_60_이상_매출_건수
    private Long age60PlusSalesCount;

    // AS 컬럼
    private Long avg_floating;
}
