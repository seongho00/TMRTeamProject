package com.koreait.exam.tmrteamproject.controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.koreait.exam.tmrteamproject.service.AddressService;
import com.koreait.exam.tmrteamproject.service.KakaoOAuthService;
import com.koreait.exam.tmrteamproject.service.PropertyService;
import com.koreait.exam.tmrteamproject.vo.AddressPickReq;
import com.koreait.exam.tmrteamproject.vo.NormalizedAddress;
import com.koreait.exam.tmrteamproject.vo.PropertyFile;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import okhttp3.Address;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
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
            @RequestParam(required = false) Double lat,
            @RequestParam(required = false) Double lng
    ) throws JsonProcessingException {
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

        // 6) 분석된 주소에서 normal인 것만 빼오기
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

        // 7) 분석된 주소마다 면적 구해오기
        List<Map<String, Object>> normals = (List<Map<String, Object>>) filteredResult.get("normalAddresses");

        if (normals == null || normals.isEmpty()) {
            System.out.println("✅ normal 주소 없음");
        }

        double sum = 0.0;
        for (Map<String, Object> addr : normals) {
            String address = (String) addr.get("address");

            double area = propertyService.resolveAreaFromLine(address);

            sum += area;
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
        String normalizedAddr = propertyService.simplifyToLegalLot(cleaned);

        // AddressService로 검색
        List<NormalizedAddress> list = addressService.search(normalizedAddr, 1, 5);
        System.out.println(list);

        Map<String, Object> response = new HashMap<>();
        if (!list.isEmpty()) {
            NormalizedAddress n = list.get(0);

            // AddressPickReq 생성
            AddressPickReq req = new AddressPickReq();
            req.setSelected(n);

            // ✅ 최종: confirm + geocode + crawl 한번에 실행
            response = addressService.confirmGeoAndCrawl(req);

        }

        double avgMonthlyPerM2 = addressService.calculateAverageMonthly(response);
        double avgDepositPerM2 = addressService.calculateAverageDeposit(response);
        // 12) 예상 선순위보증금 계산
        // 선임차 환산보증금 + 채권금액
        // 선임차 환산보증금 : 지역 평균 월세 * 전유면적
        double seniorityTotal = avgMonthlyPerM2 * currentArea * 100 + weightedValue;

        long rounded = Math.round(seniorityTotal);

        // 한국 원화 기준 포맷
        NumberFormat formatter = NumberFormat.getCurrencyInstance(Locale.KOREA);
        String formatted = formatter.format(rounded);

        System.out.println(formatted); // → ₩17,857,978


        // 시세 괴리 리스크
        int dailyRate = 123; // 사용자 입력값
        int deposit = 123; // 사용자 입력값
        double unit_rent = dailyRate / currentArea;
        double unit_deposit = deposit / currentArea;


        // 괴리율 계산
        double rentGapRatio = (unit_rent - avgMonthlyPerM2) / avgMonthlyPerM2;
        double depositGapRatio = (unit_deposit - avgDepositPerM2) / avgDepositPerM2;

        // 4. 리스크 레벨
        String rentRisk = getRiskLevel(rentGapRatio);
        String depositRisk = getRiskLevel(depositGapRatio);

        System.out.println("rentRist : " + rentRisk);
        System.out.println("depositRisk : " + depositRisk);

        return ResponseEntity.ok(result);
    }

    // 리스크 등급 계산
    public static String getRiskLevel(double gapRatio) {
        double absGap = Math.abs(gapRatio);
        if (absGap <= 0.1) return "정상";      // ±10% 이내
        else if (absGap <= 0.2) return "주의"; // ±20% 이내
        else if (absGap <= 0.3) return "위험"; // ±30% 이내
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


    @GetMapping("/selectJuso")
    public String selectJuso(Model model) {

        return "property/selectJuso";
    }

    @GetMapping("/test")
    @ResponseBody
    public String test(Model model) throws JsonProcessingException {
        kakaoOAuthService.searchActualUsage(127.447033947, 36.316349615);

        return "";
    }

}

