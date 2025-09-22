package com.koreait.exam.tmrteamproject.controller;

import com.koreait.exam.tmrteamproject.service.AddressService;
import com.koreait.exam.tmrteamproject.service.JobStatusService;
import com.koreait.exam.tmrteamproject.service.PropertyService;
import com.koreait.exam.tmrteamproject.vo.AddressPickReq;
import com.koreait.exam.tmrteamproject.vo.NormalizedAddress;
import com.koreait.exam.tmrteamproject.vo.ResultData;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.text.DecimalFormat;
import java.text.NumberFormat;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.function.Function;

@Controller
@RequestMapping("/usr/property")
@Slf4j
@RequiredArgsConstructor
public class PropertyController {

    private final PropertyService propertyService;
    private final AddressService addressService;
    private final JobStatusService jobStatusService;

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
            @RequestParam("deposit") int beforeDeposit,
            @RequestParam("monthlyRent") int beforeMonthlyRent,
            @RequestParam(required = false) Double lat,
            @RequestParam(required = false) Double lng
    ) throws Exception {
        // 로딩바 나타낼 상태 객체 생성
        String jobId = UUID.randomUUID().toString();
        jobStatusService.setStatus(jobId, "init");

        // 0) (만원)으로 들어온 데이터 10,000 곱해주기

        final int deposit = beforeDeposit * 10000;
        final int monthlyRent = beforeMonthlyRent * 10000;

        CompletableFuture.runAsync(() -> {
            try {
                jobStatusService.setStatus(jobId, "pdf");

                // 1) 들어온 파일 모으기 (file 또는 files)
                List<MultipartFile> all = new ArrayList<>();
                if (file != null && !file.isEmpty()) all.add(file);
                if (files != null) {
                    for (MultipartFile f : files) if (f != null && !f.isEmpty()) all.add(f);
                }
                if (all.isEmpty()) {
                    jobStatusService.setStatus(jobId, "error: 파일 없음");
                    return; // 그냥 끝냄
                }

                // 2) PDF만 추리기 (MIME/확장자 + 매직바이트 스니핑)
                List<MultipartFile> pdfOnly = all.stream()
                        .filter(f -> isPdfByHeader(f) || looksLikePdf(f))
                        .toList();

                if (pdfOnly.isEmpty()) {
                    jobStatusService.setStatus(jobId, "error: PDF 아님");
                    return;
                }

                // 3) PDF가 2개 이상이면 경고하고 중단
                if (pdfOnly.size() > 1) {
                    List<String> names = pdfOnly.stream()
                            .map(f -> Optional.ofNullable(f.getOriginalFilename()).orElse("noname"))
                            .toList();
                    jobStatusService.setStatus(jobId, "error: PDF 여러 개");
                    return;
                }

                // 4) 좌표 메타(옵션)
                Map<String, String> extra = new HashMap<>();
                if (lat != null) extra.put("lat", String.valueOf(lat));
                if (lng != null) extra.put("lng", String.valueOf(lng));

                // 5) 파이썬에 파일 보내고 분석 결과 받기
                MultipartFile thePdf = pdfOnly.get(0);
                Map<String, Object> result = propertyService.analyzeWithPythonDirect(List.of(thePdf), extra);

                jobStatusService.setStatus(jobId, "crawl");
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

                jobStatusService.setStatus(jobId, "area");
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

                jobStatusService.setStatus(jobId, "rent");
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

                jobStatusService.setStatus(jobId, "calc");
                // 12) 예상 선순위보증금 계산
                // 지역 평균 월세 * 전유면적
                double seniorityTotal = avgMonthlyPerM2 * currentArea * 100;

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

                jobStatusService.setStatus(jobId, "collateralValue");
                // 13) 담보가치 계산
                // 연 임대수익 / 임대수익률
                // 연 임대수익 : 월세 * 12 + 보증금 * 0.02(환산율)

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
                double landBasePrice = Double.parseDouble(body.get("land_base_price").toString());

                // 토지면적
                double landShareArea = (double) result.get("landShareArea");

                // 토지 지분가치 (토지시가 * 토지면적)
                double landShareValue = landShareArea * landBasePrice;

                // 건물 지분 가치 (건물시가 * 전유면적)
                double buildingValue = currentArea * buildBasePrice;

                // 담보가치(정적)
                double collateralValue = landShareValue + buildingValue;

                System.out.println("realItem : " + realItem);
                // 실거래가를 통해 가치 구하기
                double dealPrice = propertyService.fetchAndCalculate("11650", "서초동");

                // 실거래가 계산
                double collateralValueByDealPrice = dealPrice * currentArea;

                // 만원 단위로 계산
                String formatCollateralValueTotal = formatToEokCheon(collateralValue);
                String formatCollateralValueByDealPrice = formatToEokCheon(collateralValueByDealPrice);

                System.out.println("formatCollateralValueTotal : " + formatCollateralValueTotal);
                System.out.println("formatCollateralValueByDealPrice : " + formatCollateralValueByDealPrice);


                // 14) 채권보증금 리스크 계산
                // 채권 최고액 + 예상 선순위보증금 금액 / 담보가치
                // 채권보증금 리스크 (정적 담보가치)
                double riskRatioStatic = (weightedValue + seniorityTotalRounded) / collateralValue;

                // 채권보증금 리스크 (실거래가 담보가치)
                double riskRatioDeal = (weightedValue + seniorityTotalRounded) / collateralValueByDealPrice;

                System.out.println("weightedValue : " + weightedValue);
                System.out.println("seniorityTotalRounded : " + seniorityTotalRounded);
                System.out.println("collateralValue : " + collateralValue);
                System.out.println("riskRatioStatic  : " + riskRatioStatic);


                // 리스크 레벨 판정 함수 (중복 방지용)
                Function<Double, String> toRiskLevel = ratio -> {
                    if (ratio < 0.5) return "정상";
                    else if (ratio < 0.7) return "주의";
                    else if (ratio < 1.0) return "위험";
                    else return "고위험";
                };

                String bondDepositRiskStatic = toRiskLevel.apply(riskRatioStatic);
                String bondDepositRiskDeal = toRiskLevel.apply(riskRatioDeal);

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
                responseData.put("bondDepositRiskStatic", bondDepositRiskStatic); // 채권보증금 리스크
                responseData.put("bondDepositRiskDeal", bondDepositRiskDeal); // 채권보증금 리스크
                responseData.put("debtRiskLevel", debtRiskLevel); // 근저당권 기반 위험
                responseData.put("collateralValue", collateralValue);
                responseData.put("avgMonthlyDisplay", avgMonthlyDisplay);
                responseData.put("avgDepositDisplay", avgDepositDisplay);
                responseData.put("MonthlyDisplayPerSqm", MonthlyDisplayPerSqm);
                responseData.put("DepositDisplayPerSqm", DepositDisplayPerSqm);
                responseData.put("weightedValue", weightedValue);

                jobStatusService.setResult(jobId, responseData);
                jobStatusService.setStatus(jobId, "done");
            } catch (Exception e) {
                jobStatusService.setStatus(jobId, "error");
            }
        });

        return ResponseEntity.ok(Map.of("ok", true, "jobId", jobId));
    }

    @GetMapping("/status/{jobId}")
    public ResponseEntity<?> getStatus(@PathVariable String jobId) {
        String status = jobStatusService.getStatus(jobId);
        // area
        //
        int percent = switch (status) {
            case "init" -> 0;
            case "pdf" -> 20;
            case "crawl" -> 40;
            case "area" -> 60;
            case "rent" -> 70;
            case "calc" -> 80;
            case "collateralValue" -> 90;
            case "done", "error" -> 100;
            default -> 0;
        };
        return ResponseEntity.ok(Map.of("status", status, "percent", percent));
    }

    @GetMapping("/result/{jobId}")
    public ResponseEntity<?> getResult(@PathVariable String jobId) {
        Map<String, Object> result = jobStatusService.getResult(jobId);
        if (result == null) {
            return ResponseEntity.status(404).body(Map.of("ok", false, "message", "아직 처리 중입니다."));
        }
        return ResponseEntity.ok(result);
    }


    private String formatToEokCheon(double value) {
        long won = Math.round(value);  // 원 단위 반올림

        long eok = won / 100_000_000;              // 억
        long cheon = Math.round((won % 100_000_000) / 10_000_000.0); // 천만 단위 반올림

        // 천만이 10이 되면 올림 처리
        if (cheon == 10) {
            eok += 1;
            cheon = 0;
        }

        if (cheon == 0) {
            return String.format("%d억", eok);
        } else {
            return String.format("%d억 %d천만", eok, cheon);
        }
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
}
