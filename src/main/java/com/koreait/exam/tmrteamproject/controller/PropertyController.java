package com.koreait.exam.tmrteamproject.controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.koreait.exam.tmrteamproject.service.AddressService;
import com.koreait.exam.tmrteamproject.service.KakaoOAuthService;
import com.koreait.exam.tmrteamproject.service.PropertyService;
import com.koreait.exam.tmrteamproject.vo.AddressPickReq;
import com.koreait.exam.tmrteamproject.vo.NormalizedAddress;
import com.koreait.exam.tmrteamproject.vo.PropertyFile;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import okhttp3.Address;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.parameters.P;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Controller
@RequestMapping("usr/property")
@Slf4j
@RequiredArgsConstructor
public class PropertyController {

    private final PropertyService propertyService;
    private final AddressService addressService;
    private final KakaoOAuthService kakaoOAuthService;

    @GetMapping("/upload")
    public String uploadForm() {
        // templates/property/upload.html 렌더링
        return "property/upload";
    }

    // 파일 업로드 및 파이썬으로 파일 보내기
    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<?> handleUpload(
            @RequestPart(value = "file", required = false) MultipartFile file,
            @RequestPart(value = "files", required = false) List<MultipartFile> files,
            @RequestParam("deposit") int deposit,
            @RequestParam("monthlyRent") int monthlyRent,
            @RequestParam(required = false) Double lat,
            @RequestParam(required = false) Double lng
    ) throws Exception {
        // 0) (만원)으로 들어온 데이터 10,000 곱해주기
        deposit *= 10000;
        monthlyRent *= 10000;

        // 1) 들어온 파일 모으기 (file 또는 files)
        List<MultipartFile> all = new ArrayList<>();
        if (file != null && !file.isEmpty()) all.add(file);
        if (files != null) {
            for (MultipartFile f : files) if (f != null && !f.isEmpty()) all.add(f);
        }
        if (all.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("ok", false, "message", "파일이 없습니다."));
        }

        // 2) PDF만 추리기 (MIME/확장자 + 매직바이트 스니핑)
        List<MultipartFile> pdfOnly = all.stream()
                .filter(f -> isPdfByHeader(f) || looksLikePdf(f))
                .toList();

        if (pdfOnly.isEmpty()) {
            return ResponseEntity.status(415).body(Map.of(
                    "ok", false,
                    "error", "unsupported_media_type",
                    "message", "PDF만 업로드할 수 있습니다."
            ));
        }

        // 3) PDF가 2개 이상이면 경고하고 중단
        if (pdfOnly.size() > 1) {
            List<String> names = pdfOnly.stream()
                    .map(f -> Optional.ofNullable(f.getOriginalFilename()).orElse("noname"))
                    .toList();
            return ResponseEntity.badRequest().body(Map.of(
                    "ok", false,
                    "error", "too_many_pdfs",
                    "message", "PDF는 1개만 업로드하세요.",
                    "count", pdfOnly.size(),
                    "files", names
            ));
        }

        // 4) 좌표 메타(옵션)
        Map<String, String> extra = new HashMap<>();
        if (lat != null) extra.put("lat", String.valueOf(lat));
        if (lng != null) extra.put("lng", String.valueOf(lng));

        // 5) 파이썬에 파일 보내고 분석 결과 받기
        MultipartFile thePdf = pdfOnly.get(0);
        Map<String, Object> result = propertyService.analyzeWithPythonDirect(List.of(thePdf), extra);

        // 6) 분석된 주소에서 normal인 것만 빼오기 (공동매물)
        Map<String, Object> filteredResult = propertyService.printNormalAddresses(result);


        // 6-1) 채권최고액 가져오기
        List<Map<String, Object>> mortgages =
                (List<Map<String, Object>>) result.get("mortgageInfo");

        long sumAmountKRW = 0;
        for (Map<String, Object> mortgage : mortgages) {
            String status = (String) mortgage.get("status");

            if (status.equals("cancelled")) continue;

            Number amount = (Number) mortgage.get("amountKRW");
            sumAmountKRW += amount.longValue();

        }

        System.out.println("sumAmountKRW : " + sumAmountKRW);

        // 7) 분석된 주소마다 면적 구해오기
        List<Map<String, Object>> normals = (List<Map<String, Object>>) filteredResult.get("normalAddresses");
        double sum = 0.0;

        if (normals == null || normals.isEmpty()) {
            System.out.println("✅ normal 주소 없음");
        } else {
            for (Map<String, Object> addr : normals) {
                String address = (String) addr.get("address");

                double area = propertyService.resolveAreaFromLine(address);

                sum += area;
            }
        }

