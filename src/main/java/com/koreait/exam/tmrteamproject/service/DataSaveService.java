package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.DataSaveRepository;
import com.koreait.exam.tmrteamproject.repository.DataSetRepository;
import com.koreait.exam.tmrteamproject.vo.ClosedBiz;
import com.koreait.exam.tmrteamproject.vo.DataSet;
import com.opencsv.CSVReaderHeaderAware;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.*;
import org.springframework.stereotype.Service;
import org.springframework.ui.Model;

import javax.transaction.Transactional;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Stream;

@Slf4j
@Service
@RequiredArgsConstructor
public class DataSaveService {

    private final DataSaveRepository dataSaveRepository;

    private final DataSetRepository dataSetRepository;

    public String setInsertData(File file, Model model) {
        log.debug("파일명: {}", file.getName());
        log.debug("파일 크기: {}", file.length());

        try {
            // 파일 확인
            if (file.length() == 0) {
                model.addAttribute("message", "없는 파일입니다.");
                return "dataset/excel";
            }

            //확장자 검사
            String fileName = file.getName();
            if (!fileName.endsWith(".xlsx") && !fileName.endsWith(".xls")) {
                model.addAttribute("message", "Excel 파일만 가능합니다");
                return "dataset/excel";
            }

            List<ClosedBiz> closedBizs = new ArrayList<>();

            try {
                FileInputStream fis = new FileInputStream(file);
                Workbook workbook = WorkbookFactory.create(fis);

                Sheet sheet = workbook.getSheetAt(0);

                for (int i = 1; i < sheet.getPhysicalNumberOfRows(); i++) {
                    Row row = sheet.getRow(i);
                    if (row == null) continue;

                    try {
                        ClosedBiz closedBiz = ClosedBiz.builder()
                                .dongName(getCellString(row.getCell(0)))
                                .upjongType(getCellString(row.getCell(1)))
                                .closeYm(getCellString(row.getCell(2)))
                                .closeCount(getCellString(row.getCell(3)))
                                .build();

                        closedBizs.add(closedBiz);
                    } catch (Exception e) {
                        log.warn("행 {} 처리 중 오류: {}", i, e.getMessage());
                    }
                }
            } catch (Exception e) {
                model.addAttribute("message", "파일 읽기 실패" +  e.getMessage());
            }

            log.debug("파싱된 폐업 데이터 리스트: {}", closedBizs);
            model.addAttribute("message", "총 " + closedBizs.size() + "건의 데이터가 성공적으로 파싱되었습니다.");

            // DB 저장
            for (ClosedBiz closedBiz : closedBizs) {
                dataSaveRepository.save(closedBiz);
            }

        } catch (Exception e) {
            model.addAttribute("message", "파일 처리중 오류가 발생 했습니다." + e.getMessage());
        }

        return "dataset/excel";
    }

    private String getCellString(Cell cell) {
        if (cell == null) return "";
        return switch (cell.getCellType()) {
            case STRING -> cell.getStringCellValue();
            case NUMERIC -> String.valueOf(cell.getNumericCellValue());
            case BOOLEAN -> String.valueOf(cell.getBooleanCellValue());
            case FORMULA -> cell.getCellFormula();
            default -> "";
        };
    }

    public int saveAllFromDir(String csvDir) {
        int totalSaved = 0;

        try {
            Path path = Paths.get(csvDir).toAbsolutePath();
            System.out.println("[INFO] CSV 디렉토리 경로: " + path);

            // CSV 파일 순회
            try (Stream<Path> paths = Files.walk(path)) {
                List<Path> csvFiles = paths
                        .filter(Files::isRegularFile)
                        .filter(f -> f.toString().toLowerCase().endsWith(".csv"))
                        .toList();

                System.out.println("[INFO] 발견된 CSV 파일 수: " + csvFiles.size());

                for (Path file : csvFiles) {
                    System.out.println("[INFO] 처리 시작 → " + file);
                    int saved = saveFromCsv(file);
                    System.out.println("[INFO] 처리 완료: " + file + " → 저장 건수: " + saved);
                    totalSaved += saved;
                }
            }
        } catch (Exception e) {
            throw new RuntimeException("CSV 디렉토리 읽기 실패: " + csvDir, e);
        }

        System.out.println("[INFO] 전체 저장 완료 → 총 건수: " + totalSaved);
        return totalSaved;
    }

    public int saveFromCsv(Path csvFile) throws Exception {
        int savedCount = 0;

        try (Reader reader = Files.newBufferedReader(csvFile, StandardCharsets.UTF_8);
             CSVReaderHeaderAware csvReader = new CSVReaderHeaderAware(reader)) {

            Map<String, String> row;
            int rowIndex = -1;
            while ((row = csvReader.readMap()) != null) {
                rowIndex++;
                if (rowIndex <= 10) { // 처음 10개 행만 미리보기
                    System.out.println("[DEBUG] " + csvFile.getFileName() + " → 행 " + rowIndex + ": " + row);
                }

                DataSet entity = mapRowToEntity(row);
                dataSetRepository.save(entity);
                savedCount++;
            }
        } catch (IOException e) {
            throw new RuntimeException("CSV 읽기 실패: " + csvFile, e);
        }

        return savedCount;
    }

