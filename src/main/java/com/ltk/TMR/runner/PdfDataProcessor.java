package com.ltk.TMR.runner;

import com.ltk.TMR.entity.LhApplyInfo;
import com.ltk.TMR.repository.LhApplyInfoRepository;
import com.ltk.TMR.service.PdfProcessingService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Slf4j
@Component
@Order(2) // LHCrawlerRunner가 실행된 후에 실행되도록 순서 지정
@RequiredArgsConstructor
public class PdfDataProcessor implements ApplicationRunner {

    private final LhApplyInfoRepository lhRepository;
    private final PdfProcessingService pdfService;

    @Override
    @Transactional
    public void run(ApplicationArguments args) {
        log.info("[Runner] PDF 데이터 추출 및 DB 업데이트 작업을 시작합니다.");

        List<LhApplyInfo> lhList = lhRepository.findAll();

        for (LhApplyInfo item : lhList) {
            // 텍스트가 추출된 공고는 스킵
            if (item.getExtractedText() != null && !item.getExtractedText().isEmpty()) {
                continue;
            }

            if (item.getAttachments() == null || item.getAttachments().isEmpty()) {
                continue;
            }

            StringBuilder allPdfText = new StringBuilder();

            // 모든 첨부파일 순회
            for (LhApplyInfo.AttachmentDto attachment : item.getAttachments()) {
                if (attachment.getName().toLowerCase().contains(".pdf")) {
                    // PDF 서비스 호출하여 데이터 추출
                    PdfProcessingService.ExtractedData extracted = pdfService.extractDataFromUrl(attachment.getUrl());
                    allPdfText.append("--- File: ").append(attachment.getName()).append(" ---\n\n");
                    allPdfText.append(extracted.getText()).append("\n\n");
                }
            }

            // 추출된 전체 텍스트를 엔티티에 저장
            if (!allPdfText.isEmpty()) {
                log.info("  > Updating extracted text for siteNo: {}", item.getSiteNo());
                item.setExtractedText(allPdfText.toString());
                // @Transactional에 의해 종료 시 변경된 내용 자동으로 DB에 반영
            }
        }
        log.info("[Runner] PDF 데이터 추출 및 DB 업데이트 작업 완료.");
    }
}