        // 8) 현재주소 면적 가져오기
        double currentArea = propertyService.resolveAreaFromLine((String) result.get("jointCollateralCurrentAddress"));
        sum += currentArea;

        // 9) 가중치 계산
        double areaWeight = currentArea / sum;

        // 10) 가중치에 따른 채권금액 계산
        Long weightedValue = Math.round(sumAmountKRW * areaWeight);

        // 11) 평균월세 가져오기
        // 현재 주소 가져오기
        String currentAddress = (String) result.get("jointCollateralCurrentAddress");

        // 2) PropertyService 유틸로 전처리
        String cleaned = propertyService.cleanup(currentAddress);
        String normalizedCurrentAddr = propertyService.simplifyToLegalLot(cleaned);

        // AddressService로 검색
        List<NormalizedAddress> list = addressService.search(normalizedCurrentAddr, 1, 5);

        Map<String, Object> response;
        NormalizedAddress n = list.get(0);

        // AddressPickReq 생성
        AddressPickReq req = new AddressPickReq();
        req.setSelected(n);

        // ✅ 최종: confirm + geocode + crawl 한번에 실행
        response = addressService.confirmGeoAndCrawl(req);

        ResultData avgMonthlyRd = addressService.calculateAverageMonthly(response, currentArea);
        double avgMonthlyPerM2 = (double) avgMonthlyRd.getData1();

        ResultData avgDepositRd = addressService.calculateAverageDeposit(response, currentArea);
        double avgDepositPerM2 = (double) avgDepositRd.getData1();
        // 12) 예상 선순위보증금 계산
        // 선임차 환산보증금 + 채권금액
        // 선임차 환산보증금 : 지역 평균 월세 * 전유면적
        double seniorityTotal = avgMonthlyPerM2 * currentArea * 100 + weightedValue;

        long seniorityTotalRounded = Math.round(seniorityTotal);

        // 한국 원화 기준 포맷
        NumberFormat formatter = NumberFormat.getCurrencyInstance(Locale.KOREA);
        String seniorityTotalFormatted = formatter.format(seniorityTotalRounded);

        // 시세 괴리 리스크
        double unit_rent = monthlyRent / currentArea;
        double unit_deposit = deposit / currentArea;

        // 괴리율 계산
        double rentGapRatio = (unit_rent - avgMonthlyPerM2) / avgMonthlyPerM2;
        double depositGapRatio = (unit_deposit - avgDepositPerM2) / avgDepositPerM2;

        // 4. 리스크 레벨
        String rentRisk = getRiskLevel(rentGapRatio);
        String depositRisk = getRiskLevel(depositGapRatio);

        // 13) 담보가치 계산
        // 연 임대수익 / 임대수익률
        // 연 임대수익 : 월세 * 12 + 보증금 * 0.02(환산율)

        double annualRentalIncome = monthlyRent * 12 + deposit * 0.02;

        List<Map<String, Object>> items = propertyService.fetchBldRgstItems(currentAddress);
        Map<String, Object> realItem = items.get(0);
        double totalArea = propertyService.resolveAreaFromLine(currentAddress);


        // 건물시가 + 토지시가
        ResponseEntity data = propertyService.getBasePrice(currentAddress, realItem);
        // 1. Body 꺼내기
        Map<String, Object> body = (Map<String, Object>) data.getBody();

        // 4. 개별 값 접근
        // 건물시가
        double buildBasePrice = Double.parseDouble(body.get("build_base_price").toString());
        // 토지시가
        double landBasePrice  = Double.parseDouble(body.get("land_base_price").toString());

        // 토지면적
        double landShareArea = (double) result.get("landShareArea");

        // 토지 지분가치 (토지시가 * 토지면적)
        double landShareValue = landShareArea * landBasePrice;

        // 건물 지분 가치 (건물시가 * 전유면적)
        double buildingValue = currentArea * buildBasePrice;

        // 담보가치(정적)
        double collateralValueTotal = landShareValue + buildingValue;
        System.out.println("landShareValue : " + landShareValue);
        System.out.println("buildingalue : " + buildingValue);
        System.out.println("collateralValue : " + collateralValueTotal);

        String regstrGbCdNm = realItem.get("regstrGbCdNm").toString();
        String mainPurpsCdNm = realItem.get("mainPurpsCdNm").toString();

        // 상가종류 분류
        String buildingType;

        if (regstrGbCdNm.equals("집합")) {
            buildingType = "집합";
        } else if (mainPurpsCdNm.contains("업무시설") || mainPurpsCdNm.contains("오피스텔") || mainPurpsCdNm.contains("사무소")) {
            buildingType = "오피스";
        } else if (totalArea < 1000 && (int) realItem.get("flrNo") <= 2) {
            buildingType = "소규모";
        } else {
            buildingType = "중대형";
        }