    private long l(Map<String, String> row, String key) {
        try {
            String value = row.getOrDefault(key, "").trim();
            if (value.isEmpty() || value.equalsIgnoreCase("NaN")) return 0L;
            return Long.parseLong(value);
        } catch (NumberFormatException e) {
            return 0L;
        }
    }

    private double d(Map<String, String> row, String key) {
        try {
            String value = row.getOrDefault(key, "").trim();
            if (value.isEmpty() || value.equalsIgnoreCase("NaN")) return 0.0;
            return Double.parseDouble(value);
        } catch (NumberFormatException e) {
            return 0.0;
        }
    }

    private String s(Map<String, String> row, String key) {
        return row.getOrDefault(key, "").trim();
    }

    private DataSet mapRowToEntity(Map<String, String> row) {
        return DataSet.builder()
                .baseYearQuarterCode(l(row, "기준_년분기_코드"))
                .adminDongCode(s(row, "행정동_코드"))
                .adminDongName(s(row,"행정동_코드_명"))
                .totalFloatingPopulation(l(row,"총_유동인구_수"))
                .maleFloatingPopulation(l(row,"남성_유동인구_수"))
                .femaleFloatingPopulation(l(row,"여성_유동인구_수"))
                .age10FloatingPopulation(l(row,"연령대_10_유동인구_수"))
                .age20FloatingPopulation(l(row,"연령대_20_유동인구_수"))
                .age30FloatingPopulation(l(row,"연령대_30_유동인구_수"))
                .age40FloatingPopulation(l(row,"연령대_40_유동인구_수"))
                .age50FloatingPopulation(l(row,"연령대_50_유동인구_수"))
                .age60PlusFloatingPopulation(l(row,"연령대_60_이상_유동인구_수"))
                .time00to06FloatingPopulation(l(row,"시간대_00_06_유동인구_수"))
                .time06to11FloatingPopulation(l(row,"시간대_06_11_유동인구_수"))
                .time11to14FloatingPopulation(l(row,"시간대_11_14_유동인구_수"))
                .time14to17FloatingPopulation(l(row,"시간대_14_17_유동인구_수"))
                .time17to21FloatingPopulation(l(row,"시간대_17_21_유동인구_수"))
                .time21to24FloatingPopulation(l(row,"시간대_21_24_유동인구_수"))
                .mondayFloatingPopulation(l(row,"월요일_유동인구_수"))
                .tuesdayFloatingPopulation(l(row,"화요일_유동인구_수"))
                .wednesdayFloatingPopulation(l(row,"수요일_유동인구_수"))
                .thursdayFloatingPopulation(l(row,"목요일_유동인구_수"))
                .fridayFloatingPopulation(l(row,"금요일_유동인구_수"))
                .saturdayFloatingPopulation(l(row,"토요일_유동인구_수"))
                .sundayFloatingPopulation(l(row,"일요일_유동인구_수"))
                .commercialChangeIndex(s(row,"상권_변화_지표"))
                .commercialChangeIndexName(s(row,"상권_변화_지표_명"))
                .avgOperatingMonths(d(row,"운영_영업_개월_평균"))
                .avgClosedMonths(d(row,"폐업_영업_개월_평균"))
                .avgOperatingMonthsSeoul(d(row,"서울_운영_영업_개월_평균"))
                .avgClosedMonthsSeoul(d(row,"서울_폐업_영업_개월_평균"))
                .totalResidentPopulation(l(row,"총_상주인구_수"))
                .maleResidentPopulation(l(row,"남성_상주인구_수"))
                .femaleResidentPopulation(l(row,"여성_상주인구_수"))
                .age10ResidentPopulation(l(row,"연령대_10_상주인구_수"))
                .age20ResidentPopulation(l(row,"연령대_20_상주인구_수"))
                .age30ResidentPopulation(l(row,"연령대_30_상주인구_수"))
                .age40ResidentPopulation(l(row,"연령대_40_상주인구_수"))
                .age50ResidentPopulation(l(row,"연령대_50_상주인구_수"))
                .age60PlusResidentPopulation(l(row,"연령대_60_이상_상주인구_수"))
                .maleAge10ResidentPopulation(l(row,"남성연령대_10_상주인구_수"))
                .maleAge20ResidentPopulation(l(row,"남성연령대_20_상주인구_수"))
                .maleAge30ResidentPopulation(l(row,"남성연령대_30_상주인구_수"))
                .maleAge40ResidentPopulation(l(row,"남성연령대_40_상주인구_수"))
                .maleAge50ResidentPopulation(l(row,"남성연령대_50_상주인구_수"))
                .maleAge60PlusResidentPopulation(l(row,"남성연령대_60_이상_상주인구_수"))
                .femaleAge10ResidentPopulation(l(row,"여성연령대_10_상주인구_수"))
                .femaleAge20ResidentPopulation(l(row,"여성연령대_20_상주인구_수"))
                .femaleAge30ResidentPopulation(l(row,"여성연령대_30_상주인구_수"))
                .femaleAge40ResidentPopulation(l(row,"여성연령대_40_상주인구_수"))
                .femaleAge50ResidentPopulation(l(row,"여성연령대_50_상주인구_수"))
                .femaleAge60PlusResidentPopulation(l(row,"여성연령대_60_이상_상주인구_수"))
                .totalHouseholds(l(row,"총_가구_수"))
                .apartmentHouseholds(l(row,"아파트_가구_수"))
                .nonApartmentHouseholds(l(row,"비_아파트_가구_수"))
                .avgMonthlyIncome(l(row,"월_평균_소득_금액"))
                .incomeSectionCode(s(row,"소득_구간_코드"))
                .totalExpenditure(l(row,"지출_총금액"))
                .foodExpenditure(l(row,"식료품_지출_총금액"))
                .clothingExpenditure(l(row,"의류_신발_지출_총금액"))
                .householdGoodsExpenditure(l(row,"생활용품_지출_총금액"))
                .medicalExpenditure(l(row,"의료비_지출_총금액"))
                .transportExpenditure(l(row,"교통_지출_총금액"))
                .educationExpenditure(l(row,"교육_지출_총금액"))
                .entertainmentExpenditure(l(row,"유흥_지출_총금액"))
                .leisureCultureExpenditure(l(row,"여가_문화_지출_총금액"))
                .otherExpenditure(l(row,"기타_지출_총금액"))
                .diningExpenditure(l(row,"음식_지출_총금액"))
                .totalWorkplacePopulation(l(row,"총_직장_인구_수"))
                .maleWorkplacePopulation(l(row,"남성_직장_인구_수"))
                .femaleWorkplacePopulation(l(row,"여성_직장_인구_수"))
                .age10WorkplacePopulation(l(row,"연령대_10_직장_인구_수"))
                .age20WorkplacePopulation(l(row,"연령대_20_직장_인구_수"))
                .age30WorkplacePopulation(l(row,"연령대_30_직장_인구_수"))
                .age40WorkplacePopulation(l(row,"연령대_40_직장_인구_수"))
                .age50WorkplacePopulation(l(row,"연령대_50_직장_인구_수"))
                .age60PlusWorkplacePopulation(l(row,"연령대_60_이상_직장_인구_수"))
                .maleAge10WorkplacePopulation(l(row,"남성연령대_10_직장_인구_수"))
                .maleAge20WorkplacePopulation(l(row,"남성연령대_20_직장_인구_수"))
                .maleAge30WorkplacePopulation(l(row,"남성연령대_30_직장_인구_수"))
                .maleAge40WorkplacePopulation(l(row,"남성연령대_40_직장_인구_수"))
                .maleAge50WorkplacePopulation(l(row,"남성연령대_50_직장_인구_수"))
                .maleAge60PlusWorkplacePopulation(l(row,"남성연령대_60_이상_직장_인구_수"))
                .femaleAge10WorkplacePopulation(l(row,"여성연령대_10_직장_인구_수"))
                .femaleAge20WorkplacePopulation(l(row,"여성연령대_20_직장_인구_수"))
                .femaleAge30WorkplacePopulation(l(row,"여성연령대_30_직장_인구_수"))
                .femaleAge40WorkplacePopulation(l(row,"여성연령대_40_직장_인구_수"))
                .femaleAge50WorkplacePopulation(l(row,"여성연령대_50_직장_인구_수"))
                .femaleAge60PlusWorkplacePopulation(l(row,"여성연령대_60_이상_직장_인구_수"))
                .attractingFacilityCount(l(row,"집객시설_수"))
                .governmentOfficeCount(l(row,"관공서_수"))
                .bankCount(l(row,"은행_수"))
                .generalHospitalCount(l(row,"종합병원_수"))
                .hospitalCount(l(row,"일반_병원_수"))
                .pharmacyCount(l(row,"약국_수"))
                .kindergartenCount(l(row,"유치원_수"))
                .elementarySchoolCount(l(row,"초등학교_수"))
                .middleSchoolCount(l(row,"중학교_수"))
                .highSchoolCount(l(row,"고등학교_수"))
                .universityCount(l(row,"대학교_수"))
                .departmentStoreCount(l(row,"백화점_수"))
                .supermarketCount(l(row,"슈퍼마켓_수"))
                .theaterCount(l(row,"극장_수"))
                .lodgingFacilityCount(l(row,"숙박_시설_수"))
                .airportCount(l(row,"공항_수"))
                .railwayStationCount(l(row,"철도_역_수"))
                .busTerminalCount(l(row,"버스_터미널_수"))
                .subwayStationCount(l(row,"지하철_역_수"))
                .busStopCount(l(row,"버스_정거장_수"))
                .serviceIndustryCode(s(row,"서비스_업종_코드"))
                .serviceIndustryName(s(row,"서비스_업종_코드_명"))
                .storeCount(l(row,"점포_수"))
                .similarIndustryStoreCount(l(row,"유사_업종_점포_수"))
                .openingRate(d(row,"개업_율"))
                .openingStoreCount(l(row,"개업_점포_수"))
                .closingRate(d(row,"폐업_률"))
                .closingStoreCount(l(row,"폐업_점포_수"))
                .franchiseStoreCount(l(row,"프랜차이즈_점포_수"))
                .monthlySalesAmount(l(row,"당월_매출_금액"))
                .monthlySalesCount(l(row,"당월_매출_건수"))
                .weekdaySalesAmount(l(row,"주중_매출_금액"))
                .weekendSalesAmount(l(row,"주말_매출_금액"))
                .mondaySalesAmount(l(row,"월요일_매출_금액"))
                .tuesdaySalesAmount(l(row,"화요일_매출_금액"))
                .wednesdaySalesAmount(l(row,"수요일_매출_금액"))
                .thursdaySalesAmount(l(row,"목요일_매출_금액"))
                .fridaySalesAmount(l(row,"금요일_매출_금액"))
                .saturdaySalesAmount(l(row,"토요일_매출_금액"))
                .sundaySalesAmount(l(row,"일요일_매출_금액"))
                .time00to06SalesAmount(l(row,"시간대_00~06_매출_금액"))
                .time06to11SalesAmount(l(row,"시간대_06~11_매출_금액"))
                .time11to14SalesAmount(l(row,"시간대_11~14_매출_금액"))
                .time14to17SalesAmount(l(row,"시간대_14~17_매출_금액"))
                .time17to21SalesAmount(l(row,"시간대_17~21_매출_금액"))
                .time21to24SalesAmount(l(row,"시간대_21~24_매출_금액"))
                .maleSalesAmount(l(row,"남성_매출_금액"))
                .femaleSalesAmount(l(row,"여성_매출_금액"))
                .age10SalesAmount(l(row,"연령대_10_매출_금액"))
                .age20SalesAmount(l(row,"연령대_20_매출_금액"))
                .age30SalesAmount(l(row,"연령대_30_매출_금액"))
                .age40SalesAmount(l(row,"연령대_40_매출_금액"))
                .age50SalesAmount(l(row,"연령대_50_매출_금액"))
                .age60PlusSalesAmount(l(row,"연령대_60_이상_매출_금액"))
                .weekdaySalesCount(l(row,"주중_매출_건수"))
                .weekendSalesCount(l(row,"주말_매출_건수"))
                .mondaySalesCount(l(row,"월요일_매출_건수"))
                .tuesdaySalesCount(l(row,"화요일_매출_건수"))
                .wednesdaySalesCount(l(row,"수요일_매출_건수"))
                .thursdaySalesCount(l(row,"목요일_매출_건수"))
                .fridaySalesCount(l(row,"금요일_매출_건수"))
                .saturdaySalesCount(l(row,"토요일_매출_건수"))
                .sundaySalesCount(l(row,"일요일_매출_건수"))
                .time00to06SalesCount(l(row,"시간대_건수~06_매출_건수"))
                .time06to11SalesCount(l(row,"시간대_건수~11_매출_건수"))
                .time11to14SalesCount(l(row,"시간대_건수~14_매출_건수"))
                .time14to17SalesCount(l(row,"시간대_건수~17_매출_건수"))
                .time17to21SalesCount(l(row,"시간대_건수~21_매출_건수"))
                .time21to24SalesCount(l(row,"시간대_건수~24_매출_건수"))
                .maleSalesCount(l(row,"남성_매출_건수"))
                .femaleSalesCount(l(row,"여성_매출_건수"))
                .age10SalesCount(l(row,"연령대_10_매출_건수"))
                .age20SalesCount(l(row,"연령대_20_매출_건수"))
                .age30SalesCount(l(row,"연령대_30_매출_건수"))
                .age40SalesCount(l(row,"연령대_40_매출_건수"))
                .age50SalesCount(l(row,"연령대_50_매출_건수"))
                .age60PlusSalesCount(l(row,"연령대_60_이상_매출_건수"))
                .build();
    }
}
