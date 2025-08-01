package com.ltk.TMR.runner;

import com.ltk.TMR.entity.LhApplyInfo;
import com.ltk.TMR.entity.LhProcessingStatus;
import com.ltk.TMR.entity.MarkdownStatus;
import com.ltk.TMR.repository.LhApplyInfoRepository;
import com.ltk.TMR.service.LlmProcessingService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.util.List;

@Slf4j
@Component
@Order(3) // PdfDataProcessor 다음에 실행
@RequiredArgsConstructor
public class LlmRunner implements ApplicationRunner {

    private final LhApplyInfoRepository lhRepository;
    private final LlmProcessingService llmService;

    @Override
    public void run(ApplicationArguments args) throws Exception {
        log.info("[Runner] LLM 처리 대기 목록 확인 및 비동기 작업 요청을 시작합니다.");

        List<LhApplyInfo> pendingList = lhRepository.findByMarkdownStatusAndProcessingStatus(
                MarkdownStatus.COMPLETED,
                LhProcessingStatus.PENDING
        );

        for (LhApplyInfo item : pendingList) {
            if (item.getMarkdownText() != null && !item.getMarkdownText().isBlank()) {
                llmService.processAndSaveDetails(item);
            }
        }
        log.info("[Runner] 총 {}건의 LLM 처리 요청을 완료했습니다.", pendingList.size());
    }
}