        // 임대수익률 가져오기
        double rentalYield = propertyService.getRentYield(n.siNm, buildingType, 1, 10);

        // 담보가치 계산
        double collateralValue = annualRentalIncome / rentalYield;

        // 14) 채권보증금 리스크 계산
        // 채권 최고액 + 예산 선순위보증금 금액 / 담보가치
        double riskRatio = (weightedValue + seniorityTotalRounded) / collateralValue;

        String bondDepositRisk;

        if (riskRatio < 0.5) {
            bondDepositRisk = "정상";
        } else if (riskRatio < 0.7) {
            bondDepositRisk = "주의";
        } else if (riskRatio < 1.0) {
            bondDepositRisk = "위험";
        } else {
            bondDepositRisk = "고위험";
        }

        // 15) 근저당권 기반 위험
        // 채권최고액 / 담보가치
        // < 0.5 : 양호
        // 0.5~ 1.0 : 경계
        // >= 1.0 : 깡통매물
        double debtRatio = weightedValue / collateralValue;

        String debtRiskLevel;

        if (debtRatio < 0.5) {
            debtRiskLevel = "정상";
        } else if (debtRatio < 0.7) {
            debtRiskLevel = "주의";
        } else if (debtRatio < 1.0) {
            debtRiskLevel = "위험";
        } else {
            debtRiskLevel = "고위험";
        }

        double predictedMonthly = avgMonthlyPerM2 * currentArea;
        double predictedDeposit = avgDepositPerM2 * currentArea;

        // 예상 월세 계산
        DecimalFormat df = new DecimalFormat("#.#"); // 소수점 한 자리, 필요할 때만 표시
        long avgMonthlyDisplay = Math.round(predictedMonthly / 10000.0);
        long avgDepositDisplay = Math.round(predictedDeposit / 10000.0);

        // 평균 m2당 월세
        double MonthlyDisplayPerSqmValue = avgMonthlyPerM2 / 1000.0;
        String MonthlyDisplayPerSqm = df.format(MonthlyDisplayPerSqmValue);
        double DepositDisplayPerSqmValue = avgDepositPerM2 / 1000.0;
        String DepositDisplayPerSqm = df.format(DepositDisplayPerSqmValue);


        // 데이터 정리해서 보내기
        Map<String, Object> responseData = new HashMap<>();
        responseData.put("ok", true);
        responseData.put("seniorityTotalFormatted", seniorityTotalFormatted); // 예상 선순위보증금
        responseData.put("rentRisk", rentRisk);       // 월세 시세괴리 단계
        responseData.put("depositRisk", depositRisk); // 보증금 시세괴리 단계
        responseData.put("bondDepositRisk", bondDepositRisk); // 채권보증금 리스크
        responseData.put("debtRiskLevel", debtRiskLevel); // 근저당권 기반 위험
        responseData.put("collateralValue", collateralValue);
        responseData.put("avgMonthlyDisplay", avgMonthlyDisplay);
        responseData.put("avgDepositDisplay", avgDepositDisplay);
        responseData.put("MonthlyDisplayPerSqm", MonthlyDisplayPerSqm);
        responseData.put("DepositDisplayPerSqm", DepositDisplayPerSqm);
        responseData.put("weightedValue", weightedValue);


        return ResponseEntity.ok(responseData);
    }

    // 리스크 등급 계산
    public static String getRiskLevel(double gapRatio) {
        double absGap = Math.abs(gapRatio);
        if (absGap <= 0.2) return "정상";      // ±20% 이내
        else if (absGap <= 0.4) return "주의"; // ±40% 이내
        else if (absGap <= 0.6) return "위험"; // ±60% 이내
        else return "고위험";
    }

    private boolean isPdfByHeader(MultipartFile f) {
        String ct = Optional.ofNullable(f.getContentType()).orElse("");
        return ct.equalsIgnoreCase(MediaType.APPLICATION_PDF_VALUE)
                || Optional.ofNullable(f.getOriginalFilename()).orElse("")
                .toLowerCase().endsWith(".pdf");
    }

    private boolean looksLikePdf(MultipartFile f) {
        try (var is = f.getInputStream()) {
            byte[] buf = is.readNBytes(1024);
            for (int i = 0; i <= buf.length - 4; i++) {
                if (buf[i] == '%' && buf[i + 1] == 'P' && buf[i + 2] == 'D' && buf[i + 3] == 'F') return true;
            }
        } catch (Exception ignored) {
        }
        return false;
    }

    @GetMapping("/test")
    @ResponseBody
    public String test() throws Exception {
        propertyService.fetchBldRgstItems("서울특별시 서초구 서초동 1317-17");
        return "성공";
    }


}
