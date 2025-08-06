package com.koreait.exam.tmrteamproject.service;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.IOUtils;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Service;
import technology.tabula.ObjectExtractor;
import technology.tabula.Page;
import technology.tabula.Table;
import technology.tabula.extractors.SpreadsheetExtractionAlgorithm;

import java.io.InputStream;
import java.net.URL;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class PdfProcessingService {

    public String extractAllTextAsMarkdown(String fileUrl) {
        log.info("  > Extracting entire PDF as Markdown from URL: {}", fileUrl);
        try (InputStream is = new URL(fileUrl).openStream()) {

            byte[] pdfBytes = IOUtils.toByteArray(is);

            PDDocument document = Loader.loadPDF(pdfBytes);

            PDFTextStripper stripper = new PDFTextStripper();
            StringBuilder fullMarkdown = new StringBuilder();

            for (int i = 1; i <= document.getNumberOfPages(); i++) {
                fullMarkdown.append("\n\n--- Page ").append(i).append(" ---\n\n");

                stripper.setStartPage(i);
                stripper.setEndPage(i);
                String pageText = stripper.getText(document);

                ObjectExtractor extractor = new ObjectExtractor(document);
                Page page = extractor.extract(i);
                SpreadsheetExtractionAlgorithm sea = new SpreadsheetExtractionAlgorithm();
                List<Table> tables = sea.extract(page);

                if (tables.isEmpty()) {
                    fullMarkdown.append(pageText);
                } else {
                    for (Table table : tables) {
                        fullMarkdown.append(convertTableToMarkdown(table)).append("\n");
                    }
                }
            }
            document.close();
            return fullMarkdown.toString();

        } catch (Exception e) {
            log.error("  > Failed to extract PDF as Markdown [{}]: {}", fileUrl, e.getMessage());
            return "오류: PDF를 마크다운으로 변환하는 데 실패했습니다. 원인: " + e.getMessage();
        }
    }

    private String convertTableToMarkdown(Table table) {
        StringBuilder sb = new StringBuilder();
        List<List<technology.tabula.RectangularTextContainer>> rows = table.getRows();

        if (rows.isEmpty()) {
            return "";
        }

        // 헤더 생성 (첫 번째 행 기준)
        sb.append("| ");
        sb.append(rows.get(0).stream().map(c -> c.getText().replaceAll("\r|\n", " ").trim()).collect(Collectors.joining(" | ")));
        sb.append(" |\n");

        // 구분선 생성
        sb.append("| ");
        sb.append(rows.get(0).stream().map(c -> "---").collect(Collectors.joining(" | ")));
        sb.append(" |\n");

        // 데이터 행 생성 (두 번째 행부터)
        for (int i = 1; i < rows.size(); i++) {
            String rowString = rows.get(i).stream()
                    .map(c -> c.getText().replaceAll("\r|\n", " ").trim())
                    .collect(Collectors.joining(" | "));
            sb.append("| ").append(rowString).append(" |\n");
        }
        return sb.toString();
    }
}