package com.ltk.TMR.service;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
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
import java.util.Iterator;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class PdfProcessingService {

    public String extractAllTextAsMarkdown(String fileUrl) {
        log.info("  > Extracting entire PDF as Markdown from URL: {}", fileUrl);
        try (InputStream is = new URL(fileUrl).openStream();
             PDDocument document = Loader.loadPDF(is.readAllBytes())) {

            PDFTextStripper stripper = new PDFTextStripper();
            StringBuilder fullMarkdown = new StringBuilder();

            for (int i = 1; i <= document.getNumberOfPages(); i++) {
                fullMarkdown.append("\n\n--- Page ").append(i).append(" ---\n\n");

                // 페이지 전체 텍스트 추출
                stripper.setStartPage(i);
                stripper.setEndPage(i);
                String pageText = stripper.getText(document);

                // 테이블 추출(tabula 사용)
                ObjectExtractor extractor = new ObjectExtractor(document);
                Page page = extractor.extract(i);
                List<Table> tables = new SpreadsheetExtractionAlgorithm().extract(page);

                if (tables.isEmpty()) {
                    // 테이블이 없으면 텍스트만 추가
                    fullMarkdown.append(pageText);
                } else {
                    // 테이블이 있으면 마크다운으로 변환하여 추가
                    for (Table table : tables) {
                        fullMarkdown.append(convertTableToMarkdown(table)).append("\n");
                    }
                }
            }
            return fullMarkdown.toString();

        } catch (Exception e) {
            log.error("  > Failed to extract PDF as Markdown [{}]: {}", fileUrl, e.getMessage());
            return "오류: PDF를 마크다운으로 변환하는 데 실패했습니다. 원인: " + e.getMessage();
        }
    }

    private String convertTableToMarkdown(Table table) {
        StringBuilder sb = new StringBuilder();
        // 헤더 구분선
        if (!table.getRows().isEmpty()) {
            sb.append("| ");
            sb.append(table.getRows().get(0).stream().map(c -> "---").collect(Collectors.joining(" | ")));
            sb.append(" |\n");
        }
        // 각 행을 "|"로 연결하여 마크다운으로 변환
        for (List<technology.tabula.RectangularTextContainer> row : table.getRows()) {
            String rowString = row.stream()
                    .map(c -> c.getText().replaceAll("\r|\n", " ").trim())
                    .collect(Collectors.joining(" | "));
            sb.append("| ").append(rowString).append(" |\n");
        }
        return sb.toString();
    }
}