package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.DataSetRepository;
import com.koreait.exam.tmrteamproject.vo.DashBoard;
import com.koreait.exam.tmrteamproject.vo.DataSet;
import com.opencsv.CSVReaderHeaderAware;
import com.opencsv.exceptions.CsvValidationException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Stream;

@Slf4j
@Service
@RequiredArgsConstructor
public class DataSetService {

    private final DataSetRepository dataSetRepository;

    // 폴더 읽기
    public int saveAllFromDir(String csvDir) {
        int totalSaved = 0;

        try (Stream<Path> paths = Files.walk(Paths.get(csvDir))) {
            for (Path file : paths
                    .filter(Files::isRegularFile)
                    .filter(f -> f.toString().toLowerCase().endsWith(".csv"))
                    .toList()) {
                totalSaved += saveOneFileInTx(file);
            }
        } catch (IOException e) {
            throw new RuntimeException("CSV 디렉토리 읽기 실패: " + csvDir, e);
        }

        return totalSaved;
    }

    @Async
    public CompletableFuture<Integer> saveAllFromDirAsync(String csvDir) {
        int saved = saveAllFromDir(csvDir);
        return CompletableFuture.completedFuture(saved);
    }

    // 파일 하나씩 처리
    public int saveOneFileInTx(Path csvFile) {
        final int BATCH_SIZE = 1000; // 필요에 따라 조절
        int savedCount = 0;
        List<DataSet> buffer = new ArrayList<>(BATCH_SIZE);

        try (Reader reader = Files.newBufferedReader(csvFile, StandardCharsets.UTF_8);
             CSVReaderHeaderAware csvReader = new CSVReaderHeaderAware(reader)) {

            Map<String, String> raw;
            while ((raw = csvReader.readMap()) != null) {
                // CSV → Entity 매핑
                DataSet entity = mapRowToEntity(normalizeRowKeys(raw));
                buffer.add(entity);

                if (buffer.size() >= BATCH_SIZE) {
                    savedCount += saveBatchSkippingDuplicates(buffer);
                    buffer.clear();
                }
            }

            if (!buffer.isEmpty()) {
                savedCount += saveBatchSkippingDuplicates(buffer);
                buffer.clear();
            }

        } catch (IOException | CsvValidationException e) {
            throw new RuntimeException("CSV 읽기 실패: " + csvFile, e);
        }

        return savedCount;
    }

    private static String compositeKeyOf(DataSet e) {
        return (e.getBaseYearQuarterCode() == null ? "" : e.getBaseYearQuarterCode()) + "|" +
                (e.getAdminDongCode()        == null ? "" : e.getAdminDongCode())        + "|" +
                (e.getServiceIndustryCode()  == null ? "" : e.getServiceIndustryCode());
    }

    private int saveBatchSkippingDuplicates(List<DataSet> batch) {
        // (1) 파일 내부 중복 제거(동일 키가 여러 번 등장 시 마지막 행만 남김)
        Map<String, DataSet> uniq = new LinkedHashMap<>();
        for (DataSet e : batch) uniq.put(compositeKeyOf(e), e);

        // (2) DB에 이미 있는 키 한번에 조회
        List<String> existingKeys = dataSetRepository.findExistingKeys(uniq.keySet());
        Set<String> existing = new java.util.HashSet<>(existingKeys);

        // (3) 신규만 추려서 저장
        List<DataSet> toInsert = uniq.entrySet().stream()
                .filter(en -> !existing.contains(en.getKey()))
                .map(Map.Entry::getValue)
                .toList();

        if (!toInsert.isEmpty()) dataSetRepository.saveAll(toInsert);
        return toInsert.size();
    }

    private static String normalizeKey(String k) {
        if (k == null) return "";
        // BOM 제거
        return k
                .replace("\uFEFF", "")   // BOM
                .trim();
    }

    private static Map<String, String> normalizeRowKeys(Map<String, String> row) {
        Map<String, String> fixed = new LinkedHashMap<>();
        for (Map.Entry<String, String> e : row.entrySet()) {
            String nk = normalizeKey(e.getKey());
            fixed.put(nk, e.getValue());
        }
        return fixed;
    }

