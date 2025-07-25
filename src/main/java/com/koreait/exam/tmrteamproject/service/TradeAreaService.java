package com.koreait.exam.tmrteamproject.service;

import com.koreait.exam.tmrteamproject.repository.PdfFileRepository;
import com.koreait.exam.tmrteamproject.repository.TradeAreaRepository;
import com.koreait.exam.tmrteamproject.vo.PdfFile;
import com.koreait.exam.tmrteamproject.vo.TradeArea;
import lombok.RequiredArgsConstructor;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.rendering.PDFRenderer;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Service;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TradeAreaService {

    private final PdfFileRepository pdfFileRepository;
    private final TradeAreaRepository tradeAreaRepository;

    public String getPdfTextFromDb(String fileName) {
        Optional<PdfFile> optionalPdf = pdfFileRepository.findByFileName(fileName);
        if (optionalPdf.isEmpty()) return "";

        try (PDDocument document = Loader.loadPDF(optionalPdf.get().getFileData())) {
            PDFTextStripper stripper = new PDFTextStripper();
            return stripper.getText(document);
        } catch (Exception e) {
            e.printStackTrace();
            return "";
        }
    }

    public void parseRecentTradeAreas() {
        List<PdfFile> recentPdfs = pdfFileRepository.findTop10ByOrderByIdDesc();

        for (PdfFile pdf : recentPdfs) {
            try (PDDocument document = Loader.loadPDF(pdf.getFileData())) {
                PDFTextStripper stripper = new PDFTextStripper();
                String text = stripper.getText(document);
                parseAndSaveTradeArea(text, pdf.getFileName());
            } catch (Exception e) {
                System.err.println("PDF 파싱 실패: " + pdf.getFileName());
                e.printStackTrace();
            }
        }
    }

    public TradeArea parseAndSaveTradeArea(String pdfText, String fileName) {
        // 데이터 부족 안내 문구가 포함된 경우 저장하지 않음
        if (pdfText.contains("선택하신 행정동에는 해당 업종의 업소 수가 3개 이하이거나")) {
            System.out.println("데이터 부족으로 저장 제외: " + fileName);
            return null;
        }

        // 정규식 기반 데이터 추출
        int storeCount = extractInt(pdfText, "업소수는.*?(\\d+)개");
        int footTraffic = extractInt(pdfText, "유동인구.*?(\\d{1,3}(,\\d{3})*)명");
        int deliveryOrders = extractInt(pdfText, "배달주문건수는.*?(\\d+)건");
        int monthlySales = extractInt(pdfText, "월평균 매출액은.*?(\\d{1,3}(,\\d{3})*)만원");

        // 증감률은 %, - 포함
        double storeYoy = extractBlockChangeWithDecreaseCheck(pdfText, "업소수", "전년동월대비");
        double storeMom = extractBlockChangeWithDecreaseCheck(pdfText, "업소수", "전월대비");
        double deliveryYoy = extractBlockChangeWithDecreaseCheck(pdfText, "배달주문건수", "전년동월대비");
        double deliveryMom = extractBlockChangeWithDecreaseCheck(pdfText, "배달주문건수", "전월대비");
        double salesYoy = extractBlockChangeWithDecreaseCheck(pdfText, "매출액", "전년동월대비");
        double salesMom = extractBlockChangeWithDecreaseCheck(pdfText, "매출액", "전월대비");

        // 피크 요일 및 시간대
        String peakDay = extractString(pdfText, "요일은\\s*(\\S+),");
        String peakTime = extractString(pdfText, "시간대는\\s*(\\S+)입니다");

        // 파일명 기반 지역명, 업종 추출
        String regionName = extractRegionName(fileName);
        String industry = extractIndustry(fileName);

        // 엔티티 생성 및 저장
        TradeArea tradeArea = TradeArea.builder()
                .regionName(regionName)
                .industry(industry)
                .storeCount(storeCount)
                .storeCountYoyChange(storeYoy)
                .storeCountMomChange(storeMom)
                .delivery_orders(deliveryOrders)
                .delivery_orders_yoy(deliveryYoy)
                .delivery_orders_mom(deliveryMom)
                .footTraffic(footTraffic)
                .monthlySales(monthlySales)
                .salesYoyChange(salesYoy)
                .salesMomChange(salesMom)
                .peakDay(peakDay)
                .peakTime(peakTime)
                .build();

        return tradeAreaRepository.save(tradeArea);
    }

    public List<String> extractImagesFromDbPdf(String fileName) {
        List<String> images = new ArrayList<>();
        Optional<PdfFile> optionalPdf = pdfFileRepository.findByFileName(fileName);
        if (optionalPdf.isEmpty()) return images;

        try (PDDocument document = Loader.loadPDF(optionalPdf.get().getFileData())) {
            PDFRenderer renderer = new PDFRenderer(document);
            for (int i = 0; i < document.getNumberOfPages(); i++) {
                BufferedImage image = renderer.renderImageWithDPI(i, 200);
                ByteArrayOutputStream baos = new ByteArrayOutputStream();
                ImageIO.write(image, "png", baos);
                String base64 = Base64.getEncoder().encodeToString(baos.toByteArray());
                images.add("data:image/png;base64," + base64);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return images;
    }

    private int extractInt(String text, String pattern) {
        Pattern p = Pattern.compile(pattern);
        Matcher m = p.matcher(text);
        if (m.find()) {
            String numStr = m.group(1).replace(",", "");
            return Integer.parseInt(numStr);
        }
        return 0;
    }

    private String extractString(String text, String pattern) {
        Pattern p = Pattern.compile(pattern);
        Matcher m = p.matcher(text);
        if (m.find()) {
            return m.group(1);
        }
        return "";
    }

    private String extractRegionName(String fileName) {
        String[] parts = fileName.replace(".pdf", "").split(" ");
        return parts.length >= 4 ? String.join(" ", Arrays.copyOfRange(parts, 0, parts.length - 1)) : "알수없음";
    }

    private String extractIndustry(String fileName) {
        String[] parts = fileName.replace(".pdf", "").split(" ");
        return parts[parts.length - 1];
    }

    public List<String> getRecentFileName() {
        return pdfFileRepository.findTop10ByOrderByIdDesc()
                .stream()
                .map(PdfFile::getFileName)
                .collect(Collectors.toList());
    }

    //각각 전년동월대비 / 전월대비 분리
    private double extractBlockChangeWithDecreaseCheck(String text, String blockKeyword, String targetKeyword) {
        Pattern blockPattern = Pattern.compile(blockKeyword + ".*?(전년동월대비[\\s\\S]{0,50}|전월대비[\\s\\S]{0,50})", Pattern.DOTALL);
        Matcher blockMatcher = blockPattern.matcher(text);

        if (blockMatcher.find()) {
            String block = blockMatcher.group(0);
            Pattern valuePattern = Pattern.compile(targetKeyword + "\\s*([\\d.]+)%\\s*(많고|낮고|증가|감소)?");
            Matcher valueMatcher = valuePattern.matcher(block);
            if (valueMatcher.find()) {
                double value = Double.parseDouble(valueMatcher.group(1));
                String direction = valueMatcher.group(2);

                if ("낮고".equals(direction) || "감소".equals(direction)) {
                    return -value;
                }

                return value;
            }
        }
        return 0.0;
    }
}
