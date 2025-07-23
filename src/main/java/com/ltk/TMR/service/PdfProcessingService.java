package com.ltk.TMR.service;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.net.URL;

@Slf4j
@Service
@RequiredArgsConstructor
public class PdfProcessingService {

    public ExtractedData extractDataFromUrl(String fileUrl) {
        log.info("  > Processing PDF from URL: {}", fileUrl);

        try (InputStream is = new URL(fileUrl).openStream()) {
            // InputStream을 byte 배열로 먼저 리딩
            byte[] pdfBytes = is.readAllBytes();

            // byte 배열을 사용하여 PDF 문서 로드
            try (PDDocument document = Loader.loadPDF(pdfBytes)) {

                // 전체 텍스트 추출
                PDFTextStripper stripper = new PDFTextStripper();
                String text = stripper.getText(document);
                return new ExtractedData(text);
            }

        } catch (Exception e) {
            // 예외 발생 시 로그를 출력, 에러 메시지와 객체 반환
            log.error("  > Failed to process PDF [{}]: {}", fileUrl, e.getMessage());
            return new ExtractedData("오류: PDF 텍스트를 추출할 수 없습니다.");
        }
    }

    /**
     * 데이터 저장용 내부 DTO
     */
    @Getter
    @RequiredArgsConstructor
    public static class ExtractedData {
        private final String text;
    }
}