    // long 파싱
    private static long parseLongSafe(String v) {
        if (v == null) return 0L;
        v = v.trim().replace(",", "").replace("\u00A0", "");
        if (v.isEmpty() || v.equalsIgnoreCase("NaN")) return 0L;
        try {
            if (v.contains(".") || v.contains("e") || v.contains("E")) {
                double d = Double.parseDouble(v);
                return Math.round(d);  // 반올림해서 정수화
            }
            return Long.parseLong(v);
        } catch (NumberFormatException e) {
            // 마지막 방어: double로 파싱 시도 후 반올림
            try {
                return Math.round(Double.parseDouble(v));
            } catch (Exception ignore) {
                return 0L;
            }
        }
    }

    // double 파싱
    private static double parseDoubleSafe(String v) {
        if (v == null) return 0.0;
        v = v.replace(",", "").trim();
        if (v.isEmpty() || v.equalsIgnoreCase("NaN")) return 0.0;
        try {
            return Double.parseDouble(v);
        } catch (NumberFormatException e) {
            return 0.0;
        }
    }

    private static String getS(Map<String, String> row, String key) {
        String v = row.get(normalizeKey(key));
        return v == null ? "" : v.trim();
    }

    private static long getL(Map<String, String> row, String key) {
        return parseLongSafe(row.get(normalizeKey(key)));
    }

    private static double getD(Map<String, String> row, String key) {
        return parseDoubleSafe(row.get(normalizeKey(key)));
    }

