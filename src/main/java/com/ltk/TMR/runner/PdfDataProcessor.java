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
@Order(2)
@RequiredArgsConstructor
public class PdfDataProcessor implements ApplicationRunner {

    private final LhApplyInfoRepository lhRepository;
    private final PdfProcessingService pdfService;

    @Override
    @Transactional
    public void run(ApplicationArguments args) {
        log.info("[Runner] PDF 전체 내용 Markdown 변환 작업을 시작합니다.");

        List<LhApplyInfo> lhList = lhRepository.findAll();

        for (LhApplyInfo item : lhList) {
            if (item.getAttachments() == null || item.getAttachments().isEmpty()) {
                continue;
            }
            // 기존 텍스트 확인 로직 제거 >> 매번 새로 추출

            item.getAttachments().stream()
                    .filter(a -> a.getName().toLowerCase().endsWith(".pdf"))
                    .findFirst()
                    .ifPresent(attachment -> {
                        // PDF 전체를 마크다운으로 변환
                        String markdownContent = pdfService.extractAllTextAsMarkdown(attachment.getUrl());
                        item.setMarkdownText(markdownContent);

                        if(markdownContent != null && !markdownContent.startsWith("오류")) {
                            log.info("  > PDF -> Markdown 변환 성공 (siteNo: {})", item.getSiteNo());
                        } else {
                            log.warn("  > PDF -> Markdown 변환 실패 (siteNo: {})", item.getSiteNo());
                        }
                    });
        }
        log.info("[Runner] PDF 전체 내용 Markdown 변환 작업을 완료했습니다.");
    }
}