    // 매핑
    private DataSet mapRowToEntity(Map<String, String> row) {
        return DataSet.builder()
                .baseYearQuarterCode(getS(row, "기준_년분기_코드"))
                .adminDongCode(getS(row, "행정동_코드"))
                .adminDongName(getS(row,"행정동_코드_명"))
                .totalFloatingPopulation(getL(row,"총_유동인구_수"))
                .maleFloatingPopulation(getL(row,"남성_유동인구_수"))
                .femaleFloatingPopulation(getL(row,"여성_유동인구_수"))
                .age10FloatingPopulation(getL(row,"연령대_10_유동인구_수"))
                .age20FloatingPopulation(getL(row,"연령대_20_유동인구_수"))
                .age30FloatingPopulation(getL(row,"연령대_30_유동인구_수"))
                .age40FloatingPopulation(getL(row,"연령대_40_유동인구_수"))
                .age50FloatingPopulation(getL(row,"연령대_50_유동인구_수"))
                .age60PlusFloatingPopulation(getL(row,"연령대_60_이상_유동인구_수"))
                .time00to06FloatingPopulation(getL(row,"시간대_00_06_유동인구_수"))
                .time06to11FloatingPopulation(getL(row,"시간대_06_11_유동인구_수"))
                .time11to14FloatingPopulation(getL(row,"시간대_11_14_유동인구_수"))
                .time14to17FloatingPopulation(getL(row,"시간대_14_17_유동인구_수"))
                .time17to21FloatingPopulation(getL(row,"시간대_17_21_유동인구_수"))
                .time21to24FloatingPopulation(getL(row,"시간대_21_24_유동인구_수"))
                .mondayFloatingPopulation(getL(row,"월요일_유동인구_수"))
                .tuesdayFloatingPopulation(getL(row,"화요일_유동인구_수"))
                .wednesdayFloatingPopulation(getL(row,"수요일_유동인구_수"))
                .thursdayFloatingPopulation(getL(row,"목요일_유동인구_수"))
                .fridayFloatingPopulation(getL(row,"금요일_유동인구_수"))
                .saturdayFloatingPopulation(getL(row,"토요일_유동인구_수"))
                .sundayFloatingPopulation(getL(row,"일요일_유동인구_수"))
                .commercialChangeIndex(getS(row,"상권_변화_지표"))
                .commercialChangeIndexName(getS(row,"상권_변화_지표_명"))
                .avgOperatingMonths(getD(row,"운영_영업_개월_평균"))
                .avgClosedMonths(getD(row,"폐업_영업_개월_평균"))
                .avgOperatingMonthsSeoul(getD(row,"서울_운영_영업_개월_평균"))
                .avgClosedMonthsSeoul(getD(row,"서울_폐업_영업_개월_평균"))
                .totalResidentPopulation(getL(row,"총_상주인구_수"))
                .maleResidentPopulation(getL(row,"남성_상주인구_수"))
                .femaleResidentPopulation(getL(row,"여성_상주인구_수"))
                .age10ResidentPopulation(getL(row,"연령대_10_상주인구_수"))
                .age20ResidentPopulation(getL(row,"연령대_20_상주인구_수"))
                .age30ResidentPopulation(getL(row,"연령대_30_상주인구_수"))
                .age40ResidentPopulation(getL(row,"연령대_40_상주인구_수"))
                .age50ResidentPopulation(getL(row,"연령대_50_상주인구_수"))
                .age60PlusResidentPopulation(getL(row,"연령대_60_이상_상주인구_수"))
                .maleAge10ResidentPopulation(getL(row,"남성연령대_10_상주인구_수"))
                .maleAge20ResidentPopulation(getL(row,"남성연령대_20_상주인구_수"))
                .maleAge30ResidentPopulation(getL(row,"남성연령대_30_상주인구_수"))
                .maleAge40ResidentPopulation(getL(row,"남성연령대_40_상주인구_수"))
                .maleAge50ResidentPopulation(getL(row,"남성연령대_50_상주인구_수"))
                .maleAge60PlusResidentPopulation(getL(row,"남성연령대_60_이상_상주인구_수"))
                .femaleAge10ResidentPopulation(getL(row,"여성연령대_10_상주인구_수"))
                .femaleAge20ResidentPopulation(getL(row,"여성연령대_20_상주인구_수"))
                .femaleAge30ResidentPopulation(getL(row,"여성연령대_30_상주인구_수"))
                .femaleAge40ResidentPopulation(getL(row,"여성연령대_40_상주인구_수"))
                .femaleAge50ResidentPopulation(getL(row,"여성연령대_50_상주인구_수"))
                .femaleAge60PlusResidentPopulation(getL(row,"여성연령대_60_이상_상주인구_수"))
                .totalHouseholds(getL(row,"총_가구_수"))
                .apartmentHouseholds(getL(row,"아파트_가구_수"))
                .nonApartmentHouseholds(getL(row,"비_아파트_가구_수"))
                .avgMonthlyIncome(getL(row,"월_평균_소득_금액"))
                .incomeSectionCode(getS(row,"소득_구간_코드"))
                .totalExpenditure(getL(row,"지출_총금액"))
                .foodExpenditure(getL(row,"식료품_지출_총금액"))
                .clothingExpenditure(getL(row,"의류_신발_지출_총금액"))
                .householdGoodsExpenditure(getL(row,"생활용품_지출_총금액"))
                .medicalExpenditure(getL(row,"의료비_지출_총금액"))
                .transportExpenditure(getL(row,"교통_지출_총금액"))
                .educationExpenditure(getL(row,"교육_지출_총금액"))
                .entertainmentExpenditure(getL(row,"유흥_지출_총금액"))
                .leisureCultureExpenditure(getL(row,"여가_문화_지출_총금액"))
                .otherExpenditure(getL(row,"기타_지출_총금액"))
                .diningExpenditure(getL(row,"음식_지출_총금액"))
                .totalWorkplacePopulation(getL(row,"총_직장_인구_수"))
                .maleWorkplacePopulation(getL(row,"남성_직장_인구_수"))
                .femaleWorkplacePopulation(getL(row,"여성_직장_인구_수"))
                .age10WorkplacePopulation(getL(row,"연령대_10_직장_인구_수"))
                .age20WorkplacePopulation(getL(row,"연령대_20_직장_인구_수"))
                .age30WorkplacePopulation(getL(row,"연령대_30_직장_인구_수"))
                .age40WorkplacePopulation(getL(row,"연령대_40_직장_인구_수"))
                .age50WorkplacePopulation(getL(row,"연령대_50_직장_인구_수"))
                .age60PlusWorkplacePopulation(getL(row,"연령대_60_이상_직장_인구_수"))
                .maleAge10WorkplacePopulation(getL(row,"남성연령대_10_직장_인구_수"))
                .maleAge20WorkplacePopulation(getL(row,"남성연령대_20_직장_인구_수"))
                .maleAge30WorkplacePopulation(getL(row,"남성연령대_30_직장_인구_수"))
                .maleAge40WorkplacePopulation(getL(row,"남성연령대_40_직장_인구_수"))
                .maleAge50WorkplacePopulation(getL(row,"남성연령대_50_직장_인구_수"))
                .maleAge60PlusWorkplacePopulation(getL(row,"남성연령대_60_이상_직장_인구_수"))
                .femaleAge10WorkplacePopulation(getL(row,"여성연령대_10_직장_인구_수"))
                .femaleAge20WorkplacePopulation(getL(row,"여성연령대_20_직장_인구_수"))
                .femaleAge30WorkplacePopulation(getL(row,"여성연령대_30_직장_인구_수"))
                .femaleAge40WorkplacePopulation(getL(row,"여성연령대_40_직장_인구_수"))
                .femaleAge50WorkplacePopulation(getL(row,"여성연령대_50_직장_인구_수"))
                .femaleAge60PlusWorkplacePopulation(getL(row,"여성연령대_60_이상_직장_인구_수"))
                .attractingFacilityCount(getL(row,"집객시설_수"))
                .governmentOfficeCount(getL(row,"관공서_수"))
                .bankCount(getL(row,"은행_수"))
                .generalHospitalCount(getL(row,"종합병원_수"))
                .hospitalCount(getL(row,"일반_병원_수"))
                .pharmacyCount(getL(row,"약국_수"))
                .kindergartenCount(getL(row,"유치원_수"))
                .elementarySchoolCount(getL(row,"초등학교_수"))
                .middleSchoolCount(getL(row,"중학교_수"))
                .highSchoolCount(getL(row,"고등학교_수"))
                .universityCount(getL(row,"대학교_수"))
                .departmentStoreCount(getL(row,"백화점_수"))
                .supermarketCount(getL(row,"슈퍼마켓_수"))
                .theaterCount(getL(row,"극장_수"))
                .lodgingFacilityCount(getL(row,"숙박_시설_수"))
                .airportCount(getL(row,"공항_수"))
                .railwayStationCount(getL(row,"철도_역_수"))
                .busTerminalCount(getL(row,"버스_터미널_수"))
                .subwayStationCount(getL(row,"지하철_역_수"))
                .busStopCount(getL(row,"버스_정거장_수"))
                .serviceIndustryCode(getS(row,"서비스_업종_코드"))
                .serviceIndustryName(getS(row,"서비스_업종_코드_명"))
                .storeCount(getL(row,"점포_수"))
                .similarIndustryStoreCount(getL(row,"유사_업종_점포_수"))
                .openingRate(getD(row,"개업_율"))
                .openingStoreCount(getL(row,"개업_점포_수"))
                .closingRate(getD(row,"폐업_률"))
                .closingStoreCount(getL(row,"폐업_점포_수"))
                .franchiseStoreCount(getL(row,"프랜차이즈_점포_수"))
                .monthlySalesAmount(getL(row,"당월_매출_금액"))
                .monthlySalesCount(getL(row,"당월_매출_건수"))
                .weekdaySalesAmount(getL(row,"주중_매출_금액"))
                .weekendSalesAmount(getL(row,"주말_매출_금액"))
                .mondaySalesAmount(getL(row,"월요일_매출_금액"))
                .tuesdaySalesAmount(getL(row,"화요일_매출_금액"))
                .wednesdaySalesAmount(getL(row,"수요일_매출_금액"))
                .thursdaySalesAmount(getL(row,"목요일_매출_금액"))
                .fridaySalesAmount(getL(row,"금요일_매출_금액"))
                .saturdaySalesAmount(getL(row,"토요일_매출_금액"))
                .sundaySalesAmount(getL(row,"일요일_매출_금액"))
                .time00to06SalesAmount(getL(row,"시간대_00~06_매출_금액"))
                .time06to11SalesAmount(getL(row,"시간대_06~11_매출_금액"))
                .time11to14SalesAmount(getL(row,"시간대_11~14_매출_금액"))
                .time14to17SalesAmount(getL(row,"시간대_14~17_매출_금액"))
                .time17to21SalesAmount(getL(row,"시간대_17~21_매출_금액"))
                .time21to24SalesAmount(getL(row,"시간대_21~24_매출_금액"))
                .maleSalesAmount(getL(row,"남성_매출_금액"))
                .femaleSalesAmount(getL(row,"여성_매출_금액"))
                .age10SalesAmount(getL(row,"연령대_10_매출_금액"))
                .age20SalesAmount(getL(row,"연령대_20_매출_금액"))
                .age30SalesAmount(getL(row,"연령대_30_매출_금액"))
                .age40SalesAmount(getL(row,"연령대_40_매출_금액"))
                .age50SalesAmount(getL(row,"연령대_50_매출_금액"))
                .age60PlusSalesAmount(getL(row,"연령대_60_이상_매출_금액"))
                .weekdaySalesCount(getL(row,"주중_매출_건수"))
                .weekendSalesCount(getL(row,"주말_매출_건수"))
                .mondaySalesCount(getL(row,"월요일_매출_건수"))
                .tuesdaySalesCount(getL(row,"화요일_매출_건수"))
                .wednesdaySalesCount(getL(row,"수요일_매출_건수"))
                .thursdaySalesCount(getL(row,"목요일_매출_건수"))
                .fridaySalesCount(getL(row,"금요일_매출_건수"))
                .saturdaySalesCount(getL(row,"토요일_매출_건수"))
                .sundaySalesCount(getL(row,"일요일_매출_건수"))
                .time00to06SalesCount(getL(row,"시간대_건수~06_매출_건수"))
                .time06to11SalesCount(getL(row,"시간대_건수~11_매출_건수"))
                .time11to14SalesCount(getL(row,"시간대_건수~14_매출_건수"))
                .time14to17SalesCount(getL(row,"시간대_건수~17_매출_건수"))
                .time17to21SalesCount(getL(row,"시간대_건수~21_매출_건수"))
                .time21to24SalesCount(getL(row,"시간대_건수~24_매출_건수"))
                .maleSalesCount(getL(row,"남성_매출_건수"))
                .femaleSalesCount(getL(row,"여성_매출_건수"))
                .age10SalesCount(getL(row,"연령대_10_매출_건수"))
                .age20SalesCount(getL(row,"연령대_20_매출_건수"))
                .age30SalesCount(getL(row,"연령대_30_매출_건수"))
                .age40SalesCount(getL(row,"연령대_40_매출_건수"))
                .age50SalesCount(getL(row,"연령대_50_매출_건수"))
                .age60PlusSalesCount(getL(row,"연령대_60_이상_매출_건수"))
                .build();
    }


    // DB에 저장된 데이터 찾기
    public DashBoard getDashboardData(String adminDongCode) {
        List<DataSet> list = dataSetRepository.findByAdminDongCodeAndBaseYearQuarterCode(adminDongCode, "20251");

        if (list.isEmpty()) {
            throw new RuntimeException("해당 행정동 데이터 없음");
        }

        // 분기중에 한개만 뽑기
        DataSet ds = list.get(0);

        return DashBoard.builder()
                .baseYearQuarterCode(ds.getBaseYearQuarterCode())
                .adminDongCode(ds.getAdminDongCode())
                .adminDongName(ds.getAdminDongName())
                .totalFloatingPopulation(ds.getTotalFloatingPopulation())
                .monthlySalesAmount(ds.getMonthlySalesAmount())
                .build();
    }
}
